from CHUBACAPP.utils.pascalVOC_writer import Writer
import pandas as pd
import ast
from tqdm import tqdm
import os
import imghdr


data_path = r"C:\Users\mmarcill\Desktop\test_image_deep_learning"
path_rapport = r"C:\Users\mmarcill\Desktop\pl03.csv"

list_label = ["brachyura", "caridea", "galatheoidea", "actinaria", "bamboo", "dandelion"]

#data_path = os.path.join(os.getcwd(), "{}".format(path_image))

rapport = pd.read_csv(path_rapport, sep=',')

for file in tqdm(os.listdir(data_path)):  # for each image in the directory
    if os.path.isfile(os.path.join(data_path, file)):  # Check if is file
        if imghdr.what(os.path.join(data_path, file)) == "jpeg":  # Check file is jpeg image
            img_ann = rapport.loc[rapport['filename'] == file]
            if not img_ann.empty:
                row = img_ann.iloc[0]
                width = ast.literal_eval(row["attributes"])["width"]
                height = ast.literal_eval(row["attributes"])["height"]
                start = True
                for index, row in img_ann.iterrows():
                    shape = row["shape_name"]
                    coord = ast.literal_eval(row["points"])
                    label = row["label_name"]
                    # xmin, ymin, xmax, ymax
                    if label in list_label and shape == "Circle":
                        if start:
                            writer = Writer(file, width, height)
                            start = False
                        x_min = max(0, int(coord[0] - coord[2]))
                        y_min = max(0, int(coord[1] - coord[2]))
                        x_max = min(width, int(coord[0] + coord[2]))
                        y_max = min(height, int(coord[1] + coord[2]))
                        writer.addObject(label, x_min, y_min, x_max, y_max)
                xml = os.path.splitext(file)[0]+'.xml'
                writer.save(os.path.join(data_path, xml))




