import os
import subprocess
import json
import pandas as pd


def sfm_data_handler(sfm_data_path, list_img):
    # Conversion from sfm_data.bin to sfm_data.json if not created. Long
    if os.path.basename(sfm_data_path)[:4] != "temp":
        if os.path.splitext(sfm_data_path)[1] == ".bin":
            print("Converting the sfm_data.bin to json...")
            # convert sfm_data.bin to json
            FNULL = open(os.devnull, 'w')  # use this if you want to suppress output to stdout from the subprocess
            sfm_dir = os.path.dirname(sfm_data_path)
            args = "utils/openMVG_main_ConvertSfM_DataFormat.exe -i \"" + os.path.join(sfm_dir,
                                                                                     "sfm_data.bin") + "\" -o \"" + os.path.join(
                sfm_dir, "sfm_data.json") + "\""
            subprocess.call(args, stdout=FNULL, stderr=FNULL, shell=False)
            sfm_data_path = os.path.join(os.path.dirname(sfm_data_path), "sfm_data.json")

        print("opening json...")
        with open(sfm_data_path, 'r') as f:
            data = json.load(f)
        print("Done")

        temp_views = []
        temp_poses = []
        for view in data['views']:
            if view['value']['ptr_wrapper']['data']['filename'] in list_img:
                temp_views.append(view)
                for pose in data['extrinsics']:
                    if pose['key'] == view['value']['ptr_wrapper']['data']['id_pose']:
                        temp_poses.append(pose)

        data['views'] = temp_views
        data['extrinsics'] = temp_poses
        data['structure'] = []

        temp_sfm_path = os.path.join(os.path.dirname(sfm_data_path), 'temp_sfm_data.json')
        out_file = open(temp_sfm_path, "w")
        json.dump(data, out_file, indent=4)
        out_file.close()

    else:
        print("Opening json...")
        with open(sfm_data_path, 'r') as f:
            data = json.load(f)
        temp_sfm_path = sfm_data_path
        print("Done !")

    return data, temp_sfm_path


def extract_camera_points(sfm_data):
    camera_points = pd.DataFrame({
        'filename': [],
        'pose_id': [],
        'width': [],
        'height': [],
        'rotation': [],
        'x': [],
        'y': [],
        'z': [],
    })
    for i in range(len(sfm_data['views'])):
        filename = sfm_data['views'][i]['value']['ptr_wrapper']['data']['filename']
        pose_id = sfm_data['views'][i]['value']['ptr_wrapper']['data']['id_pose']
        width = sfm_data['views'][i]['value']['ptr_wrapper']['data']['width']
        height = sfm_data['views'][i]['value']['ptr_wrapper']['data']['height']

        for j in range(len(sfm_data['extrinsics'])):
            if sfm_data['extrinsics'][j]['key'] == pose_id:
                rotation = sfm_data['extrinsics'][j]['value']['rotation']
                NL = pd.DataFrame({
                    'filename': [filename],
                    'pose_id': [pose_id],
                    'width': [width],
                    'height': [height],
                    'rotation': [rotation],
                    'x': [sfm_data['extrinsics'][j]['value']['center'][0]],
                    'y': [sfm_data['extrinsics'][j]['value']['center'][1]],
                    'z': [sfm_data['extrinsics'][j]['value']['center'][2]],
                })
                camera_points = pd.concat([camera_points, NL], ignore_index=True)
                break
    return camera_points
