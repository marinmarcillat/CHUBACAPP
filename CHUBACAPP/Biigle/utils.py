import shutil
import requests
import os
from PIL import Image
import io
from CHUBACAPP.Biigle.biigle import Api


def list_images(dir):
    img_list = []
    for file in os.listdir(dir):  # for each image in the directory
        file_path = os.path.join(dir, file)
        if os.path.isfile(file_path):  # Check if is file
            filename, file_extension = os.path.splitext(file_path)
            if file_extension == '.jpg':
                img_list.append(file_path)
    return img_list

def connect(mail, token):
    try:
        api = Api(mail, token)
        return api
    except:
        return 0

def save_label(api, annotation, old_label, new_label, cat):
    if cat == "Largo":
        ann = api.get('image-annotations/{}/labels'.format(annotation)).json()
        if old_label != new_label:
            if ann[0]['label']['id'] == old_label:
                p = api.post('image-annotations/{}/labels'.format(annotation),
                             json={'label_id': new_label, 'confidence': 1, })
                p = api.delete('image-annotation-labels/{}'.format(ann[0]['id']))
    if cat == 'Label':
        label = api.get('images/{}/labels'.format(annotation)).json()
        if old_label != new_label:
            for i in label:
                if i['label']['id'] == old_label:
                    p = api.post('images/{}/labels'.format(annotation),
                                 json={'label_id': new_label})
                    p = api.delete('image-labels/{}'.format(ann[i]['id']))
                    break


def download_largo(api, model, label, dir):
    endpoint_url = '{}s/{}/image-annotations/filter/label/{}'
    annotations = api.get(endpoint_url.format('volume', model, label)).json()

    patch_url = 'https://biigle.ifremer.fr/storage/largo-patches/{}/{}/{}/{}.jpg'

    for annotation_id, image_uuid in annotations.items():
        url = patch_url.format(image_uuid[:2], image_uuid[2:4], image_uuid, annotation_id)
        print('Fetching', url)
        patch = requests.get(url, stream=True)
        if patch.ok != True:
            raise Exception('Failed to fetch {}'.format(url))
        with open('{}/{}.jpg'.format(dir, annotation_id), 'wb') as f:
            patch.raw.decode_content = True
            shutil.copyfileobj(patch.raw, f)
    return 1

def download_image(api, volume, label, path):
    img_ids = api.get('volumes/{}/files/filter/labels/{}'.format(volume, label)).json()
    for i in img_ids:
        img = api.get('images/{}/file'.format(i))
        img_encoded = Image.open(io.BytesIO(img.content))
        out = img_encoded.resize((600, 400))
        out.save(os.path.join(path, str(i) + ".jpg"))
    return 1









