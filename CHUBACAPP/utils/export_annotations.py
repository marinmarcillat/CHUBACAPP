import json, os
import fiona
import numpy as np
from fiona.crs import from_epsg
from shapely.geometry import Point, Polygon, LineString, mapping
import CHUBACAPP.utils.coord_conversions as coord_conv


def exp_3dmetrics(output_point_path, output_poly_path, point, polygon, coords_origin):
    # Export to 3Dmetrics Json measurement file
    export_point = {
        "Data": [],
        "Fields": [
            {
                "Name": "LabelName",
                "Type": "Text"
            },
            {
                "Name": "LabelHierarchy",
                "Type": "Text"
            },
            {
                "Name": "Filename",
                "Type": "Text"
            },
            {
                "Name": "AnnotationId",
                "Type": "Text"
            },
            {
                "Name": "coord",
                "Type": "Point"
            }
        ],
        "Measurement pattern": "3DMetrics",
        "Reference": {
            "altitude": 0,
            "latitude": 0,
            "longitude": 0,
        }
    }

    export_polygon = {
        "Data": [],
        "Fields": [
            {
                "Name": "LabelName",
                "Type": "Text"
            },
            {
                "Name": "LabelHierarchy",
                "Type": "Text"
            },
            {
                "Name": "Filename",
                "Type": "Text"
            },
            {
                "Name": "AnnotationId",
                "Type": "Text"
            },
            {
                "Name": "Area",
                "Type": "Area"
            }
        ],
        "Measurement pattern": "3DMetrics",
        "Reference": {
            "altitude": 0,
            "latitude": 0,
            "longitude": 0,
        }
    }

    if coords_origin is not None:
        for d in [export_point, export_polygon]:
            d['Reference']['altitude'] = coords_origin[2]
            d['Reference']['latitude'] = coords_origin[0]
            d['Reference']['longitude'] = coords_origin[1]

    for i in point:
        coord = i[0]
        pts = {
            "x": coord[0],
            "y": coord[1],
            "z": coord[2],
        }
        pts_ann = [{"LabelName": str(i[1])},
                   {"LabelHierarchy": str(i[2])},
                   {"Filename": str(i[3])},
                   {"AnnotationId": str(i[4])},
                   {"coord": pts, }]
        export_point["Data"].append(pts_ann)

    for i in polygon:
        coords = i[0]
        pts = []
        for coord in coords:
            pts.append({
                "x": coord[0],
                "y": coord[1],
                "z": coord[2],
            })
        Area = {
            "area": 0,
            "Length": 0,
            "pts": pts,
        }
        pts_ann = [{"LabelName": str(i[1])},
                   {"LabelHierarchy": str(i[2])},
                   {"Filename": str(i[3])},
                   {"AnnotationId": str(i[4])},
                   {"Area": Area, }]
        export_polygon["Data"].append(pts_ann)

    out_file = open(output_point_path, "w")
    json.dump(export_point, out_file, indent=4)
    out_file.close()

    out_file = open(output_poly_path, "w")
    json.dump(export_polygon, out_file, indent=4)
    out_file.close()


def exp_shp(output_path, point, line, polygon, coords_origin):
    # Export in a shp file for GIS analysis. We lost a part of the z information for polygons
    schema_polygon = {
        'geometry': 'Polygon',
        'properties': {
            'id': 'int',
            'z': 'float',
            'label_name': 'str',
            'label_hierarchy': 'str',
            'filename': 'str',
            'annotation_id_biigle': 'int'
        }
    }

    schema_point = {
        'geometry': 'Point',
        'properties': {
            'id': 'int',
            'z': 'float',
            'radius': 'float',
            'label_name': 'str',
            'label_hierarchy': 'str',
            'filename': 'str',
            'annotation_id_biigle': 'int'
        }
    }

    schema_LineString = {
        'geometry': 'LineString',
        'properties': {
            'id': 'int',
            'z': 'float',
            'label_name': 'str',
            'label_hierarchy': 'str',
            'filename': 'str',
            'annotation_id_biigle': 'int'
        }
    }

    if coords_origin is not None:
        point, line, polygon = coord_conv.convert_all_to_lat_long(coords_origin, point, line, polygon)

    id_img = 0
    id_poly = 1
    id_point = 1
    id_line = 1
    # write your shapefile, as projection of epsg: 4326
    output_path = os.path.join(output_path, '3DLayer')
    isExist = os.path.exists(output_path)
    if not isExist:
        os.makedirs(output_path)

    with fiona.open(output_path, 'w', 'ESRI Shapefile', layer='polygon', schema=schema_polygon,
                    crs=from_epsg(4326)) as out:
        for p in polygon:
            if len(p[0]) >= 3:
                polygon_geom = Polygon(np.array(p[0])[:, 0:2])
                out.write({
                    'geometry': mapping(polygon_geom),
                    'properties': {
                        'id': id_poly,
                        'z': np.array(p[0])[:, 2].mean(),
                        'label_name': p[1],
                        'label_hierarchy': p[2],
                        'filename': p[3],
                        'annotation_id_biigle': p[4],
                    }
                })
                id_poly += 1

    with fiona.open(output_path, 'w', 'ESRI Shapefile', layer='point', schema=schema_point,
                    crs=from_epsg(4326)) as out:
        for p in point:
            point_geom = Point(p[0][:2])
            out.write({
                'geometry': mapping(point_geom),
                'properties': {
                    'id': id_point,
                    'z': p[0][2],
                    'radius': p[5],
                    'label_name': p[1],
                    'label_hierarchy': p[2],
                    'filename': p[3],
                    'annotation_id_biigle': p[4],
                }
            })
            id_point += 1

    with fiona.open(output_path, 'w', 'ESRI Shapefile', layer='line', schema=schema_LineString,
                    crs=from_epsg(4326)) as out:
        for p in line:
            if len(p[0]) >= 3:
                line_geom = LineString(np.array(p[0])[:, 0:2])
                out.write({
                    'geometry': mapping(line_geom),
                    'properties': {
                        'id': id_line,
                        'z': np.array(p[0])[:, 2].mean(),
                        'label_name': p[1],
                        'label_hierarchy': p[2],
                        'filename': p[3],
                        'annotation_id_biigle': p[4],
                    }
                })
                id_line += 1


def export_3d_annotations(exp, output_path, point, line, polygon, coords_origin=None, thread=None):
    output_point_path = os.path.join(output_path, 'point_output.json')
    output_poly_path = os.path.join(output_path, 'poly_output.json')

    print("Exporting...")
    if exp == '3Dmetrics':
        exp_3dmetrics(output_point_path, output_poly_path, point, polygon, coords_origin)
    elif exp == 'shp':
        exp_shp(output_path, point, line, polygon, coords_origin)

    if thread is not None:
        thread.prog_val.emit(0)
        thread.finished.emit()
        thread.running = False

def save_bounds_polygons(output_path, polygon):
    export_polygon = {
        "Data": [],
        "Fields": [
            {
                "Name": "LabelName",
                "Type": "Text"
            },
            {
                "Name": "LabelHierarchy",
                "Type": "Text"
            },
            {
                "Name": "Filename",
                "Type": "Text"
            },
            {
                "Name": "AnnotationId",
                "Type": "Text"
            },
            {
                "Name": "Area",
                "Type": "Area"
            }
        ],
        "Measurement pattern": "3DMetrics",
        "Reference": {
            "altitude": 0,
            "latitude": 0,
            "longitude": 0,
        }
    }
    output_poly_path = os.path.join(output_path, 'all_bounds_polygons_output.json')

    for i in polygon:
        coords = i[0]
        pts = []
        for coord in coords:
            pts.append({
                "x": coord[0],
                "y": coord[1],
                "z": coord[2],
            })
        Area = {
            "area": 0,
            "Length": 0,
            "pts": pts,
        }
        pts_ann = [{"LabelName": str(i[1])},
                   {"LabelHierarchy": str(i[2])},
                   {"Filename": str(i[3])},
                   {"AnnotationId": str(i[4])},
                   {"Area": Area, }]
        export_polygon["Data"].append(pts_ann)

    out_file = open(output_poly_path, "w")
    json.dump(export_polygon, out_file, indent=4)
    out_file.close()

    return output_poly_path
