"""
Main file of the ChubacApp GUI
Written using the QT5 protocol
TODO: Cut in multiple subfiles to classify different actions
"""

import os
import sys
import time

import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import (
    QDialog, QMainWindow, QFileDialog, QProgressBar
)
import pyvista as pv
from scipy import stats

import CHUBACAPP.Biigle.utils as utils
import CHUBACAPP.blender.blender_reprojection as blender
import CHUBACAPP.preprocessing.Nav_file_manager as Nav_file_manager
import CHUBACAPP.preprocessing.blur_detection as blur
import CHUBACAPP.preprocessing.dim2_nav_filter as dim2_nav_filter
import CHUBACAPP.post_reprojection.annotations_filter_homogenize as post_reproj
import CHUBACAPP.annotation_geolocalisation.annotations_to_shp as shp
from CHUBACAPP.Biigle.choose_label import SelectWindow
from CHUBACAPP.blender.add_camera import AddCameraWindow
import CHUBACAPP.blender.camera_config as cc
from CHUBACAPP.main_window_ui import Ui_MainWindow
from CHUBACAPP.utils.coord_conversions import read_origin
from CHUBACAPP.utils.pyvista_utils import plot_obj_with_multiple_textures, add_annotations
import CHUBACAPP.post_reprojection.no_overlap as NO
from CHUBACAPP.DL import detect_yoloV5


class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        with open(r'UI/DarkOrange.qss', 'r', encoding='utf-8') as file:
            qss = file.read()
        self.setStyleSheet(qss)

        self.setWindowIcon(QtGui.QIcon('Logo-Ifremer.png'))

        # setting  the geometry of window
        self.setGeometry(100, 100, 1600, 1200)
        #self.showMaximized()

        self.connectActions()

        self.BiRe_LabAnn.addItems(["Annotations", "Labels"])
        self.BiRe_ExportType.addItems(["shp", "3Dmetrics"])
        self.reclass_cat.addItems(['Largo', 'Label'])
        cameras = cc.load_cameras()
        self.BiRe_cam_select.addItems(list(cameras.keys()))
        self.DIS_cam_select.addItems(list(cameras.keys()))
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)

        self.progress_bar = QProgressBar()
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

        self.api_volume = 54
        self.api_label_tree = 23

        self.window = 8
        self.alpha_val = [0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005, 0.002, 0.001, 0.0001, 0]

        self.conf_val = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
        self.confidence = 0.3

        self.api = 0

    def normalOutputWritten(self, text):
        """Append text to the QTextEdit."""
        debug_wins = [self.BiRe_Debug, self.RemBlu_Debug, self.PrePro_Debug, self.tools_debug, self.PR_debug, self.DIS_debug, self.TM_Debug]
        for output_win in debug_wins:
            cursor = output_win.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertText(text)
            output_win.setTextCursor(cursor)
            output_win.ensureCursorVisible()

    def connectActions(self):
        # Preprocessing
        self.PrePro_Input_S.clicked.connect(lambda: self.selectDir(self.PrePro_Input))
        self.PrePro_OutputPath_S.clicked.connect(lambda: self.selectDir(self.PrePro_OutputPath))
        self.TextRefPath_S.clicked.connect(lambda: self.selectFile(self.TextRefPath, "*.txt"))
        self.PrePro_sfm_data_B.clicked.connect(lambda: self.selectFile(self.PrePro_sfm_data, "sfm file (*.json *.bin)"))
        self.PrePro_mod_ori_B.clicked.connect(lambda: self.selectFile(self.PrePro_mod_ori, "*.txt"))
        self.PrePro_run.clicked.connect(self.preprocessing)

        # Remove blur
        self.RemBlu_Input_S.clicked.connect(lambda: self.selectDir(self.RemBlu_Input))
        self.RemBlu_Csv_S.clicked.connect(lambda: self.selectFile(self.RemBlu_Csv, "*.csv"))
        self.AlphaSlider.valueChanged.connect(self.blur_slider)
        self.RemBlu_Run.clicked.connect(self.blur_detect)
        self.RemBlu_Filter.clicked.connect(self.blur_filter)

        # Deep learning
        self.ConfidenceSlider.valueChanged.connect(self.confidence_slider)
        self.AD_model_B.clicked.connect(lambda: self.selectDir(self.AD_model))
        self.AD_Dir_B.clicked.connect(lambda: self.selectDir(self.AD_Dir))
        self.AD_run.clicked.connect(self.auto_detect)

        # Disjoint image selection
        self.DIS_sfm_path_B.clicked.connect(lambda: self.selectFile(self.DIS_sfm_path, "sfm file (*.json *.bin)"))
        self.DIS_model_B.clicked.connect(lambda: self.selectFile(self.DIS_model, "*.ply"))
        self.DIS_img_dir_B.clicked.connect(lambda: self.selectDir(self.DIS_img_dir))
        self.DIS_add_camera.clicked.connect(self.add_camera)
        self.DIS_run.clicked.connect(self.launch_dis)


        # Annotations2shp
        self.BiRe_2DInput_S.clicked.connect(lambda: self.selectDir(self.BiRe_2DInput))
        self.BiRe_Csv_S.clicked.connect(lambda: self.selectFile(self.BiRe_Csv, "*.csv"))
        self.BiRe_2DRun.clicked.connect(self.ann2shp)

        self.BiRe_Model_B.clicked.connect(lambda: self.selectFile(self.BiRe_Model, "*.ply"))
        self.BiRe_sfm_B.clicked.connect(lambda: self.selectFile(self.BiRe_sfm, "sfm file (*.json *.bin)"))
        self.BiRe_mod_ori_B.clicked.connect(lambda: self.selectFile(self.BiRe_mod_ori, "*.txt"))
        self.BiRe_video_path_B.clicked.connect(lambda: self.selectFile(self.BiRe_video_path, "video file (*.mp4 *.avi)"))
        self.BiRe_img_dir_B.clicked.connect(lambda: self.selectDir(self.BiRe_img_dir))
        self.BiRe_add_camera.clicked.connect(self.add_camera)

        self.BiRe_3DRun.clicked.connect(self.blender2shp)

        # topographic metrics
        self.TM_model_B.clicked.connect(lambda: self.selectFile(self.TM_model, "*.ply"))
        self.TM_output_B.clicked.connect(lambda: self.selectDir(self.TM_output))
        self.TM_run.clicked.connect(self.launch_tm)

        # Reclassifier
        self.Dir_b.clicked.connect(lambda: self.selectDir(self.Dir))
        self.Run_b.clicked.connect(self.start_class)
        self.connect.clicked.connect(self.on_connect)
        self.Origin.clicked.connect(lambda: self.select_label(self.Origin_txt))
        self.Lab1.clicked.connect(lambda: self.select_label(self.Lab1_txt))
        self.Lab2.clicked.connect(lambda: self.select_label(self.Lab2_txt))
        self.Lab3.clicked.connect(lambda: self.select_label(self.Lab3_txt))
        self.Lab4.clicked.connect(lambda: self.select_label(self.Lab4_txt))

        self.sel_lab1.clicked.connect(lambda: self.nextimage(self.sel_lab1))
        self.sel_lab2.clicked.connect(lambda: self.nextimage(self.sel_lab2))
        self.sel_lab3.clicked.connect(lambda: self.nextimage(self.sel_lab3))
        self.sel_lab4.clicked.connect(lambda: self.nextimage(self.sel_lab4))

        # Biigle DL
        self.connect_2.clicked.connect(self.on_connect)
        self.AD_model_B.clicked.connect(lambda: self.selectFile(self.AD_model, "*.pt"))
        self.AD_classes_B.clicked.connect(lambda: self.selectFile(self.AD_classes, "*.names"))
        self.AD_Dir_B.clicked.connect(lambda: self.selectDir(self.AD_Dir))
        self.AD_output_B.clicked.connect(lambda: self.selectDir(self.AD_output))
        self.AD_run.clicked.connect(self.launch_inference)


        # plot
        self.plot_model_path_B.clicked.connect(lambda: self.selectFile(self.plot_model_path, "model file (*.ply *.obj)"))
        self.plot_annotation_path_B.clicked.connect(lambda: self.selectFile(self.plot_annotation_path, "*.json"))
        self.plot_launch.clicked.connect(self.start_plot)
        self.plot_update_B.clicked.connect(self.update_plot)

        # post reprojection
        self.PR_input_B.clicked.connect(lambda: self.selectDir(self.PR_input))
        self.PR_output_B.clicked.connect(lambda: self.selectDir(self.PR_output))
        self.PR_data_config_B.clicked.connect(lambda: self.selectFile(self.PR_data_config, "*.csv"))

        self.PR_run.clicked.connect(self.post_proj_process)

        # Tools
        self.FN_Dir_B.clicked.connect(lambda: self.selectDir(self.FN_Dir))
        self.ImgList_Dir_B.clicked.connect(lambda: self.selectDir(self.ImgList_Dir))
        self.FN_Nav_B.clicked.connect(lambda: self.selectFile(self.FN_Nav, "*.dim2"))

        self.set_api_run.clicked.connect(self.set_api)
        self.FN_Run.clicked.connect(self.filter_nav)
        self.ImgList_Run.clicked.connect(self.image_list)

    def selectFile(self, line, fileType):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        file_path = QFileDialog.getOpenFileName(self, "Open file", "", fileType, options=options)
        if file_path[0] != "":
            line.setText(file_path[0])
            if line == self.RemBlu_Csv:
                self.enable_filtering(file_path[0])

    def selectDir(self, line):
        dir_path = QFileDialog.getExistingDirectory(None, 'Open Dir', r"")
        if dir_path:
            line.setText(dir_path)

    def set_api(self):
        if self.set_api_vol.text() == "" or self.set_api_LT.text() == "":
            print("Some required inputs missing")
            return 0
        else:
            self.api_volume = self.set_api_vol.text()
            self.api_label_tree = self.set_api_LT.text()
            print("Set API done !")

    def select_label(self, txt):
        sel = SelectWindow(self.labels)
        res = sel.exec_()
        if res == QDialog.Accepted:
            id, value = sel.get_value()
            txt.setText(str(id + "_" + str(value)))

    def add_camera(self):
        ac = AddCameraWindow()
        res = ac.exec_()
        if res == QDialog.Accepted:
            name, ocm, dist_coeff, res = ac.get_value()
            cameras = cc.load_cameras()
            cameras = cc.add_camera(cameras, name, ocm, dist_coeff, res)
            if cc.save_cameras(cameras):
                self.BiRe_cam_select.addItems(list(cameras.keys()))
                print("Successfully added camera !")

    def blur_slider(self):
        alpha = self.alpha_val[self.AlphaSlider.value()]
        self.blur_data["outlier"] = self.blur_data["delta"] > stats.t(df=self.window).ppf(1 - alpha) / np.sqrt(
            self.window)
        p = (self.blur_data["outlier"].values.sum() / len(self.blur_data)) * 100
        self.PercToRemoved.setText("{:.1f}".format(p) + " %")
        self.AlphaVal.setNum(alpha)

    def confidence_slider(self):
        self.confidence = self.conf_val[self.ConfidenceSlider.value()]
        self.Confidence_txt.setText("{:.2f}".format(self.confidence) + " %")

    def launch_dis(self):
        if self.DIS_sfm_path.text() == "" or self.DIS_model.text() == "" or self.DIS_img_dir.text() == "" or self.DIS_method.currentText() == "":
            print("Some required inputs missing")
            return 0
        else:
            self.progress_bar.show()
            sfm_path = self.DIS_sfm_path.text()
            model_path = self.DIS_model.text()
            camera_model = self.DIS_cam_select.currentText()
            img_path = self.DIS_img_dir.text()
            method = self.DIS_method.currentText()

            self.dis_thread = NO.DISThread(sfm_path, model_path, camera_model, img_path, method)
            self.dis_thread .prog_val.connect(self.setProgressVal)
            self.dis_thread .finished.connect(self.end_dis)
            self.dis_thread .start()
    def end_dis(self):
        self.progress_bar.hide()
        self.DIS_sfm_path.setText("")
        self.DIS_model.setText("")
        self.DIS_img_dir.setText("")
        print("Disjoint image selection done !")

    def launch_tm(self):
        if self.TM_output.text() == "" or self.TM_model.text() == "" or self.TM_scales.text() == "":
            print("Some required inputs missing")
            return 0
        else:
            self.progress_bar.show()
            model_path = self.TM_model.text()
            output_path = self.TM_output.text()
            scales = list(map(float, self.TM_scales.text().split(',')))
            metrics_cb = (self.TM_slope, self.TM_aspect, self.TM_roughness, self.TM_TRI, self.TM_BPI, self.TM_GM, self.TM_GC)
            metrics = [b.checkState() for b in metrics_cb]
            
            import CHUBACAPP.post_reprojection.topographic_metrics as tm

            self.tm_thread = tm.pcdGenThread(model_path, scales, output_path, metrics)
            self.tm_thread.prog_val.connect(self.setProgressVal)
            self.tm_thread.finished.connect(self.end_tm)
            self.tm_thread.start()

    def end_tm(self):
        self.progress_bar.hide()
        self.TM_model.setText("")
        self.TM_output.setText("")
        print("Topographic metrics computed !")


    def ann2shp(self):
        if self.BiRe_Csv.text() == "" or self.BiRe_2DInput.text() == "" or self.BiRe_ExpName.text() == "":
            print("Some required inputs missing")
            return 0
        else:
            data_path = self.BiRe_2DInput.text()
            annotations_path = self.BiRe_Csv.text()
            output_path_name = self.BiRe_ExpName.text()
            self.progress_bar.show()
            if self.BiRe_LabAnn.currentText() == "Annotations":
                self.AnnThread = shp.Ann_to_shpThread(data_path, annotations_path, output_path_name)
                self.AnnThread.prog_val.connect(self.setProgressVal)
                self.AnnThread.finished.connect(self.end_shp)
                self.AnnThread.start()
            elif self.BiRe_LabAnn.currentText() == "Labels":
                self.LabThread = shp.Lab_to_shpThread(data_path, annotations_path, output_path_name)
                self.LabThread.prog_val.connect(self.setProgressVal)
                self.LabThread.finished.connect(self.end_shp)
                self.LabThread.start()

    def end_shp(self):
        self.progress_bar.hide()
        self.BiRe_2DInput.setText("")
        self.BiRe_Csv.setText("")
        self.BiRe_ExpName.setText("Layers")
        print("Convert to shp done !")

    def blender2shp(self):
        if self.BiRe_Csv.text() == "" or self.BiRe_Model.text() == "" or self.BiRe_sfm.text() == "":
            print("Some required inputs missing")
            return 0
        else:
            model_path = self.BiRe_Model.text()
            sfm_path = self.BiRe_sfm.text()
            annotations_path = self.BiRe_Csv.text()
            export_type = self.BiRe_ExportType.currentText()
            model_origin_path = self.BiRe_mod_ori.text()
            origin_coords = None
            if os.path.exists(model_origin_path):
                origin_coords = read_origin(model_origin_path)
            label = (self.BiRe_LabAnn.currentText() == "Labels")
            camera = self.BiRe_cam_select.currentText()
            video = self.BiRe_video.checkState()
            video_path = None
            time_interval = None
            image_path = None
            if video:
                video_path = self.BiRe_video_path.text()
                time_interval = float(self.BiRe_time_inter.text())
                image_path = self.BiRe_img_dir.text()

            self.progress_bar.show()
            self.AnnThread = blender.annotationsTo3DThread(annotations_path, sfm_path, model_path, export_type, origin_coords, label,
                                                           camera, video, video_path, time_interval, image_path)
            self.AnnThread.prog_val.connect(self.setProgressVal)
            self.AnnThread.finished.connect(self.end_blend_shp)
            self.AnnThread.start()

    def end_blend_shp(self):
        self.progress_bar.hide()
        self.BiRe_Model.setText("")
        self.BiRe_Csv.setText("")
        self.BiRe_sfm.setText("")
        self.BiRe_video_path.setText("")
        self.BiRe_time_inter.setText("")
        self.BiRe_img_dir.setText("")
        print("Reprojection done !")

    def auto_detect(self):
        if self.AD_model.text() == "" or self.AD_Dir.text() == "":
            print("Some required inputs missing")
            return 0
        else:
            print("Not ready yet")

    def blur_detect(self):
        if self.RemBlu_Input.text() == "":
            print("Some required inputs missing")
            return 0
        else:
            images_path = self.RemBlu_Input.text()
            self.progress_bar.show()
            self.blur_thread = blur.BlurThread(images_path)
            self.blur_thread.prog_val.connect(self.setProgressVal)
            self.blur_thread.finished.connect(lambda: self.enable_filtering(images_path))
            self.blur_thread.start()

    def enable_filtering(self, data_path):
        self.progress_bar.hide()
        if os.path.isdir(data_path):
            csv_path = os.path.join(data_path, 'deblur.csv')
        else:
            csv_path = data_path
        try:
            self.blur_data = pd.read_csv(csv_path)
        except:
            print('Not a valid .csv file')
        self.AlphaSlider.setEnabled(True)
        self.RemBlu_Filter.setEnabled(True)
        self.RemBlu_Run.setDisabled(True)
        self.AlphaSlider.setValue(7)
        self.blur_slider()

    def blur_filter(self):
        if self.RemBlu_Input.text() == "":
            print("Some required inputs missing")
            return 0
        else:
            images_path = self.RemBlu_Input.text()
            self.progress_bar.show()
            self.blur_thread = blur.FilterThread(images_path, self.blur_data)
            self.blur_thread.prog_val.connect(self.setProgressVal)
            self.blur_thread.finished.connect(self.reset_filtering)
            self.blur_thread.start()

    def reset_filtering(self):
        self.progress_bar.hide()
        self.AlphaSlider.setDisabled(True)
        self.RemBlu_Filter.setDisabled(True)
        self.RemBlu_Run.setEnabled(True)
        print("Filtering done !")

    def filter_nav(self):
        if self.FN_Dir.text() == "" or self.FN_Nav.text() == "":
            print("Some required inputs missing")
            return 0
        else:
            data_path = self.FN_Dir.text()
            dim2_path = self.FN_Nav.text()
            self.progress_bar.show()
            self.filter_nav_thread = dim2_nav_filter.filter_navThread(data_path, dim2_path)
            self.filter_nav_thread.prog_val.connect(self.setProgressVal)
            self.filter_nav_thread.finished.connect(self.reset_blur_filter)
            self.filter_nav_thread.start()

    def reset_blur_filter(self):
        self.progress_bar.hide()
        self.FN_Nav.setText("")
        self.FN_Dir.setText("")
        print("dim2 Nav Filtering done !")

    def image_list(self):
        if self.ImgList_Dir.text() == "":
            print("Some required inputs missing")
            return 0
        else:
            Img_List_Dir = self.ImgList_Dir.text()
            img_list = utils.list_images(Img_List_Dir)
            textfile = open(os.path.join(Img_List_Dir, "img_list.txt"), "w")
            textfile.write(','.join(img_list))
            textfile.close()
            self.ImgList_Dir.setText("")
            print("Image list done !")

    def post_proj_process(self):
        if self.PR_input.text() == "" or self.PR_output.text() == "":
            print("Some required inputs missing")
            return 0
        elif (self.PR_homogenize.checkState() and self.PR_data_config.text() == ""):
            print("Some required inputs missing")
            return 0
        elif (not self.PR_homogenize.checkState() and not self.PR_filter.checkState()):
            print("No operations conducted. Please select at least one")
            return 0
        else:
            homogenize = self.PR_homogenize.checkState()
            filter = self.PR_filter.checkState()
            input_path = self.PR_input.text()
            output_path = self.PR_output.text()
            data_config_path = self.PR_data_config.text()
            self.progress_bar.show()
            self.PRThread = post_reproj.filter_homogenThread(input_path, output_path, data_config_path, filter,
                                                             homogenize)
            self.PRThread.prog_val.connect(self.setProgressVal)
            self.PRThread.finished.connect(self.end_PR)
            self.PRThread.start()

    def end_PR(self):
        print("Post reprojection done !")
        self.progress_bar.hide()
        self.PR_input.setText("")
        self.PR_output.setText("")
        self.PR_data_config.setText("")

    def preprocessing(self):
        if self.PrePro_Input.text() == "" or self.PrePro_OutputPath.text() == "" or self.NavName.text() == "":
            print("Some required inputs missing")
            return 0
        else:
            data_path = self.PrePro_Input.text()
            ref_nav_path = self.TextRefPath.text()
            output_path = self.PrePro_OutputPath.text()
            output_name = self.NavName.text()
            nav_correction = self.RawNav.checkState()
            optical = self.PrePro_optical.checkState()
            sfm_data_path = self.PrePro_sfm_data.text()
            model_origin_path = self.PrePro_mod_ori.text()
            copy = self.CopyImage.checkState()
            self.NavThread = Nav_file_manager.NavThread(data_path, output_path, output_name, nav_correction, optical,
                                                        ref_nav_path, sfm_data_path, model_origin_path, copy)
            self.NavThread.finished.connect(self.end_prepro)
            self.NavThread.start()

    def end_prepro(self):
        print("Preprocessing done !")
        self.PrePro_Input.setText("")
        self.TextRefPath.setText("")
        self.PrePro_OutputPath.setText("")

    def on_connect(self):
        if self.mail.text() != "" and self.credentials.text() != "":
            self.api = utils.connect(self.mail.text(), self.credentials.text())
        elif self.mail_2.text() != "" and self.credentials_2.text() != "":
            self.api = utils.connect(self.mail_2.text(), self.credentials_2.text())
        if self.api != 0:
            self.connect.setText("Connected")
            self.connect_2.setText("Connected")
            self.labels = self.api.get('label-trees/{}'.format(self.api_label_tree)).json()["labels"]
            self.Lab1.setEnabled(True)
            self.Lab2.setEnabled(True)
            self.Lab3.setEnabled(True)
            self.Lab4.setEnabled(True)
            self.Origin.setEnabled(True)

    def launch_inference(self):
        if self.AD_model.text() != "" and self.AD_Dir.text() != "":
            print("Missing inputs")
        else:
            model_path = self.AD_model.text()
            img_dir = self.AD_Dir.text()
            output_path = self.AD_output.text()
            classes_path = self.AD_classes.text()
            download = self.AD_download.checkState()
            exp_biigle = self.Exp_biigle.checkState()
            if exp_biigle:
                if self.api == 0:
                    print("Missing api...")
                    return 0
                else:
                    api = self.api
            else:
                api = None
                
            self.inferenceThread = detect_yoloV5.inferenceThread(model_path, img_dir, classes_path, output_path, download, api, self.confidence, self.api_label_tree, self.api_volume)
            
            


    def end_inference(self):
        self.progress_bar.hide()
        self.AD_model.setText("")

        print("Inference done !")


    def start_class(self):
        if self.Dir.text() == "" or self.Lab1_txt.text() == "" or self.Lab2_txt.text() == "" or self.connect.text() != "Connected":
            print("Missing inputs")
        else:
            self.dir_path = self.Dir.text()
            self.origin = self.Origin_txt.text()
            self.Label1 = self.Lab1_txt.text()
            self.Label2 = self.Lab2_txt.text()
            self.Label3 = self.Lab3_txt.text()
            self.Label4 = self.Lab4_txt.text()
            label = self.origin.split("_")[0]

            self.cat = self.reclass_cat.currentText()

            if self.download.checkState():
                if self.cat == "Largo":
                    if utils.download_largo(self.api, self.api_volume, label, self.dir_path) != 1:
                        print("error")
                        return 0
                if self.cat == 'Label':
                    if utils.download_image(self.api, self.api_volume, label, self.dir_path) != 1:
                        print("error")
                        return 0

            self.img_list = utils.list_images(self.dir_path)
            self.Remaining.setText(str(len(self.img_list)))
            self.timelist = []
            self.prev_timer = time.time()

            self.img_id = 0
            pixmap = QtGui.QPixmap(self.img_list[self.img_id])
            self.Image.setPixmap(pixmap)

            self.sel_lab1.setText(self.Label1)
            self.sel_lab2.setText(self.Label2)
            if self.Label3 == "":
                self.sel_lab3.hide()
                self.sel_lab3.setDisabled(True)
            else:
                self.sel_lab3.setText(self.Label3)

            if self.Label4 == "":
                self.sel_lab4.hide()
                self.sel_lab4.setDisabled(True)
            else:
                self.sel_lab4.setText(self.Label4)

    def nextimage(self, label):
        print("Saving Label:" + str(label.text()))
        annotation = os.path.basename(self.img_list[self.img_id])[:-4]
        utils.save_label(self.api, annotation, int(self.origin.split("_")[0]), int(label.text().split("_")[0]),
                         self.cat)
        os.remove(self.img_list[self.img_id])

        self.img_id += 1
        if len(self.img_list) > self.img_id:
            self.Remaining.setText(str(len(self.img_list) - self.img_id))
            self.DoneNb.setText(str(self.img_id))
            self.timelist.append(round((time.time() - self.prev_timer), 2))
            self.prev_timer = time.time()
            self.Speed.setText(str(round((sum(self.timelist) / len(self.timelist)) * len(self.img_list) / 60)))

            pixmap = QtGui.QPixmap(self.img_list[self.img_id])
            self.Image.setPixmap(pixmap)
        else:
            self.end_class()

    def end_class(self):
        print("Session over !")
        self.Origin_txt.setText("")
        self.Dir.setText("")
        self.Lab1_txt.setText("")
        self.Lab2_txt.setText("")
        self.Lab3_txt.setText("")
        self.Lab4_txt.setText("")

    def start_plot(self):
        if self.plot_model_path.text() == "":
            print("Some required inputs missing")
            return 0
        else:
            model_path = self.plot_model_path.text()
            json_path = self.plot_annotation_path.text()
            self.plotter = self.pv_plott
            pre = os.path.splitext(os.path.basename(model_path))[1]
            if pre == '.obj':
                plot_obj_with_multiple_textures(self.plotter, model_path)
            elif pre == '.ply':
                mesh = pv.read(model_path)
                self.plotter.add_mesh(mesh)
            self.ann_pv_obj, labels_name = add_annotations(self.plotter, json_path)
            self.plot_cb1.addItems(np.unique(np.array(labels_name)).tolist())
            self.plot_cb1.setEnabled(True)
            self.plot_update_B.setEnabled(True)
            self.plotter.reset_camera()

    def update_plot(self):
        for mesh in self.ann_pv_obj:
            self.plotter.remove_actor(mesh)
        json_path = self.plot_annotation_path.text()
        ann_filter = self.plot_cb1.currentText()

        add_annotations(self.plotter, json_path, ann_filter)
        self.plotter.reset_camera()

    def setProgressVal(self, val):
        self.progress_bar.setValue(val)

    def __del__(self):
        # Restore sys.stdout
        sys.stdout = sys.__stdout__


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
