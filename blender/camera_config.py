import json

json_path = r'blender/cameras.json'

def add_camera(data, name, ocm, dist_coeff, res):
    data[name] = {
        'optical_camera_matrix': ocm,
        'dist_coeff': dist_coeff,
        'resolution': res,
    }
    return data
def save_cameras(data):
    with open(json_path, 'w') as fp:
        json.dump(data, fp)
    return 1

def load_cameras():
    with open(json_path, 'r') as fp:
        data = json.load(fp)
    return data
