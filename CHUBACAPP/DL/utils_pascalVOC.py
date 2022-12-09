# -*- coding: utf-8 -*-
from CHUBACAPP.utils.pascalVOC_writer import Writer
import xml.etree.ElementTree as ET
from PIL import Image
import pandas as pd
import os, io

def read_pascalVOC_content(xml_file: str):
    """
    Read a pascalVOC xml file and return a pandas table with annotations
    :param xml_file: path to an xml pascalVOC file
    :return:
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    list_with_all_boxes = []

    for boxes in root.iter('object'):

        filename = root.find('filename').text

        ymin, xmin, ymax, xmax = None, None, None, None

        ymin = float(boxes.find("bndbox/ymin").text)
        xmin = float(boxes.find("bndbox/xmin").text)
        ymax = float(boxes.find("bndbox/ymax").text)
        xmax = float(boxes.find("bndbox/xmax").text)
        confidence = float(boxes.find("difficult").text)
        name = boxes.find("name").text

        list_with_single_boxes = [xmin, ymin, xmax, ymax, confidence, name]
        list_with_all_boxes.append(list_with_single_boxes)

    annotations = pd.DataFrame(list_with_all_boxes, columns=['xmin', 'ymin', 'xmax', 'ymax', 'confidence', 'name'])

    return annotations


def export_annotations_pascal(image_name, annotations, width, height, output_path):
    """
    Export an annotation pandas table to a xml pascalVOC file
    :param image_name: image name (with suffix .jpg or .png)
    :param annotations: annotations pandas table
    :param width: image width
    :param height: image height
    :param output_path: export directory path
    :return:
    """
    writer = Writer(image_name, width, height)
    xml = os.path.splitext(image_name)[0] + '.xml'
    output_path = os.path.join(output_path, xml)
    for index, row in annotations.iterrows():
        writer.addObject(row["name"], row["xmin"], row["ymin"], row["xmax"], row["ymax"], difficult = row["confidence"])
        writer.save(output_path)
    return output_path


def download_images(api, volume, output_path):
    """
    Download all images from a volume into the output_path
    :param api: biigle api object
    :param volume: biigle volume
    :param output_path: output directory path
    :return:
    """
    img_ids = api.get('volumes/{}/files'.format(volume)).json()
    for i in img_ids:
        img = api.get('images/{}/file'.format(i))
        img_info = api.get('images/{}'.format(i)).json()
        img_name = img_info["filename"]
        img_encoded = Image.open(io.BytesIO(img.content))
        img_encoded.save(os.path.join(output_path, str(img_name)))
    return 1
