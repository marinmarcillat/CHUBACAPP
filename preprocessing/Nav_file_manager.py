"""
Functions to deal with dim2 navigation files
"""

import pandas as pd
import numpy as np
import os
from PyQt5 import QtCore
import imghdr
from shutil import copy

from utils import sfm, coord_conversions


def recalibration(nav_ori, nav_ref):
    """
    Recalibrate the navigation using a reference .txt navigation
    """
    nav_ori_trim = nav_ori.iloc[:, [1, 2, 5]]
    nav_ori_trim = nav_ori_trim.set_axis(["date", "time", "name"], axis=1, inplace=False)
    nav_ori_trim["datetime"] = pd.to_datetime(nav_ori_trim['date'] + nav_ori_trim['time'], format='%d/%m/%Y%H:%M:%S.%f')

    nav_ref_trim = nav_ref.iloc[:, [0, 1, 2, 3]]
    nav_ref_trim["datetime"] = pd.to_datetime(nav_ref_trim['Date'] + nav_ref_trim['Heure'],
                                              format='%d/%m/%Y%H:%M:%S.%f')

    combined = pd.merge_asof(nav_ori_trim, nav_ref_trim, on="datetime", direction='nearest')

    nav_updated = nav_ori
    nav_updated[6] = combined['latitude']
    nav_updated[7] = combined['longitude']
    return nav_updated


def optical_correction(nav, camera_points):
    nav_ori_trim = nav.iloc[:, [1, 2, 5]]
    nav_ori_trim = nav_ori_trim.set_axis(["date", "time", "filename"], axis=1, inplace=False)

    combined = pd.merge(nav_ori_trim, camera_points, on=['filename'])

    nav_updated = nav
    nav_updated[6] = combined['lat']
    nav_updated[7] = combined['long']
    return nav_updated


def concat_navigation(data_path):
    """
    Concatenate multiple navigation file together
    """
    combined = []
    for root, subdirs, files in os.walk(data_path):
        for file_i in files:
            if file_i[-5:] == ".dim2" and file_i[:4] == "acq_":
                nav_path = os.path.join(root, file_i)
                nav_data = pd.read_csv(nav_path, sep=";", header=None, dtype=str, na_filter=False)
                if len(combined) == 0:
                    combined = nav_data
                else:
                    combined = pd.concat([combined, nav_data])
    return combined


def save_dim2(nav_data, output_path):
    """
    Save dim2 file
    """
    nav_df = nav_data.to_numpy()
    output_file = open(output_path, "w")
    np.savetxt(output_file, nav_df, delimiter=';', fmt="%s")
    output_file.close()


def copy_img(data_path, output_path):
    """
    Copy only images from a data_path directory to another
    """
    for root, subdirs, files in os.walk(data_path):
        for file_i in files:
            file_path = os.path.join(root, file_i)
            if os.path.isfile(file_path):
                if imghdr.what(file_path) == "jpeg":
                    copy(file_path, os.path.join(output_path, file_i))


class NavThread(QtCore.QThread):
    """
    Thread for the ChubacApp GUI
    """
    finished = QtCore.pyqtSignal()

    def __init__(self, data_path, output_path, output_name, nav_correction, optical, ref_nav_path,
                 sfm_data_path, model_origin_path, copy):
        super(NavThread, self).__init__()
        self.running = True
        self.data_path = data_path
        self.output_path = output_path
        self.output_name = output_name
        self.nav_correction = nav_correction
        self.optical_correction = optical
        self.sfm_data_path = sfm_data_path
        self.model_origin_path = model_origin_path
        self.ref_nav_path = ref_nav_path
        self.copy = copy

    def run(self):

        nav = concat_navigation(self.data_path)

        if self.nav_correction:
            if os.path.isfile(self.ref_nav_path):
                nav_ref = pd.read_csv(self.ref_nav_path, sep="\t")
                nav_updated = recalibration(nav, nav_ref)
        elif self.optical_correction:
            if os.path.isfile(self.sfm_data_path) and os.path.isfile(self.model_origin_path):
                list_img = list(nav[5].unique())
                sfm_data, temp_sfm_data_path = sfm.sfm_data_handler(self.sfm_data_path, list_img)
                camera_points = sfm.extract_camera_points(sfm_data)

                with open(self.model_origin_path) as f:
                    d = f.readlines()
                model_origin = list(map(float, d[0].split(";")))

                geographic_coords = coord_conversions.local_2_position2d(camera_points, model_origin)
                geo_camera_points = pd.concat([camera_points, geographic_coords], axis=1)

                nav_updated = optical_correction(nav, geo_camera_points)
        else:
            nav_updated = nav
        save_dim2(nav_updated, os.path.join(self.output_path, self.output_name + '.dim2'))

        if self.copy:
            copy_img(self.data_path, self.output_path)

        self.finished.emit()
        self.running = False
