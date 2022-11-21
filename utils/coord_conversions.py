from scipy.spatial.distance import euclidean
from geopy.distance import distance
import pandas as pd
import numpy as np


def dist_ref(x, y, x_ref, y_ref):
    # Euclidean distance to a reference position
    return euclidean((x, y), (x_ref, y_ref))


def annotation2hitpoint(ann_coords, hit_points, mapx, mapy, x_original_center, scale_x_sfm, x_sfm_center, y_original_center, scale_y_sfm, y_sfm_center):
    (x,y) = ann_coords
    # Undistort coordinates
    und_x, und_y = (mapx[round(y), round(x)], mapy[round(y), round(x)])

    # resize from original image size to openMVG image size
    x_scaled = round((und_x - x_original_center) * scale_x_sfm + x_sfm_center)
    y_scaled = round((und_y - y_original_center) * scale_y_sfm + y_sfm_center)

    # Get the location of the intersection between ray and target
    if 0 <= x_scaled < len(hit_points) and 0 <= y_scaled < len(hit_points[0]):
        coord = hit_points[x_scaled][y_scaled]
        return coord
    else:
        return None


def local_2_lat_long(model_origin, coords):
    inter_point = distance(meters=coords[0]).destination(model_origin, bearing=0)
    final_point = distance(meters=coords[1]).destination(inter_point, bearing=90)
    z = abs(model_origin[2]) + abs(coords[2])
    return final_point.latitude, final_point.longitude, z


def local_2_position2d(local, model_origin):
    positions = []
    for index, point in local.iterrows():
        coord = list(point[['x', 'y', 'z']])
        position = local_2_lat_long(model_origin, coord)
        positions.append(position)
    position2d = pd.DataFrame(positions, columns=['lat', 'long', 'z'])
    return position2d


def lat_long_2_local(coords, model_origin):
    offset_z = abs(model_origin[2]) - abs(coords[2])
    offset_x = distance((coords[0], model_origin[1]), (coords[0], coords[1])).m
    if coords[1] < model_origin[1]:
        offset_x = -offset_x
    offset_y = distance((model_origin[0], coords[1]), (coords[0], coords[1])).m
    if coords[0] < model_origin[0]:
        offset_y = -offset_y
    offset = [offset_x, offset_y, offset_z]
    return offset


def position2d_2_local(position2d, model_origin):
    offsets = []
    for index, point in position2d.iterrows():
        coords = list(point[['lat', 'long', 'z']])
        offset = lat_long_2_local(coords, model_origin)
        offsets.append(offset)
    offsets_df = pd.DataFrame(offsets, columns=['x', 'y', 'z_off'])
    return offsets_df

def convert_all_to_lat_long(origin_coords, point, line, polygon):
    for figure in [polygon, line]:
        for i in range(len(figure)):
            p = figure[i]
            if len(p[0]) >= 3:
                coords_local = np.array(p[0])[:, 0:3]
                nested_global = np.copy(coords_local)
                for j in range(len(coords_local)):
                    c = coords_local[j]
                    lat, long, z = local_2_lat_long(origin_coords, c)
                    nested_global[j] = [lat, long, -z]
                nested_global_list = nested_global.tolist()
                figure[i][0] = nested_global_list

    for i in range(len(point)):
        p = point[i]
        lat, long, z = local_2_lat_long(origin_coords, p[0][:3])
        point[i][0] = [lat,long,z]

    return point, line, polygon

def read_origin(origin_path):
    with open(origin_path) as f:
        coords_literal = f.readlines()
    coords = coords_literal[0].split(";")
    coords = [float(c)for c in coords]

    return coords

