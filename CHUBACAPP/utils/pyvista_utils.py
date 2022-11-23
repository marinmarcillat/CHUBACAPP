import pyvista as pv
import os
import numpy as np
import json
import random


def plot_obj_with_multiple_textures(plotter, obj_path):
    obj_mesh = pv.read(obj_path)
    texture_dir = os.path.dirname(obj_path)

    pre = os.path.splitext(os.path.basename(obj_path))[0]

    mtl_path = os.path.join(texture_dir, pre + ".mtl")

    texture_paths = []
    mtl_names = []

    # parse the mtl file
    with open(mtl_path) as mtl_file:
        for line in mtl_file.readlines():
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            if parts[0] == 'map_Kd':
                texture_paths.append(os.path.join(texture_dir, parts[1]))
            elif parts[0] == 'newmtl':
                mtl_names.append(parts[1])

    material_ids = obj_mesh.cell_arrays['MaterialIds']

    # This one do.
    for i in np.unique(material_ids):
        mesh_part = obj_mesh.extract_cells(material_ids == i)
        mesh_part.textures[mtl_names[i]] = pv.read_texture(texture_paths[i])
        plotter.add_mesh(mesh_part)


def points_to_mesh(points):
    """
    Construct a mesh surface from polygons point using Delaunay triangulation
    :param points: polygons points
    :return: pyvista 3D mesh
    """

    polygons_pts = pv.PolyData(points)  # Convert to pyvista format
    mesh = polygons_pts.delaunay_2d(offset=0.5,
                                    edge_source=pv.lines_from_points(points, close=True))  # Delaunay triangulation
    return mesh


def parse_annotation(json_path):
    """
    Parse json annotations from 3D metric
    :param json_path: path to json path
    :return: list of annotations (key, points)
    """
    with open(json_path) as json_file:
        data = json.load(json_file)

    annotations = []
    for plg in data['Data']:
        for sub in plg:
            sub_key = list(sub.keys())[0]
            try:
                pts = sub[sub_key]["pts"]
                plg_pts_list = []
                for pt in pts:
                    x = pt['x']
                    y = pt['y']
                    z = pt['z']
                    plg_pts_list.append([x, y, z])
                np_plg_pts = np.array(plg_pts_list)
                try:
                    name = plg[0]['LabelName']
                except:
                    name = sub_key
                annotations.append([name, np_plg_pts])
            except:
                try:  # if is a point
                    pt = sub[sub_key]
                    x = pt['x']
                    y = pt['y']
                    z = pt['z']
                    try:
                        name = plg[0]['LabelName']
                    except:
                        name = sub_key
                    annotations.append([name, np.array([[x, y, z]])])
                except:
                    pass

    return annotations

def color_dict(d, name):
    if name in d.keys():
        color = d[name]
        return d, color
    else:
        r = lambda: random.randint(0, 255)
        color = '#%02X%02X%02X' % (r(), r(), r())
        d[name] = color
        return d, color

def add_annotations(plotter, json_path, filter=None):
    annotations = parse_annotation(json_path)
    labels_name = []
    ann_pv_obj = []
    colors = dict()
    for annotation in annotations:

        if filter is not None:
            if annotation[0] != filter:
                continue

        if len(annotation[1]) != 1:
            mesh = points_to_mesh(annotation[1])
        else:
            mesh = pv.Sphere(0.1, annotation[1][0].tolist())
        colors, color = color_dict(colors, annotation[0])
        p = plotter.add_mesh(mesh, color)
        ann_pv_obj.append(p)
        labels_name.append(annotation[0])
    return ann_pv_obj, labels_name
