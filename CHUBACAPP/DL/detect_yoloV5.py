import torch
import warnings
import os
from tqdm import tqdm
import imghdr
from PyQt5 import QtCore

from CHUBACAPP.DL.utils_pascalVOC import export_annotations_pascal, download_images
import CHUBACAPP.DL.export_to_biigle as export_to_biigle
warnings.filterwarnings("ignore")

class inferenceThread(QtCore.QThread):
    """Detects the blurry image and store their reference for later suppression"""
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, model, img_dir, classes, output, download, api, confidence, api_label_tree, api_volume):
        super(inferenceThread, self).__init__()
        self.running = True
        self.model = model
        self.img_dir = img_dir
        self.classes = classes
        self.output = output
        self.download = download
        self.confidence = confidence
        self.label_tree = api_label_tree
        self.volume = api_volume
        self.api = api
        if self.api is None:
            self.export_biigle = False
        else:
            self.export_biigle = True


    def run(self):
        print("Starting inference process...")
        if self.download:
            download_images(self.api, self.volume, self.output)

        model_inference(self.model, self.classes, self.output, self.export_biigle, self.api, self.confidence,
                        self.label_tree, self.volume)

        print("Done !")
        self.prog_val.emit(0)
        self.finished.emit()
        self.running = False

def model_inference(path_model, path_classes, output_path, export_biigle, api = None, confidence=0.25,
                    label_tree_id=None, volume_id=None):
    """
    Apply a trained neural network model (yoloV5) on provided images. Can export created annotations directly to biigle
    or to a pascalVOC file
    :param path_model: path to yolo v5 trained model. An example is accessible here
    :param path_classes: txt file of the different classes possible
    :param output_path: path to image to infer directory
    :param export_biigle: boolean, export to Biigle if true
    :param confidence: confidence level for detection
    :param label_tree_id: Biigle label tree id with the different classes from the classes.txt configuration file
    :param volume_id: Biigle volume id where images from output_path are
    """

    NMS_iou = 0.45
    shape = "Rectangle"  # Shape can be "Circle" or "Rectangle"

    model = torch.hub.load('ultralytics/yolov5', 'custom', path=path_model, device='cpu')  # Load the model

    model.conf = confidence
    model.iou = NMS_iou

    if export_biigle:
        label_idx = export_to_biigle.create_label_index(api, label_tree_id, path_classes)
        images_idx = export_to_biigle.create_image_index(api, volume_id)

    for image in tqdm(os.listdir(output_path)):  # for each image in the directory
        file_path = os.path.join(output_path, image)
        if os.path.isfile(file_path):  # Check if is image
            if imghdr.what(file_path) == "jpeg":  # Check image is jpeg image
                results = model(file_path)  # inference happens here

                annotations_xy = results.pandas().xyxy[0]  # Convert to panda table

                if len(annotations_xy) != 0:  # if features detected
                    height = results.ims[0].shape[0]
                    width = results.ims[0].shape[1]
                    # Save to pascalVOC file
                    pascalVOC_path = export_annotations_pascal(image, annotations_xy, width, height, output_path)

                    if export_biigle:
                        if label_tree_id is None or volume_id is None:
                            print("Error ! Missing argument...")
                        else:
                            export_to_biigle.pascalVOC_to_biigle(image, pascalVOC_path, label_idx, images_idx, shape,
                                                                 api)
