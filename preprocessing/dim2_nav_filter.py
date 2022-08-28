import os
import pandas as pd
import imghdr
import numpy as np
from PyQt5 import QtCore

class filter_navThread(QtCore.QThread):
    '''Does the work'''
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, data_path, dim2_path, output_name = r"filtered_nav.dim2"):
        super(filter_navThread, self).__init__()
        self.running = True
        self.data_path = data_path
        self.dim2_path = dim2_path
        self.output_name = output_name

    def run(self):
        '''This starts the thread on the start() call'''
        filter_nav(self.data_path, self.dim2_path, self.output_name, self)


def filter_nav(data_path, dim2_path, output_name = r"filtered_nav.dim2", thread = None):
    # Filters navigation dim2 files according to image in the data_path file
    nav_data = pd.read_csv(dim2_path, sep=";", header=None, dtype=str, na_filter=False)

    list_img = []
    for file in os.listdir(data_path):  # for each image in the directory
        file_path = os.path.join(data_path, file)
        if os.path.isfile(file_path):  # Check if is a file
            if imghdr.what(file_path) == "jpeg":
                list_img.append(file)

    updated_nav = nav_data[nav_data[5].isin(list_img)]

    output_path = os.path.join(data_path, output_name)
    nav_df = updated_nav.to_numpy()
    output_file = open(output_path, "w")
    np.savetxt(output_file, nav_df, delimiter=';', fmt="%s")
    output_file.close()

    if thread is not None:
        thread.prog_val.emit(0)
        thread.finished.emit()
        thread.running = False

if __name__ == "__main__":
    dim2_path = r"D:\CHUBACARC_stage_marin\pl03\sub_mosaic_3D_PL03\sub_mosaic_3D_pl03_7\output_nav_ref_PL03.dim2"
    data_path = r"D:\CHUBACARC_stage_marin\pl03\sub_mosaic_3D_PL03\sub_mosaic_3D_pl03_7"
    output_name = r"filtered_nav.dim2"

    filter_nav(data_path, dim2_path, output_name)
