from multiprocessing import Pool
import numpy as np
import os, imghdr
from shutil import copy
import pandas as pd
from tqdm import tqdm
from time import sleep
from scipy.spatial import distance_matrix
from PyQt5 import QtCore

import CHUBACAPP.utils.pyvista_utils as pv_utils
import CHUBACAPP.utils.sfm as sfm
import CHUBACAPP.post_reprojection.permutator as pm
import CHUBACAPP.blender.blender_reprojection as brp
import CHUBACAPP.utils.export_annotations as exp_tools


class DISThread(QtCore.QThread):
    """Detects the blurry image and store their reference for later suppression"""
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, sfm_path, model_path, camera_model, img_path, method):
        super(DISThread, self).__init__()
        self.running = True
        self.sfm_path = sfm_path
        self.model_path = model_path
        self.camera_model = camera_model
        self.img_path = img_path
        self.method = method

    def run(self):
        disjoint_image_selection(self.sfm_path, self.model_path, self.camera_model, self.img_path, self.method, self)


def disjoint_image_selection(sfm_path, model_path, camera_model, img_path, method, thread=None):
    dist_filter = 12

    output_path = os.path.join(img_path, "disjoint_img_selection")
    isExist = os.path.exists(output_path)
    if not isExist:
        os.makedirs(output_path)

    print("Initiating...")
    if thread is not None:
        thread.prog_val.emit(round(0))

    sfm_data = sfm.sfm_data_handler(sfm_path, None, True)
    camera_points = sfm.extract_camera_points(sfm_data)
    dm = camera_points_distance_matrix(camera_points)
    list_img_model = camera_points['filename'].unique()
    list_img = list_image_in_model(img_path, list_img_model)
    print("Done !")

    print("Getting image bound... {} images to reproject".format(len(list_img)))
    json_path = get_bounds(list_img, sfm_path, model_path, output_path, camera_model)
    print("Done !")

    print("Getting contact matrix...")
    M, volumes = contact_matrix(json_path, dm, dist_filter, thread)
    pd.DataFrame(M).to_csv(os.path.join(output_path, 'contact_matrix.csv'), index=False, header=False)
    print("Done !")

    print("Image selection...")
    if method == "Forward":
        keep = pm.forward(M)
    elif method == "permutations":
        keep = pm.permutate(M)
    else:
        print("Not a valid method, aborting...")
        if thread is not None:
            thread.prog_val.emit(0)
            thread.finished.emit()
            thread.running = False

        return 0
    print("Done !")

    pv_utils.save_volumes(volumes, keep, output_path)
    filter_images(img_path, keep, volumes)
    print("Saved !")

    if thread is not None:
        thread.prog_val.emit(0)
        thread.finished.emit()
        thread.running = False

    return 1


def contact_matrix(json_path, dm, dist_filter, thread=None):
    annotations = pv_utils.parse_annotation(json_path)
    ann_volumes = []
    if thread is not None:
        thread.prog_val.emit(0)
        prog = 0
        tot_len = len(annotations)
    for annotation in annotations:
        if thread is not None:
            thread.prog_val.emit(round((prog / tot_len) * 100))
            prog += 1
        if annotation[0] == 'bound' and len(annotation[1]) != 1:
            mesh = pv_utils.points_to_mesh(annotation[1])
            volume = pv_utils.get_volume(mesh)
            filename = annotation[2]
            ann_volumes.append([filename, volume])

    print("Starting contact analysis... {} images to analyse".format(len(ann_volumes)))
    contact_matrix = np.zeros(shape=(len(ann_volumes), len(ann_volumes)))
    if thread is not None:
        thread.prog_val.emit(0)
        tot_len = len(ann_volumes)
    for i in range(len(ann_volumes)):
        if thread is not None:
            thread.prog_val.emit(round((i / tot_len) * 100))
        for j in range(len(ann_volumes)):
            if dm[i, j] < dist_filter:
                k, intersection = ann_volumes[i][1].collision(ann_volumes[j][1], 1)
                if intersection:
                    contact_matrix[i, j] = 1
    print("Done !")

    return contact_matrix, ann_volumes


def camera_points_distance_matrix(camera_points):
    positions = []
    for index, row in camera_points.iterrows():
        positions.append([float(row['x']), float(row['y']), float(row['z'])])

    dm = distance_matrix(positions, positions)
    return dm


def multi_process_reprojection(args):
    sfm_path, model_path, list_imgs, camera_model, annotations, i = args
    sleep(i * 10)  # avoid problems in json read
    ann23d = brp.annotationsTo3D(sfm_path, model_path, list_imgs, camera_model)

    polygon = []
    for image in list_imgs:
        result = ann23d.reproject(annotations, image, False)
        polygon.extend(result[2])

    return polygon


def get_bounds(list_imgs, sfm_path, model_path, output_path, camera_model):
    multipro = True
    annotations = pd.DataFrame(
        columns=['filename', 'shape_name', 'points', 'label_name', 'label_hierarchy', 'annotation_id'])

    nb_processes = 8
    img_list_split = np.array_split(list_imgs, nb_processes)
    args = []
    i = 0
    for img_list_i in img_list_split:
        args.append([sfm_path, model_path, img_list_i, camera_model, annotations, i])
        i += 1

    if multipro:
        print("Starting multiprocessing reprojection...")
        results = list(Pool(nb_processes).map(multi_process_reprojection, args))
        print("Done !")

    else:
        results = []
        for arg in args:
            results.append(multi_process_reprojection(arg))

    polygon = []
    for result in results:
        polygon.extend(result)

    json_path = exp_tools.save_bounds_polygons(output_path, polygon)

    return json_path


def filter_images(data_path, keep, volumes):
    img_to_keep = []
    for i in range(len(volumes)):
        if keep[i]:
            img_to_keep.append(volumes[i][0])

    select_path = os.path.join(data_path, "disjoint_img_selection")
    isExist = os.path.exists(select_path)
    if not isExist:
        os.makedirs(select_path)

    for file in os.listdir(data_path):  # for each image in the directory
        if os.path.isfile(os.path.join(data_path, file)):  # Check if is a file
            if imghdr.what(os.path.join(data_path, file)) == "jpeg":
                if file in img_to_keep:
                    copy(os.path.join(data_path, file), select_path)


def list_image_in_model(dir, img_in_model):
    list_img = []
    for file in os.listdir(dir):  # for each image in the directory
        if os.path.isfile(os.path.join(dir, file)):  # Check if is a file
            if imghdr.what(os.path.join(dir, file)) == "jpeg":
                if file in img_in_model:
                    list_img.append(file)
    return list_img
