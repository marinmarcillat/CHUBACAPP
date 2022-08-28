# Detection and removal of blurry images, and removal from the .dim2 nav file
# Uses the variance of the Laplacian to get the amount of blur of images, and then filter them using student t test
# Blur detection based on Adrian Rosebrock fast fourier transform algorythm

import cv2
import os
from shutil import copy
import imghdr
import pandas as pd
from PyQt5 import QtCore

class BlurThread(QtCore.QThread):
    """Detects the blurry image and store their reference for later suppression"""
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, images):
        super(BlurThread, self).__init__()
        self.running = True
        self.images = images

    def run(self):
        """This starts the thread on the start() call"""
        window = 8
        data_path = os.path.join(os.getcwd(), "{}".format(self.images))

        fm_list = pd.DataFrame(
            {"file": [],
             "fm": []},
            index=[])
        i = 0
        tot_len = len(os.listdir(data_path))
        for file in os.listdir(data_path):  # for each image in the directory
            self.prog_val.emit(round((i/tot_len)*100))
            i += 1
            if os.path.isfile(os.path.join(data_path, file)):  # Check if is a file
                if imghdr.what(os.path.join(data_path, file)) == "jpeg":  # Check file is jpeg image
                    orig = cv2.imread(os.path.join(data_path, file))
                    fm_gray = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)  # Extract the grey channel
                    fm = cv2.Laplacian(fm_gray,
                                       cv2.CV_64F).var()  # Get the variance of the image Laplacian convolution results
                    fm_list = fm_list.append({'file': file, 'fm': fm},
                                             ignore_index=True)  # Store the metric and the image name

        fm_list["m_mean"] = fm_list["fm"].rolling(window=window, center=True).mean()
        fm_list["m_std"] = fm_list["fm"].rolling(window=window, center=True).std()
        fm_list["delta"] = (fm_list["m_mean"] - fm_list["fm"]) / fm_list["m_std"]
        fm_list.to_csv(os.path.join(data_path, 'deblur.csv')) #save blur values
        # user input to choose the filter level
        self.prog_val.emit(0)
        self.finished.emit()
        self.running = False


class FilterThread(QtCore.QThread):
    """
    Filters images detected by the blur detection class according to user input threshold level
    """
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, images, blur_data):
        super(FilterThread, self).__init__()
        self.running = True
        self.images = images
        self.blur_data = blur_data

    def run(self):
        # Create a "bin" directory to store all blurry images
        blurry_path = os.path.join(self.images, "blurry")
        isExist = os.path.exists(blurry_path)
        if not isExist:
            os.makedirs(blurry_path)

        tot_len = len(self.blur_data)
        for index, row in self.blur_data.iterrows():
            self.prog_val.emit((index / tot_len) * 100)
            if row["outlier"]:  # Cut the image to the bin
                copy(os.path.join(self.images, row["file"]), blurry_path)
                os.remove(os.path.join(self.images, row["file"]))

        self.prog_val.emit(0)
        self.finished.emit()
        self.running = False
