from tqdm import tqdm
import pandas as pd
from math import hypot

def export_annotations_image(file, annotations, shape, api, path_classes):
    label_tree_id = 27
    volume_id = 54

    shapes_id = {"Circle": 4,
                 "Rectangle": 5,
                 }

    # liste des images du volume biigle
    print("Getting images index from biigle")
    image_ids = api.get('volumes/{}/files'.format(volume_id)).json()
    biigle_images = []
    for image_id in tqdm(image_ids):
        image_info = api.get('images/{}'.format(image_id)).json()
        biigle_images.append([image_info["filename"], image_info['id']])
    biigle_images_df = pd.DataFrame(biigle_images, columns=['name', 'id'])

    with open(path_classes, 'r') as f:
        classes = f.read().splitlines()

    # label_index creator
    label_tree = api.get('label-trees/{}'.format(label_tree_id)).json()
    labels = label_tree['labels']
    label_id = []
    for i in classes:
        added = False
        for label in labels:
            if label['name'] == i:
                label_id.append([label['name'], label['id']])
                added = True
        if not added:
            print("Error: missing label in label tree !!")
            return 0

    image_id = int(biigle_images_df.loc[biigle_images_df['name'] == file]['id'])

    post_data = {
        'shape_id': shapes_id[shape],
        'label_id': 0,
        'confidence': 1,
        'points': [],
    }
    for index, row in annotations.iterrows():
        if shape == "Circle":
            width = row['xmax'] - row['xmin']
            height = row['ymax'] - row['ymin']
            x = row['xmin'] + (width /2)
            y = row['ymin'] + (height /2)
            points = [int(x), int(y), int(hypot(width, height) / 2)]
        elif shape == "Rectangle":
            points = [int(row["xmin"]), int(row["ymin"]), int(row["xmax"]), int(row["ymin"]), int(row["xmax"]), int(row["ymax"]), int(row["xmin"]), int(row["ymax"])]

        for label in label_id:
            if label[0] == row["name"]:
                post_data['label_id'] = label[1]
        post_data['points'] = points
        post_data['confidence'] = float(row["confidence"])
        p = api.post('images/{}/annotations'.format(image_id), json=post_data)
    return 1
