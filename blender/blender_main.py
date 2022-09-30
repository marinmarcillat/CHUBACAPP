import ast
import json
import os
import subprocess
from math import dist

import itertools
import numpy as np
import pandas as pd
from PyQt5 import QtCore
from fiona.crs import from_epsg
import fiona
import cv2

from shapely.geometry import Point, Polygon, LineString, mapping

import blender.camera_config as cc
import utils.coord_conversions as coord_tools
import utils.sfm as sfm_tools


class annotationsTo3DThread(QtCore.QThread):
    '''
    Thread class for Chubacapp GUI
    '''
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, annotation_path, sfm_data_path, model_path, exp, label):
        super(annotationsTo3DThread, self).__init__()
        self.running = True
        self.annotation_path = annotation_path
        self.sfm_data_path = sfm_data_path
        self.model_path = model_path
        self.exp = exp
        self.label = label

    def run(self):
        '''This starts the thread on the start() call'''
        annotationsTo3D(self.annotation_path, self.sfm_data_path, self.model_path, self.exp, self.label, self)


def annotationsTo3D(annotation_path, sfm_data_path, model_path, exp, label, thread=None):
    """
    Reprojects annotations from biigle on a 3D .ply model
    Inputs:
    - annotation_path: annotation csv file path from Biigle
    - sfm_data_path: temp_sfm_data.json or sfm_data.bin or .json path from the 3D model.
        if not temp_sfm_data.json, one will be generated (.bin -> .json -> temp_sfm_data.json)
        temp_sfm_data is a filtered version with only the useful cameras in it
    - model_path: .ply 3D model path
    - exp: '3Dmetrics' or 'shp', export format (shp lose z info)
    - label: if True, not annotations but image labels
    - Thread: For ChubacApp only, do not use
    Outputs:
    outputs will be stored in the annotation directory
    """

    # Imports here because of thread safe issues with the photogrametric module
    import bpy
    from mathutils import Vector, Euler

    from photogrammetry_importer.blender_utility.object_utility import add_collection
    from photogrammetry_importer.file_handlers.openmvg_json_file_handler import (
        OpenMVGJSONFileHandler,
    )
    from photogrammetry_importer.importers.camera_utility import add_camera_object
    from photogrammetry_importer.types.camera import Camera

    min_radius = 0.01  # Minnimum radius of a circle annotation if error
    camera_model = 'otus2' # camera model, see camera_config

    output_path = os.path.dirname(annotation_path)

    output_point_path = os.path.join(output_path, 'point_output.json')
    output_poly_path = os.path.join(output_path, 'poly_output.json')

    annotations = pd.read_csv(annotation_path, sep=",", )
    list_img = list(annotations['filename'])

    # Conversion from sfm_data.bin to sfm_data.json if not created. Long
    sfm_data, temp_sfm_path = sfm_tools.sfm_data_handler(sfm_data_path, list_img)

    intrinsics = sfm_data['intrinsics'][0]['value']['ptr_wrapper']['data']
    resolution = [intrinsics['height'], intrinsics['width']]
    focal = [intrinsics['focal_length'], intrinsics['focal_length']]
    principal_point = intrinsics['principal_point']
    distortion = intrinsics['disto_k3']

    optical_camera_matrix = cc.config_camera[camera_model]["optical_camera_matrix"]
    # -> Distortion coefficients
    dist_coeff = cc.config_camera[camera_model]["dist_coeff"]
    # -> Original resolution (width, height)
    (w, h) = cc.config_camera[camera_model]["resolution"]

    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(optical_camera_matrix, dist_coeff, (w, h), 1, (w, h))
    # create undistortion maps
    mapx, mapy = cv2.initUndistortRectifyMap(optical_camera_matrix, dist_coeff, None, newcameramtx, (w, h), 5)

    min_x = roi[0]
    max_x = roi[0] + roi[2]
    min_y = roi[1]
    max_y = roi[1] + roi[3]

    scale_x_sfm = intrinsics['width'] / w
    scale_y_sfm = intrinsics['height'] / h

    x_original_center = w / 2
    y_original_center = h / 2

    x_sfm_center = intrinsics['width'] / 2
    y_sfm_center = intrinsics['height'] / 2

    # initialize blender
    scene = bpy.data.scenes["Scene"]
    objects = bpy.data.objects

    print("Creating camera...")
    cameras, points = OpenMVGJSONFileHandler.parse_openmvg_file(
        temp_sfm_path,
        "",
        Camera.IMAGE_FP_TYPE_NAME,
        False,
    )
    print("Done !")

    # get all cameras from sfm_data.json
    camera_collection = add_collection("Camera Collection")
    cam_list = []
    for cam in cameras:
        cam_name = cam.get_file_name()
        cam_list.append(cam_name)
        camera_object = add_camera_object(cam, cam_name, camera_collection)

    # objects to consider
    print("opening model")
    if thread is not None:
        thread.prog_val.emit(10)
    bpy.ops.import_mesh.ply(filepath=model_path)
    model_name = os.path.splitext(os.path.basename(model_path))[0]
    bpy.data.objects[model_name].rotation_euler = (0, 0, 0)
    target = bpy.data.objects[model_name]
    print("Done !")

    def get_hit_points(image):
        # get all hit point between rays and target

        # camera object which defines ray source
        # create the first camera object
        cam = bpy.data.objects[image]
        scene.collection.objects.link(cam)

        scene.render.pixel_aspect_x = 1.0
        scene.render.pixel_aspect_y = 1.0
        scene.render.resolution_x = resolution[1]
        scene.render.resolution_y = resolution[0]

        # get vectors which define view frustum of camera
        frame = cam.data.view_frame(scene=scene)
        topRight = frame[0]
        bottomLeft = frame[2]
        topLeft = frame[3]

        # setup vectors to match pixels
        xRange = np.linspace(topLeft[0], topRight[0], resolution[1])
        yRange = np.linspace(topLeft[1], bottomLeft[1], resolution[0])

        # array to store hit information
        values = np.empty((xRange.size, yRange.size), dtype=object)

        # indices for array mapping
        indexX = 0
        indexY = 0

        # filling array with None
        for x in xRange:
            for y in yRange:
                values[indexX, indexY] = None
                indexY += 1
            indexX += 1
            indexY = 0

        # calculate origin
        matrixWorld = target.matrix_world
        origin = cam.matrix_world.translation
        # reset indices
        indexX = 0
        indexY = 0

        # iterate over all X/Y coordinates
        for x in xRange:
            for y in yRange:
                # get current pixel vector from camera center to pixel
                pixelVector = Vector((x, y, topLeft[2]))
                # rotate that vector according to camera rotation
                pixelVector.rotate(cam.matrix_world.to_quaternion())
                # calculate direction vector
                destination = (pixelVector + cam.matrix_world.translation)
                direction = (destination - origin).normalized()
                # perform the actual ray casting
                hit, location, norm, face = target.ray_cast(origin=origin, direction=direction)
                if hit:
                    values[indexX, indexY] = (matrixWorld @ location)

                # update indices
                indexY += 1

            indexX += 1
            indexY = 0
        return values

    # List of points corresponding to the image bound
    edge1 = [(x, min_y+1) for x in range(min_x+1, max_x - 1)]
    edge2 = [(max_x - 1, y) for y in range(min_y+1, max_y - 1)]
    edge3 = [(x, max_y - 1) for x in range(max_x - 1, min_x+1, -1)]
    edge4 = [(min_x+1, y) for y in range(max_y - 1, min_y+1, -1)]
    points_bound = edge1 + edge2 + edge3 + edge4
    points_bound = list(itertools.chain(*points_bound))

    point = []
    polygon = []
    line = []
    prog = 0
    tot_len = len(annotations['filename'].unique())
    print("Start annotations analysis...")
    for image in annotations['filename'].unique():
        if thread is not None:
            thread.prog_val.emit(round((prog / tot_len) * 100))
        prog += 1
        s = str(round((prog / tot_len) * 100)) + " %, " + str(prog) + " / " + str(tot_len)
        print(s, end="\r")

        if image in cam_list:
            hit_points = get_hit_points(image)
            ann_img = annotations.loc[annotations['filename'] == image]

            if label:
                ann['shape_name'] = 'Rectangle'
                ann['points'] = str(points_bound)
                ann['annotation_id'] = 999
            else:
                image_bound = pd.DataFrame({
                    'filename': [image],
                    'shape_name': ['Rectangle'],
                    'points': [str(points_bound)],
                    'label_name': ['bound'],
                    'label_hierarchy': ['bound'],
                    'annotation_id': [999],
                })
                ann_img = pd.concat([ann_img, image_bound])  # Add an annotation corresponding to the image imprint

            for index, ann in ann_img.iterrows():  # for each annotation
                if ann['shape_name'] in ['Circle', 'Point']:  # if the annotation is a point or a circle
                    x, y = ast.literal_eval(ann['points'])[:2]

                    if min_x < x < max_x and min_y < y < max_y:

                        # get the location of the intersection between ray and target
                        coord = coord_tools.annotation2hitpoint((x, y), hit_points, mapx, mapy, x_original_center,
                                                          scale_x_sfm, x_sfm_center, y_original_center, scale_y_sfm,
                                                          y_sfm_center)

                        if coord is not None:  # If we have a hit point

                            if ann['shape_name'] == 'Circle':
                                # If the annotation is a circle, we try to get an approximate radius by looking
                                # North, South, East and West from the center. We then keep the minimal distance
                                # obtained
                                radius = []  # min arbitrary value
                                r = ast.literal_eval(ann['points'])[2]
                                list_coord_r = [(x + r, y), (x - r, y), (x, y + r), (x, y - r)]
                                for i in list_coord_r:
                                    if min_x < i[0] < max_x and min_y < i[1] < max_y:
                                        # get the location of the intersection between ray and target
                                        coord_radius = coord_tools.annotation2hitpoint((i[0], i[1]), hit_points, mapx, mapy,
                                                                                 x_original_center, scale_x_sfm,
                                                                                 x_sfm_center,
                                                                                 y_original_center, scale_y_sfm,
                                                                                 y_sfm_center)

                                        if coord_radius is not None:
                                            ct = [coord[0], coord[1]]
                                            off = [coord_radius[0], coord_radius[1]]
                                            radius.append(dist(ct, off))
                                if len(radius) != 0:
                                    # If no other point is found, set the radius to an arbitrary small value
                                    radius = min(radius)
                                else:
                                    radius = min_radius
                            else:
                                radius = 0

                            point.append([[coord[0], coord[1], coord[2]], ann['label_name'], ann['label_hierarchy'],
                                          ann['filename'],
                                          ann['annotation_id'], radius])


                elif ann['shape_name'] == 'LineString':  # if geometry is a line
                    list_coord = list(zip(*[iter(ast.literal_eval(ann['points']))] * 2))
                    points_out = []
                    for i in list_coord:
                        if min_x < i[0] < max_x and min_y < i[1] < max_y:
                            # get the location of the intersection between ray and target
                            coord = coord_tools.annotation2hitpoint((i[0], i[1]), hit_points, mapx, mapy,
                                                                     x_original_center, scale_x_sfm,
                                                                     x_sfm_center,
                                                                     y_original_center, scale_y_sfm,
                                                                     y_sfm_center)

                            if coord is not None:
                                points_out.append([coord[0], coord[1], coord[2]])
                    if len(points_out) != 0:
                        line.append(
                            [points_out, ann['label_name'], ann['label_hierarchy'], ann['filename'],
                             ann['annotation_id']])



                elif ann['shape_name'] in ['Polygon', 'Rectangle']:  # if geometry is a polygon or rectangle
                    list_coord = list(zip(*[iter(ast.literal_eval(ann['points']))] * 2))
                    points_out = []

                    for i in list_coord:  # For all the points of the polygone
                        if min_x < i[0] < max_x and min_y < i[1] < max_y:
                            # get the location of the intersection between ray and target
                            coord = coord_tools.annotation2hitpoint((i[0], i[1]), hit_points, mapx, mapy,
                                                                     x_original_center, scale_x_sfm,
                                                                     x_sfm_center,
                                                                     y_original_center, scale_y_sfm,
                                                                     y_sfm_center)

                            if coord is not None:
                                points_out.append([coord[0], coord[1], coord[2]])
                    if len(points_out) != 0:  # If more than one point exist
                        polygon.append(
                            [points_out, ann['label_name'], ann['label_hierarchy'], ann['filename'],
                             ann['annotation_id']])

    print("Exporting...")
    if exp == '3Dmetrics':
        # Export to 3Dmetrics Json measurement file
        export_point = {
            "Data": [],
            "Fields": [
                {
                    "Name": "LabelName",
                    "Type": "Text"
                },
                {
                    "Name": "LabelHierarchy",
                    "Type": "Text"
                },
                {
                    "Name": "Filename",
                    "Type": "Text"
                },
                {
                    "Name": "AnnotationId",
                    "Type": "Text"
                },
                {
                    "Name": "coord",
                    "Type": "Point"
                }
            ],
            "Measurement pattern": "3DMetrics",
            "Reference": {
                "altitude": 0,
                "latitude": 0,
                "longitude": 0,
            }
        }

        export_polygon = {
            "Data": [],
            "Fields": [
                {
                    "Name": "LabelName",
                    "Type": "Text"
                },
                {
                    "Name": "LabelHierarchy",
                    "Type": "Text"
                },
                {
                    "Name": "Filename",
                    "Type": "Text"
                },
                {
                    "Name": "AnnotationId",
                    "Type": "Text"
                },
                {
                    "Name": "Area",
                    "Type": "Area"
                }
            ],
            "Measurement pattern": "3DMetrics",
            "Reference": {
                "altitude": 0,
                "latitude": 0,
                "longitude": 0,
            }
        }

        for i in point:
            coord = i[0]
            pts = {
                "x": coord[0],
                "y": coord[1],
                "z": coord[2],
            }
            pts_ann = [{"LabelName": str(i[1])},
                       {"LabelHierarchy": str(i[2])},
                       {"Filename": str(i[3])},
                       {"AnnotationId": str(i[4])},
                       {"coord": pts, }]
            export_point["Data"].append(pts_ann)

        for i in polygon:
            coords = i[0]
            pts = []
            for coord in coords:
                pts.append({
                    "x": coord[0],
                    "y": coord[1],
                    "z": coord[2],
                })
            Area = {
                "area": 0,
                "Length": 0,
                "pts": pts,
            }
            pts_ann = [{"LabelName": str(i[1])},
                       {"LabelHierarchy": str(i[2])},
                       {"Filename": str(i[3])},
                       {"AnnotationId": str(i[4])},
                       {"Area": Area, }]
            export_polygon["Data"].append(pts_ann)

        out_file = open(output_point_path, "w")
        json.dump(export_point, out_file, indent=4)
        out_file.close()

        out_file = open(output_poly_path, "w")
        json.dump(export_polygon, out_file, indent=4)
        out_file.close()

        print("ok")

    elif exp == 'shp':
        # Export in a shp file for GIS analysis. We lost a part of the z information for polygons
        schema_polygon = {
            'geometry': 'Polygon',
            'properties': {
                'id': 'int',
                'z': 'float',
                'label_name': 'str',
                'label_hierarchy': 'str',
                'filename': 'str',
                'annotation_id_biigle': 'int'
            }
        }

        schema_point = {
            'geometry': 'Point',
            'properties': {
                'id': 'int',
                'z': 'float',
                'radius': 'float',
                'label_name': 'str',
                'label_hierarchy': 'str',
                'filename': 'str',
                'annotation_id_biigle': 'int'
            }
        }

        schema_LineString = {
            'geometry': 'LineString',
            'properties': {
                'id': 'int',
                'z': 'float',
                'label_name': 'str',
                'label_hierarchy': 'str',
                'filename': 'str',
                'annotation_id_biigle': 'int'
            }
        }

        id_img = 0
        id_poly = 1
        id_point = 1
        id_line = 1
        # write your shapefile, as projection of epsg: 4326
        output_path = os.path.join(output_path, '3DLayer')
        isExist = os.path.exists(output_path)
        if not isExist:
            os.makedirs(output_path)

        with fiona.open(output_path, 'w', 'ESRI Shapefile', layer='polygon', schema=schema_polygon,
                        crs=from_epsg(4326)) as out:
            for p in polygon:
                if len(p[0]) >= 3:
                    polygon_geom = Polygon(np.array(p[0])[:, 0:2])
                    out.write({
                        'geometry': mapping(polygon_geom),
                        'properties': {
                            'id': id_poly,
                            'z': np.array(p[0])[:, 2].mean(),
                            'label_name': p[1],
                            'label_hierarchy': p[2],
                            'filename': p[3],
                            'annotation_id_biigle': p[4],
                        }
                    })
                    id_poly += 1

        with fiona.open(output_path, 'w', 'ESRI Shapefile', layer='point', schema=schema_point,
                        crs=from_epsg(4326)) as out:
            for p in point:
                point_geom = Point(p[0][:2])
                out.write({
                    'geometry': mapping(point_geom),
                    'properties': {
                        'id': id_point,
                        'z': p[0][2],
                        'radius': p[5],
                        'label_name': p[1],
                        'label_hierarchy': p[2],
                        'filename': p[3],
                        'annotation_id_biigle': p[4],
                    }
                })
                id_point += 1

        with fiona.open(output_path, 'w', 'ESRI Shapefile', layer='line', schema=schema_LineString,
                        crs=from_epsg(4326)) as out:
            for p in line:
                if len(p[0]) >= 3:
                    line_geom = LineString(np.array(p[0])[:, 0:2])
                    out.write({
                        'geometry': mapping(line_geom),
                        'properties': {
                            'id': id_line,
                            'z': np.array(p[0])[:, 2].mean(),
                            'label_name': p[1],
                            'label_hierarchy': p[2],
                            'filename': p[3],
                            'annotation_id_biigle': p[4],
                        }
                    })
                    id_line += 1

    if thread is not None:
        thread.prog_val.emit(0)
        thread.finished.emit()
        thread.running = False


if __name__ == "__main__":
    sfm_path = r"D:\CHUBACARC_stage_marin\pl03\3D_model\sfm_data_exp.json"
    annotation_path = r"D:\CHUBACARC_stage_marin\pl03\annotations\44-pl03.csv"
    model_path = r"D:\CHUBACARC_stage_marin\pl03\3D_model\Global_model.ply"

    annotationsTo3D(annotation_path, sfm_path, model_path, exp='shp', label=False)