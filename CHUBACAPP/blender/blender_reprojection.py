import os
from ast import literal_eval
from math import dist
import pyvista as pv
from multiprocessing import Pool

import itertools
import numpy as np
import pandas as pd
from PyQt5 import QtCore
import cv2

import CHUBACAPP.blender.camera_config as cc
import CHUBACAPP.utils.export_annotations as exp_tools
import CHUBACAPP.utils.sfm as sfm_tools
import CHUBACAPP.utils.video as video


class annotationsTo3DThread(QtCore.QThread):
    '''
    Thread class for Chubacapp GUI
    '''
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, annotation_path, sfm_data_path, model_path, exp, origin_coords, label, camera_model,
                 video_annotations=False,
                 video_path=None, time_interval=None, image_path=None):
        super(annotationsTo3DThread, self).__init__()
        self.running = True
        self.annotation_path = annotation_path
        self.sfm_data_path = sfm_data_path
        self.model_path = model_path
        self.exp = exp
        self.origin_coords = origin_coords
        self.label = label
        self.camera_model = camera_model
        self.video_annotations = video_annotations
        if self.video_annotations:
            self.video_path = video_path
            self.time_interval = time_interval
            self.image_path = image_path

        self.output_path = os.path.dirname(annotation_path)

    def run(self):
        if self.video_annotations:
            print("Retrieve annotations tracks...")
            annotations, fn_ts = video.get_annotations_tracks(self.annotation_path, self.image_path, self.video_path,
                                                       self.time_interval)

            fn_ts_path = os.path.join(self.output_path, "filename_timestamp.csv")
            fn_ts.to_csv(fn_ts_path, index=False)

            print("Done !")
        else:
            annotations = pd.read_csv(self.annotation_path, sep=",")
            for i, row in annotations.iterrows():
                annotations.at[i, 'points'] = literal_eval(row['points'])

        img_list = list(annotations['filename'].unique())
        nb_processes = 4
        img_list_split = np.array_split(img_list, nb_processes)
        args = []
        for img_list_i in img_list_split:
            annotations_i = annotations.loc[annotations['filename'].isin(img_list_i.tolist())]
            args.append([self.sfm_data_path, self.model_path, img_list_i, self.camera_model, annotations_i, self.label])

        print("Starting multiprocessing reprojection...")
        results = list(Pool(nb_processes).map(process_annotationTo3D, args))
        print("Done !")

        point, line, polygon = [[], [], []]
        for result in results:
            point.extend(result[0])
            line.extend(result[1])
            polygon.extend(result[2])

        exp_tools.export_3d_annotations(self.exp, self.output_path, point, line, polygon, self.origin_coords, self)


def process_annotationTo3D(args):
    sfm_data_path, model_path, img_list, camera_model, annotations, label = args
    ann23d = annotationsTo3D(sfm_data_path, model_path, img_list, camera_model)
    point, line, polygon = ann23d.batch_reproject(annotations, label)
    return point, line, polygon


def annotationsTo3D(sfm_data_path, model_path, list_ann_img, camera_model, thread=None):
    import bpy
    from mathutils import Vector

    from CHUBACAPP.photogrammetry_importer.blender_utility.object_utility import add_collection
    from CHUBACAPP.photogrammetry_importer.file_handlers.openmvg_json_file_handler import (
        OpenMVGJSONFileHandler,
    )
    from CHUBACAPP.photogrammetry_importer.importers.camera_utility import add_camera_object
    from CHUBACAPP.photogrammetry_importer.types.camera import Camera

    class reproject:

        def __init__(self, sfm_data_path, model_path, list_ann_img, camera_model, thread=None):
            if thread is not None:
                self.thread = thread
            else:
                self.thread = None
            self.model_path = model_path
            self.min_radius = 0.01

            sfm_data, temp_sfm_path = sfm_tools.sfm_data_handler(sfm_data_path, list_ann_img)
            intrinsics = sfm_data['intrinsics'][0]['value']['ptr_wrapper']['data']
            self.resolution = [intrinsics['height'], intrinsics['width']]

            camera_parameters = cc.load_cameras()
            optical_camera_matrix = np.array(camera_parameters[camera_model]["optical_camera_matrix"], dtype='f')
            # -> Distortion coefficients
            dist_coeff = np.array(camera_parameters[camera_model]["dist_coeff"], dtype='f')
            # -> Original resolution (width, height)
            (w, h) = camera_parameters[camera_model]["resolution"]

            newcameramtx, roi = cv2.getOptimalNewCameraMatrix(optical_camera_matrix, dist_coeff, (w, h), 1, (w, h))
            # create undistortion maps
            self.mapx, self.mapy = cv2.initUndistortRectifyMap(optical_camera_matrix, dist_coeff, None, newcameramtx,
                                                               (w, h), 5)

            self.min_x = roi[0]
            self.max_x = roi[0] + roi[2]
            self.min_y = roi[1]
            self.max_y = roi[1] + roi[3]

            self.scale_x_sfm = intrinsics['width'] / w
            self.scale_y_sfm = intrinsics['height'] / h

            self.x_original_center = w / 2
            self.y_original_center = h / 2

            self.x_sfm_center = intrinsics['width'] / 2
            self.y_sfm_center = intrinsics['height'] / 2

            # initialize blender
            self.scene = bpy.data.scenes["Scene"]
            self.objects = bpy.data.objects

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
            self.cam_list = []
            for cam in cameras:
                cam_name = cam.get_file_name()
                self.cam_list.append(cam_name)
                self.camera_object = add_camera_object(cam, cam_name, camera_collection)

            # objects to consider
            print("opening model")
            bpy.ops.import_mesh.ply(filepath=self.model_path)
            model_name = os.path.splitext(os.path.basename(self.model_path))[0]
            bpy.data.objects[model_name].rotation_euler = (0, 0, 0)
            self.target = bpy.data.objects[model_name]
            print("Done !")

            # List of points corresponding to the image bound
            edge1 = [(x, self.min_y + 1) for x in range(self.min_x + 1, self.max_x - 1)]
            edge2 = [(self.max_x - 1, y) for y in range(self.min_y + 1, self.max_y - 1)]
            edge3 = [(x, self.max_y - 1) for x in range(self.max_x - 1, self.min_x + 1, -1)]
            edge4 = [(self.min_x + 1, y) for y in range(self.max_y - 1, self.min_y + 1, -1)]
            points_bound = edge1 + edge2 + edge3 + edge4
            self.points_bound = list(itertools.chain(*points_bound))

        def initiate_debug(self):
            self.mesh = pv.read(self.model_path)

        def plot_annotations(self, annotations):
            p = pv.Plotter()
            p.add_mesh(self.mesh)
            for annotation in annotations:
                p.add_mesh(pv.Sphere(annotation[3], annotation[:3]), color="red")
            p.show()

        def get_hit_points(self, image):
            # get all hit point between rays and target

            # camera object which defines ray source
            # create the first camera object
            cam = bpy.data.objects[image]
            self.scene.collection.objects.link(cam)

            self.scene.render.pixel_aspect_x = 1.0
            self.scene.render.pixel_aspect_y = 1.0
            self.scene.render.resolution_x = self.resolution[1]
            self.scene.render.resolution_y = self.resolution[0]

            # get vectors which define view frustum of camera
            frame = cam.data.view_frame(scene=self.scene)
            topRight = frame[0]
            bottomLeft = frame[2]
            topLeft = frame[3]

            # setup vectors to match pixels
            xRange = np.linspace(topLeft[0], topRight[0], self.resolution[1])
            yRange = np.linspace(topLeft[1], bottomLeft[1], self.resolution[0])

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
            matrixWorld = self.target.matrix_world
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
                    hit, location, norm, face = self.target.ray_cast(origin=origin, direction=direction)
                    if hit:
                        values[indexX, indexY] = (matrixWorld @ location)

                    # update indices
                    indexY += 1

                indexX += 1
                indexY = 0
            return values

        def annotation2hitpoint(self, ann_coords):
            (x, y) = ann_coords
            if self.min_x < x < self.max_x and self.min_y < y < self.max_y:
                # Undistort coordinates
                und_x, und_y = (self.mapx[round(y), round(x)], self.mapy[round(y), round(x)])

                # resize from original image size to openMVG image size
                x_scaled = round((und_x - self.x_original_center) * self.scale_x_sfm + self.x_sfm_center)
                y_scaled = round((und_y - self.y_original_center) * self.scale_y_sfm + self.y_sfm_center)

                # Get the location of the intersection between ray and target
                if 0 <= x_scaled < len(self.hit_points) and 0 <= y_scaled < len(self.hit_points[0]):
                    coord = self.hit_points[x_scaled][y_scaled]
                    return coord
            return None

        def reproject(self, annotations, image, label):
            point = []
            polygon = []
            line = []
            if image in self.cam_list:
                self.hit_points = self.get_hit_points(image)
                if label:
                    annotations['shape_name'] = 'Rectangle'
                    annotations['points'] = self.points_bound
                    annotations['annotation_id'] = 999
                else:
                    image_bound = pd.DataFrame({
                        'filename': [image],
                        'shape_name': ['Rectangle'],
                        'points': [self.points_bound],
                        'label_name': ['bound'],
                        'label_hierarchy': ['bound'],
                        'annotation_id': [999],
                    })
                    annotations = pd.concat([annotations, image_bound])

                for index, ann in annotations.iterrows():  # for each annotation
                    if ann['shape_name'] in ['Circle', 'Point']:  # if the annotation is a point or a circle
                        x, y = ann['points'][:2]

                        # get the location of the intersection between ray and target
                        coord = self.annotation2hitpoint((x, y))

                        if coord is not None:  # If we have a hit point
                            if ann['shape_name'] == 'Circle':
                                # If the annotation is a circle, we try to get an approximate radius by looking
                                # North, South, East and West from the center. We then keep the minimal distance
                                # obtained
                                radius = []  # min arbitrary value
                                r = ann['points'][2]
                                list_coord_r = [(x + r, y), (x - r, y), (x, y + r), (x, y - r)]
                                for i in list_coord_r:
                                    # get the location of the intersection between ray and target
                                    coord_radius = self.annotation2hitpoint((i[0], i[1]))

                                    if coord_radius is not None:
                                        ct = [coord[0], coord[1]]
                                        off = [coord_radius[0], coord_radius[1]]
                                        radius.append(dist(ct, off))
                                if len(radius) != 0:
                                    # If no other point is found, set the radius to an arbitrary small value
                                    radius = min(radius)
                                else:
                                    radius = self.min_radius
                            else:
                                radius = 0
                            point.append([[coord[0], coord[1], coord[2]], ann['label_name'], ann['label_hierarchy'],
                                          ann['filename'],
                                          ann['annotation_id'], radius])

                    elif ann['shape_name'] == 'LineString':  # if geometry is a line
                        list_coord = list(zip(*[iter(ann['points'])] * 2))
                        points_out = []
                        for i in list_coord:
                            # get the location of the intersection between ray and target
                            coord = self.annotation2hitpoint((i[0], i[1]))
                            if coord is not None:
                                points_out.append([coord[0], coord[1], coord[2]])
                        if len(points_out) != 0:
                            line.append(
                                [points_out, ann['label_name'], ann['label_hierarchy'], ann['filename'],
                                 ann['annotation_id']])

                    elif ann['shape_name'] in ['Polygon', 'Rectangle']:  # if geometry is a polygon or rectangle
                        list_coord = list(zip(*[iter(ann['points'])] * 2))
                        points_out = []

                        for i in list_coord:  # For all the points of the polygone
                            # get the location of the intersection between ray and target
                            coord = self.annotation2hitpoint((i[0], i[1]))

                            if coord is not None:
                                points_out.append([coord[0], coord[1], coord[2]])
                        if len(points_out) != 0:  # If more than one point exist
                            polygon.append(
                                [points_out, ann['label_name'], ann['label_hierarchy'], ann['filename'],
                                 ann['annotation_id']])
            else:
                print("Image not in model !")

            return point, line, polygon

        def batch_reproject(self, annotations, label):
            point = []
            polygon = []
            line = []
            prog = 0
            tot_len = len(annotations['filename'].unique())
            print("Start annotations analysis...")
            for image in annotations['filename'].unique():
                if self.thread is not None:
                    self.thread.prog_val.emit(round((prog / tot_len) * 100))
                prog += 1
                s = str(round((prog / tot_len) * 100)) + " %, " + str(prog) + " / " + str(tot_len)
                print(s, end="\r")

                ann_img = annotations.loc[annotations['filename'] == image]
                result = self.reproject(ann_img, image, label)
                point.extend(result[0])
                line.extend(result[1])
                polygon.extend(result[2])

            return point, line, polygon,

    return reproject(sfm_data_path, model_path, list_ann_img, camera_model, thread)
