import numpy as np
import pandas as pd
import os, imghdr
import ast
import cv2


def find_first(video_path, image_path):
    vidcap = cv2.VideoCapture(video_path)

    image = cv2.imread(image_path, 0)
    sim_list = []
    for i in range(20):
        success, frame = vidcap.read()
        if not success: break

        # Initiate SIFT detector
        sift = cv2.SIFT_create()
        # find the keypoints and descriptors with SIFT
        kp1, des1 = sift.detectAndCompute(frame, None)
        kp2, des2 = sift.detectAndCompute(image, None)
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des1, des2, k=2)
        # store all the good matches as per Lowe's ratio test.
        good = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good.append(m)

        if len(good) > 10:
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        similarity = np.sum(np.concatenate(np.abs(np.eye(3) - M)))
        timestamp = vidcap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        sim_list.append([timestamp, similarity])

    df = pd.DataFrame(sim_list, columns=['timestamp', 'similarity'])

    return df.loc[df['similarity'].idxmin()]

def get_img_list(img_path):
    img_list = []
    for file in sorted(os.listdir(img_path)):
        jpg_path = os.path.join(img_path, file)
        if os.path.isfile(jpg_path) and imghdr.what(jpg_path) == "jpeg":
            img_list.append(file)
    return img_list


def get_annotations_tracks(annotation_path, img_path, video_path, time_interval):
    annotations = pd.read_csv(annotation_path, sep=",", )

    img_list = get_img_list(img_path)

    img_df = pd.DataFrame(img_list, columns=['filename'])

    first_frame = find_first(video_path, os.path.join(img_path, img_list[0]))
    img_df['timestamp'] = [first_frame['timestamp'] + (i * time_interval) for i in range(len(img_df))]

    # prepare all tracks for reprojection
    ann_tracks = pd.DataFrame(
        columns=['timestamp', 'points', 'filename', 'shape_name', 'label_name', 'label_hierarchy', 'annotation_id'])
    for index, row in annotations.iterrows():
        tracking = pd.DataFrame({'timestamp': ast.literal_eval(row['frames'].replace('null', "'NaN'")),
                                 'points': ast.literal_eval(row['points'].replace('null', "'NaN'"))}).astype(
            {"timestamp": float}).dropna()
        tracking = pd.merge_asof(tracking, img_df, on='timestamp', direction='nearest', tolerance=0.1).dropna()
        tracking['shape_name'], tracking['label_name'], tracking['label_hierarchy'], tracking['annotation_id'] = [
            row['shape_name'], row['label_name'], row['label_hierarchy'], row['video_annotation_label_id']]
        ann_tracks = pd.concat([ann_tracks, tracking], ignore_index=True)

    return ann_tracks, img_df
