# -*- coding: utf-8 -*-
from pascal_voc_writer import Writer
import os

def export_annotations_pascal(file, annotations, width, height, data_path):
    
    writer = Writer(file, width, height)

    for index, row in annotations.iterrows():
        writer.addObject(row["name"], row["xmin"], row["ymin"], row["xmax"], row["ymax"])
        
        xml = os.path.splitext(file)[0]+'.xml'
        writer.save(os.path.join(data_path, xml))
