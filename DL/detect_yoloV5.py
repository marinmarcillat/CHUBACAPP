import torch
import warnings
import os
from tqdm import tqdm
import imghdr
warnings.filterwarnings("ignore")

def model_inference(path_model, path_data, export_biigle, export_pascal, api, confidence = 0.25):
    NMS_confidence = confidence
    NMS_iou = 0.45
    shape = "Circle"

    path_classes = r"classes.txt"

    if export_biigle:
        from DL.export_to_biigle import export_annotations_image

    if export_pascal:
        from DL.export_to_pascal_VOC import export_annotations_pascal

    model = torch.hub.load('yolov5', 'custom', source='local', path = path_model, device = 'cpu')

    model.conf = NMS_confidence
    model.iou = NMS_iou

    for file in tqdm(os.listdir(path_data)):  # for each image in the directory
        file_path = os.path.join(path_data, file)
        if os.path.isfile(file_path):  # Check if is file
            if imghdr.what(file_path) == "jpeg":  # Check file is jpeg image
                results = model(file_path)

                #results.show()

                annotations_xy = results.pandas().xyxy[0]

                if export_biigle:
                    export_annotations_image(file, annotations_xy, shape, api, path_classes)

                if export_pascal:
                    height = len(results.pandas().imgs[0])
                    width = len(results.pandas().imgs[0][0])
                    export_annotations_pascal(file, annotations_xy, width, height, path_data)
