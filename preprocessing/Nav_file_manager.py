"""
Functions to deal with dim2 navigation files
"""

import pandas as pd
import numpy as np
import os
from PyQt5 import QtCore
import imghdr
from shutil import copy


def recalibration(nav_ori, nav_ref):
    """
    Recalibrate the navigation using a reference .txt navigation
    """
    nav_ori_trim = nav_ori.iloc[:, [1, 2, 5]]
    nav_ori_trim = nav_ori_trim.set_axis(["date", "time", "name"], axis=1, inplace=False)
    nav_ori_trim["datetime"] = pd.to_datetime(nav_ori_trim['date'] + nav_ori_trim['time'], format='%d/%m/%Y%H:%M:%S.%f')

    nav_ref_trim = nav_ref.iloc[:, [0, 1, 2, 3]]
    nav_ref_trim["datetime"] = pd.to_datetime(nav_ref_trim['Date'] + nav_ref_trim['Heure'], format='%d/%m/%Y%H:%M:%S.%f')

    combined = pd.merge_asof(nav_ori_trim, nav_ref_trim, on="datetime", direction = 'nearest')

    nav_updated = nav_ori
    nav_updated[6] = combined['latitude']
    nav_updated[7] = combined['longitude']
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

    def __init__(self, data_path, output_path, output_name, ref_nav_path, copy):
        super(NavThread, self).__init__()
        self.running = True
        self.data_path = data_path
        self.output_path = output_path
        self.output_name = output_name
        self.ref_nav_path = ref_nav_path
        self.copy = copy

    def run(self):

        self.nav = concat_navigation(self.data_path)

        if os.path.isfile(self.ref_nav_path):
            self.nav_ref = pd.read_csv(self.nav_ref_path, sep="\t")
            self.nav_updated = recalibration(self.nav, self.nav_ref)
            save_dim2(self.nav_updated, os.path.join(self.output_path, self.output_name+ '.dim2'))
        else:
            save_dim2(self.nav, os.path.join(self.output_path, self.output_name + '.dim2'))

        if self.copy:
            copy_img(self.data_path, self.output_path)

        self.finished.emit()
        self.running = False

