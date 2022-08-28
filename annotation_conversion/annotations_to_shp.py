from osgeo import gdal, osr
from geopy.distance import distance as dist
import pandas as pd
import cv2 as cv
import numpy as np
import fiona
from fiona.crs import from_epsg
from shapely.geometry import Point, Polygon, LineString, mapping
import ast
import os
import sys
from tqdm import tqdm
from PyQt5 import QtCore
import imghdr

'''
Convert Biigle annotations to 2D annotations using geotiff from Matisse software
Uses features matching to get an homographic matrix, than use it to convert annotations coordinates
Less precise than 3D reprojection
'''

MIN_MATCH_COUNT = 10

# Schematic structure for shp export
schema_polygon = {
    'geometry': 'Polygon',
    'properties': {
        'id': 'int',
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
        'label_name': 'str',
        'label_hierarchy': 'str',
        'filename': 'str',
        'annotation_id_biigle': 'int'
    }
}

schema_polygon_labels = {
    'geometry': 'Polygon',
    'properties': {
        'id': 'int',
        'label_name': 'str',
        'label_hierarchy': 'str',
        'filename': 'str',
        'label_id_biigle': 'int'
    }
}


def homographic_trsf(homography, coord):
    """
    Fonction to convert coordinates using an homographic matrix
    """
    x, y = coord
    p = np.array((x, y, 1)).reshape((3, 1))
    temp_p = homography.dot(p)
    sum = np.sum(temp_p, 1)
    px = int(round(sum[0] / sum[2]))
    py = int(round(sum[1] / sum[2]))
    return [px, py]


def geographic_trsf(trsf, c_t, coord):
    """
    Fonction to convert coordinates to a specific geo referential
    """
    x, y = coord
    px, py = gdal.ApplyGeoTransform(trsf, x, y)
    (lat, long, z) = c_t.TransformPoint(px, py)
    return [long, lat]


class Ann_to_shpThread(QtCore.QThread):
    '''
    Thread for the Chubacapp GUI
    '''
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, data_path, annotations_path, output_path_name="Layers"):
        super(Ann_to_shpThread, self).__init__()
        self.running = True
        self.data_path = data_path
        self.annotations_path = annotations_path
        self.output_path_name = output_path_name

    def run(self):
        matisse_output_name = "MyProcessing_"
        annotations = pd.read_csv(self.annotations_path)

        output_path = os.path.join(self.data_path, self.output_path_name)

        id_img = 0
        id_poly = 1
        id_point = 1
        id_line = 1
        poly = []
        point = []
        line = []
        tot_len = len(os.listdir(self.data_path))
        prog_bar = 0
        for file in sorted(os.listdir(self.data_path)):  # for each image in the directory
            self.prog_val.emit(round((prog_bar / tot_len) * 100))
            prog_bar += 1
            jpg_path = os.path.join(self.data_path, file)
            if os.path.isfile(jpg_path):  # Check if is a file
                if imghdr.what(jpg_path) == "jpeg":
                    tiff_str = matisse_output_name + f'{id_img:04d}' + '.tiff'
                    tiff_path = os.path.join(self.data_path, tiff_str)
                    id_img += 1

                    ann_img = annotations.loc[annotations['filename'] == file]

                    img1 = cv.imread(str(jpg_path), 0)  # queryImage
                    img2 = cv.imread(str(tiff_path), 0)  # trainImage

                    ##### HOMOGRAPHY #####
                    # Determine the homographic matrix using feature detection

                    # Initiate SIFT detector
                    sift = cv.SIFT_create()
                    # find the keypoints and descriptors with SIFT
                    kp1, des1 = sift.detectAndCompute(img1, None)
                    kp2, des2 = sift.detectAndCompute(img2, None)
                    FLANN_INDEX_KDTREE = 1
                    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
                    search_params = dict(checks=50)
                    flann = cv.FlannBasedMatcher(index_params, search_params)
                    matches = flann.knnMatch(des1, des2, k=2)
                    # store all the good matches as per Lowe's ratio test.
                    good = []
                    for m, n in matches:
                        if m.distance < 0.7 * n.distance:
                            good.append(m)

                    if len(good) > MIN_MATCH_COUNT:
                        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
                        M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 5.0)

                    else:
                        print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
                        matchesMask = None
                        break

                    ##### GEOGRAPHIC #####
                    # Get the transformation from geotiff coordinates to WGS84

                    src_ds = gdal.Open(str(tiff_path))
                    gt_forward = src_ds.GetGeoTransform()

                    # get CRS from dataset
                    crs = osr.SpatialReference()
                    crs.ImportFromWkt(src_ds.GetProjectionRef())
                    # create lat/long crs with WGS84 datum
                    crsGeo = osr.SpatialReference()
                    crsGeo.ImportFromEPSG(4326)  # 4326 is the EPSG id of lat/long crs
                    c_t = osr.CoordinateTransformation(crs, crsGeo)

                    for index, ann in ann_img.iterrows():
                        if ann['shape_name'] in ['Circle', 'Point', 'Ellipse']:  # if geometry is a point or a circle
                            coord = ast.literal_eval(ann['points'])[:2]
                            coord_trsf = homographic_trsf(M, coord)
                            coord_fin = geographic_trsf(gt_forward, c_t, coord_trsf)
                            if ann['shape_name'] == 'Circle':
                                r = ast.literal_eval(ann['points'])[2]
                                coord_r = (coord[0] + r, coord[1])
                                coord_r_trsf = homographic_trsf(M, coord_r)
                                coord_r_fin = geographic_trsf(gt_forward, c_t, coord_r_trsf)
                                radius = dist(coord_fin[::-1], coord_r_fin[::-1]).m
                            else:
                                radius = 0
                            point.append([coord_fin, radius, ann['label_name'], ann['label_hierarchy'], ann['filename'],
                                          ann['annotation_id']])

                        elif ann['shape_name'] in ['Polygon', 'Rectangle']:  # if geometry is a polygon or rectangle
                            coord = list(zip(*[iter(ast.literal_eval(ann['points']))] * 2))
                            coord_fin = []
                            for i in coord:
                                coord_trsf = homographic_trsf(M, i)
                                coord_fin.append(geographic_trsf(gt_forward, c_t, coord_trsf))
                            poly.append([coord_fin, ann['label_name'], ann['label_hierarchy'], ann['filename'],
                                         ann['annotation_id']])

                        elif ann['shape_name'] == 'LineString':  # if geometry is a line
                            coord = list(zip(*[iter(ast.literal_eval(ann['points']))] * 2))
                            coord_fin = []
                            for i in coord:
                                coord_trsf = homographic_trsf(M, i)
                                coord_fin.append(geographic_trsf(gt_forward, c_t, coord_trsf))
                            line.append([coord_fin, ann['label_name'], ann['label_hierarchy'], ann['filename'],
                                         ann['annotation_id']])

        # write your shapefile, as projection of epsg: 4326
        with fiona.open(output_path, 'w', 'ESRI Shapefile', layer='polygon', schema=schema_polygon,
                        crs=from_epsg(4326)) as out:
            for p in poly:
                polygon_geom = Polygon(p[0])
                out.write({
                    'geometry': mapping(polygon_geom),
                    'properties': {
                        'id': id_poly,
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
                point_geom = Point(p[0])
                out.write({
                    'geometry': mapping(point_geom),
                    'properties': {
                        'id': id_point,
                        'radius': p[1],
                        'label_name': p[2],
                        'label_hierarchy': p[3],
                        'filename': p[4],
                        'annotation_id_biigle': p[5],
                    }
                })
                id_point += 1

        with fiona.open(output_path, 'w', 'ESRI Shapefile', layer='line', schema=schema_LineString,
                        crs=from_epsg(4326)) as out:
            for p in line:
                line_geom = LineString(p[0])
                out.write({
                    'geometry': mapping(line_geom),
                    'properties': {
                        'id': id_line,
                        'label_name': p[1],
                        'label_hierarchy': p[2],
                        'filename': p[3],
                        'annotation_id_biigle': p[4],
                    }
                })
                id_line += 1

        self.prog_val.emit(0)
        self.finished.emit()
        self.running = False


class Lab_to_shpThread(QtCore.QThread):
    '''
    Same thing but for labels
    '''
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, data_path, labels_path, output_path_name="Layers"):
        super(Lab_to_shpThread, self).__init__()
        self.running = True
        self.data_path = data_path
        self.labels_path = labels_path
        self.output_path_name = output_path_name

    def run(self):
        matisse_output_name = "MyProcessing_"
        labels = pd.read_csv(self.labels_path)
        output_path = os.path.join(self.data_path, self.output_path_name)

        id_img = 0
        id_poly = 1
        poly = []

        coord = [[0, 0], [6000, 0], [6000, 4000], [0, 4000]]
        prog_bar = 0
        tot_len = len(os.listdir(self.data_path))
        for file in sorted(os.listdir(self.data_path)):  # for each image in the directory
            self.prog_val.emit(round((prog_bar / tot_len) * 100))
            prog_bar += 1  # for each image in the directory

            jpg_path = os.path.join(self.data_path, file)
            if os.path.isfile(jpg_path):  # Check if is file
                if imghdr.what(jpg_path) == "jpeg":
                    img = file
                    tiff_str = matisse_output_name + f'{id_img:04d}' + '.tiff'
                    tiff_path = os.path.join(self.data_path, tiff_str)
                    id_img += 1

                    lab_img = labels.loc[labels['filename'] == img]

                    img1 = cv.imread(str(jpg_path), 0)  # queryImage
                    img2 = cv.imread(str(tiff_path), 0)  # trainImage

                    ##### HOMOGRAPHY #####

                    # Initiate SIFT detector
                    sift = cv.SIFT_create()
                    # find the keypoints and descriptors with SIFT
                    kp1, des1 = sift.detectAndCompute(img1, None)
                    kp2, des2 = sift.detectAndCompute(img2, None)
                    FLANN_INDEX_KDTREE = 1
                    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
                    search_params = dict(checks=50)
                    flann = cv.FlannBasedMatcher(index_params, search_params)
                    matches = flann.knnMatch(des1, des2, k=2)
                    # store all the good matches as per Lowe's ratio test.
                    good = []
                    for m, n in matches:
                        if m.distance < 0.7 * n.distance:
                            good.append(m)

                    if len(good) > MIN_MATCH_COUNT:
                        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
                        M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 5.0)

                    else:
                        print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
                        matchesMask = None
                        break

                    ##### GEOGRAPHIC #####

                    src_ds = gdal.Open(str(tiff_path))
                    gt_forward = src_ds.GetGeoTransform()

                    # get CRS from dataset
                    crs = osr.SpatialReference()
                    crs.ImportFromWkt(src_ds.GetProjectionRef())
                    # create lat/long crs with WGS84 datum
                    crsGeo = osr.SpatialReference()
                    crsGeo.ImportFromEPSG(4326)  # 4326 is the EPSG id of lat/long crs
                    c_t = osr.CoordinateTransformation(crs, crsGeo)

                    for index, lab in lab_img.iterrows():
                        coord_fin = []
                        for i in coord:
                            coord_trsf = homographic_trsf(M, i)
                            coord_fin.append(geographic_trsf(gt_forward, c_t, coord_trsf))
                        poly.append(
                            [coord_fin, lab['label_name'], lab['label_hierarchy'], lab['filename'], lab['label_id']])

        # write your shapefile, as projection of epsg: 4326
        with fiona.open(output_path, 'w', 'ESRI Shapefile', layer='label_polygons', schema=schema_polygon_labels,
                        crs=from_epsg(4326)) as out:
            for p in poly:
                polygon_geom = Polygon(p[0])
                out.write({
                    'geometry': mapping(polygon_geom),
                    'properties': {
                        'id': id_poly,
                        'label_name': p[1],
                        'label_hierarchy': p[2],
                        'filename': p[3],
                        'label_id_biigle': p[4],
                    }
                })
                id_poly += 1

        self.prog_val.emit(0)
        self.finished.emit()
        self.running = False
