import os

import geopandas
import pandas as pd
import shapely
from PyQt5 import QtCore
from shapely.geometry.base import geom_factory

'''
Provides functions to homogenize and filter annotations after reprojection on 3D model

'''


class filter_homogenThread(QtCore.QThread):
    '''Does the work'''
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, input_path, output_path, data_types_config_path, f, h):
        super(filter_homogenThread, self).__init__()
        self.running = True
        self.input_path = input_path
        self.output_path = output_path
        self.data_types_config_path = data_types_config_path
        self.f = f  # filter ?
        self.h = h  # homogenise ?

    def run(self):
        '''This starts the thread on the start() call'''
        unic_poly = None  # unic_poly is the union polygon of all images imprints on the 3D model

        poly_path = os.path.join(self.input_path, "polygon.shp")
        point_path = os.path.join(self.input_path, "point.shp")

        polygons = geopandas.read_file(poly_path)
        points = geopandas.read_file(point_path)

        if self.f:
            points, polygons, unic_poly = filter_overlap(points, polygons, self)
        if self.h:
            points, polygons = homogenize(points, polygons, self.data_types_config_path, self)

        save_all(points, polygons, self.output_path, unic_poly)
        self.prog_val.emit(0)
        self.finished.emit()
        self.running = False


def recursiv(data_config, l):
    """
    Small function to retrieve all subclasses recursively
    """
    end_list = []
    for i in l:
        s = data_config.loc[data_config['classes'] == i]
        if len(s) != 0:
            if isinstance(s['subclasses'].iloc[0], str):
                s_l = s['subclasses'].iloc[0].split("/")
                if len(s_l) != 0:
                    r_s = recursiv(data_config, s_l)
                    end_list.extend(r_s)
        end_list.append(i)
    return end_list


def make_valid(ob):
    if ob.is_valid:
        return ob
    return ob.buffer(0)


def filter_overlap(points, gdf, thread=None):
    """
    Filter annotations to avoid redundancy due to image overlap
    Points are filtered using image imprints (bounds) on the 3D model
    """
    bounds = gdf[gdf['label_name'] == 'bound'] # get the bounds of each image on the 3D model
    ann_poly = gdf[gdf['label_name'] != 'bound']

    first_poly = True
    first_point = True
    tot_len = len(bounds)
    prog = 0
    for index, bound in bounds.iterrows():
        if thread is not None:
            thread.prog_val.emit((prog / tot_len) * 100)
        prog += 1
        s = str(round((prog / tot_len) * 100)) + " %, " + str(prog) + " / " + str(tot_len)
        print(s, end="\r")

        bound = geopandas.GeoDataFrame(bound.to_frame().transpose())
        if first_poly:
            unic_poly = bound
            first_poly = False
        else:
            if unic_poly['geometry'].intersects(bound.iloc[0].squeeze()['geometry']).any():
                new_polygon = bound.iloc[0].squeeze()['geometry']
                intersect = unic_poly['geometry'].intersection(new_polygon)
                for overlap in intersect:
                    new_polygon = new_polygon.difference(overlap)
                if new_polygon.geom_type == "GeometryCollection":
                    poly_list = []
                    for feature in new_polygon:
                        if isinstance(feature, shapely.geometry.polygon.Polygon):
                            poly_list.append(feature)
                    new_polygon = shapely.geometry.MultiPolygon(poly_list)

                if not new_polygon.is_empty:
                    corr_polygon = make_valid(new_polygon)
                    bound['geometry'] = corr_polygon
                    unic_poly = pd.concat([unic_poly, bound], ignore_index=True)

            else:
                corr_polygon = make_valid(bound.iloc[0]['geometry'])
                bound['geometry'] = corr_polygon
                unic_poly = pd.concat([unic_poly, bound], ignore_index=True)

        if not bound.geometry.is_empty.iloc[0]:
            bound.set_crs(epsg=4326, inplace=True)
            points_inside = points[points['filename'].isin(bound['filename'])]
            points_inside = geopandas.sjoin(points_inside, bound, how='inner').iloc[:, :8]
            points_inside.columns = ['id', 'z', 'radius', 'label_name', 'label_hier', 'filename', 'annotation',
                                     'geometry']

            if first_point:
                global_points = points_inside
                first_point = False
            else:
                points_inside.columns = global_points.columns
                global_points = pd.concat([global_points, points_inside], ignore_index=True)

    for index, row in ann_poly.iterrows(): # Looping over all polygons
        if row['geometry'].is_valid:
            next
        else:
            ann_poly.loc[[index], 'geometry'] = ann_poly.loc[[index], 'geometry'].buffer(0)
    grouped_polygons = ann_poly.reset_index().dissolve(by='label_name')
    grouped_polygons = grouped_polygons.reset_index().explode().drop(['index'], axis=1)
    global_polygons = grouped_polygons[['id', 'z', 'label_name', 'label_hier', 'filename', 'annotation', 'geometry']]
    global_polygons['id'] = range(len(global_polygons))
    global_polygons.index = range(len(global_polygons))

    global_points = global_points[
        ['id', 'z', 'radius', 'label_name', 'label_hier', 'filename', 'annotation', 'geometry']]
    global_points['id'] = range(len(global_points))
    global_points.index = range(len(global_points))

    return global_points, global_polygons, unic_poly


def homogenize(points, polygons, data_types_config_path, thread=None):
    """
    Homogenize annotations using data_types_config file
    Annotations will be corrected to the right shape (point or polygon), and grouped in label classes
    """
    data_config = pd.read_csv(data_types_config_path, sep=';')

    processed_points = []
    first_pt = True
    processed_polygons = []
    first_poly = True
    tot_len = len(data_config)
    prog = 0
    for index, row in data_config.iterrows():
        if thread is not None:
            thread.prog_val.emit((prog / tot_len) * 100)
        prog += 1
        s = str(round((prog / tot_len) * 100)) + " %, " + str(prog) + " / " + str(tot_len)
        print(s, end="\r")

        c = row['classes']
        str_s_c = row['subclasses']
        all_s_c = [c]
        if isinstance(str_s_c, str):
            s_c = str_s_c.split("/")
            all_s_c.extend(recursiv(data_config, s_c))
        shape = row['shape']

        c_list = []
        for s_c in all_s_c:
            if shape == 'Point':
                original_ann = points[points['label_name'] == s_c]
                c_list.append(original_ann)
                to_convert = polygons[polygons['label_name'] == s_c]
                if len(to_convert) != 0:
                    to_convert['geometry'] = to_convert['geometry'].centroid
                    c_list.append(to_convert)
            elif shape == 'Polygon':
                original_ann = polygons[polygons['label_name'] == s_c]
                c_list.append(original_ann)
                to_convert = points[points['label_name'] == s_c]
                if len(to_convert) != 0:
                    to_convert['geometry'] = to_convert['geometry'].buffer(to_convert['radius'])
                    c_list.append(to_convert)

        combined = c_list[0]
        for i in range(1, len(c_list)):
            combined = pd.concat([combined, c_list[i]], ignore_index=True)

        combined['label_name'] = c
        combined['label_hier'] = str_s_c

        if shape == 'Point':
            if first_pt:
                processed_points = combined
                first_pt = False
            else:
                processed_points = pd.concat([processed_points, combined], ignore_index=True)
        elif shape == 'Polygon':
            if first_poly:
                processed_polygons = combined
                first_poly = False
            else:
                processed_polygons = pd.concat([processed_polygons, combined], ignore_index=True)
    return processed_points, processed_polygons


def save_all(points, polygons, output_path, unic_poly=None):
    """
    Save all annotations (and eventually images imprints) in shp files
    """
    output_bound_path = os.path.join(output_path, "export_bound.shp")
    output_point_path = os.path.join(output_path, "export_point.shp")
    output_poly_path = os.path.join(output_path, "export_poly.shp")

    points.to_file(output_point_path)
    polygons.to_file(output_poly_path)

    if unic_poly is not None:
        unic_poly.to_file(output_bound_path)


if __name__ == "__main__":
    input_path = r"F:\OTUS 2018\WC_complet\processed_images\outReconstruction\Layer_image_polygons"
    output_path = r"F:\OTUS 2018\WC_complet\processed_images\outReconstruction\Layer_image_polygons\output"

    data_types_config_path = r"F:\OTUS 2018\Data_annotations\Homogenize.csv"

    poly_path = os.path.join(input_path, "polygon.shp")
    point_path = os.path.join(input_path, "point.shp")

    polygons = geopandas.read_file(poly_path)
    points = geopandas.read_file(point_path)

    points, polygons, unic_poly = filter_overlap(points, polygons)
    points, polygons = homogenize(points, polygons, data_types_config_path)

    save_all(points, polygons, output_path, unic_poly)
