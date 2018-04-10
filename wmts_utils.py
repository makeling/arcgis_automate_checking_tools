#! /usr/bin/env
# _*_ coding:utf-8 _*_
# __author__ = 'keling ma'

import requests
from xml.dom.minidom import parseString
import random

# get tile matrix set identifier from input wmts url
def get_tmsi_from_url(url):
    url_group = url.split('/')
    i = 0
    for item in url_group:
        if item == '1.0.0':
            i += 3
            break

        i += 1
    if i > len(url -1):
        tmsi = ""
    else:
        tmsi = url_group[i]

    return tmsi

# get wmts capabilities url from the tile request url
def get_wmts_capabilities_url(url):
    url_group = url.split('/')
    url_wmts = ""
    i = 0
    for item in url_group:
        if item == '1.0.0':
            url_wmts += item + '/WMTSCapabilities.xml'
            break
        else:
            url_wmts += item + '/'

        i += 1

    return url_wmts

# submit request to get wmts capabilities
def request_wmts_capabilities(url):
    try:

        r = requests.request('get', url)

        return url, r.text
    except:
        return url, None


# compute tilematrix json
def compute_tile_matrix(level, resolution, map_xmin, map_ymin, map_xmax, map_ymax, ora_xmin, ora_ymax, tile_size):
    tile_matrix = {}

    print(level, " ", resolution, " ", map_xmin, " ,", map_ymin, "  ", map_xmax, " ", map_ymax, " ", ora_xmin, " ",
          ora_ymax, " ", tile_size)

    if map_xmin < ora_xmin:
        map_xmin = ora_xmin
    if map_ymax > ora_ymax:
        map_ymax = ora_ymax

    # print("min_x", map_xmin, "max_y", map_ymax)
    # print("ora_x", ora_xmin, "ora_y", ora_ymax)

    col_left_len = map_xmin - ora_xmin
    col_right_len = map_xmax - ora_xmin
    row_up_len = ora_ymax - map_ymax
    row_down_len = ora_ymax - map_ymin
    col_left_num = int(col_left_len / (resolution * tile_size))
    col_right_num = int(col_right_len / (resolution * tile_size))
    row_up_num = int(row_up_len / (resolution * tile_size))
    row_down_num = int(row_down_len / (resolution * tile_size))

    # print('width_c: ', col_right_num - col_left_num)
    # print('height_c: ', row_down_num - row_up_num)

    tile_matrix[level] = {'up_row': row_up_num, 'left_col': col_left_num, 'down_row': row_down_num,
                          'right_col': col_right_num}

    return tile_matrix

# compute resolution based on wmts rules
def compute_resolution(scale, meters_per_units):
    resolution = float(float(scale) * 0.28 * 0.001 / meters_per_units)
    return resolution

# decode wmts capabilities xml then get tile matrix include row_up, row_down, col_left, col_right json dictionary
def decode_wmts_xml(xmlString, tmsi, ):
    DOMTree = parseString(xmlString)

    collection = DOMTree.documentElement
    layer = collection.getElementsByTagName('Layer')
    bbox = layer[0].getElementsByTagName('ows:BoundingBox')
    #
    # print(type(bbox[0].))
    lower_Corner = bbox[0].getElementsByTagName('ows:LowerCorner')[0].childNodes[0].data
    upper_corner = bbox[0].getElementsByTagName('ows:UpperCorner')[0].childNodes[0].data

    map_minx = float(lower_Corner.split(" ")[0])
    map_miny = float(lower_Corner.split(" ")[1])
    map_maxx = float(upper_corner.split(" ")[0])
    map_maxy = float(upper_corner.split(" ")[1])
    # print('lower_corner: ', lower_Corner, '    upper_corner: ', upper_corner)
    # print(map_minx, " ", map_miny, " ", map_maxx, " ", map_maxy)

    tile_matrix_sets = collection.getElementsByTagName("TileMatrixSet")

    tile_level_matrix = []

    for tile_matrix_set in tile_matrix_sets:
        tile_matrixs = tile_matrix_set.getElementsByTagName('TileMatrix')
        if len(tile_matrixs) > 0:
            tile_matrix_set_identifier = tile_matrix_set.getElementsByTagName('ows:Identifier')[0].childNodes[0].data
            tile_matrix_crs = tile_matrix_set.getElementsByTagName('ows:SupportedCRS')[0].childNodes[0].data
            # print("tile_matrix_crs: ", tile_matrix_crs)
            # print("tile_matrix_set_identifier : ", tile_matrix_set_identifier)
            ll = len(tile_matrix_crs)
            meters_per_degree = get_meters_per_degree(int(tile_matrix_crs[ll - 4:]))
            # print("meters_per_degree", meters_per_degree)

            if tile_matrix_set_identifier == tmsi:
                i = 0
                for i in range(len(tile_matrixs)):
                    scale_denominator = tile_matrixs[i].getElementsByTagName('ScaleDenominator')[0].childNodes[0].data
                    identifier = tile_matrixs[i].getElementsByTagName('ows:Identifier')[0].childNodes[0].data
                    matrix_width = tile_matrixs[i].getElementsByTagName('MatrixWidth')[0].childNodes[0].data
                    matrix_height = tile_matrixs[i].getElementsByTagName('MatrixHeight')[0].childNodes[0].data
                    top_left_corner = tile_matrixs[i].getElementsByTagName('TopLeftCorner')[0].childNodes[0].data
                    tile_size = int(tile_matrixs[i].getElementsByTagName('TileWidth')[0].childNodes[0].data)
                    top_left_minx = float(top_left_corner.split(" ")[1])
                    top_left_maxy = float(top_left_corner.split(" ")[0])

                    resolution = compute_resolution(scale_denominator, meters_per_degree)

                    # print('width: ', matrix_width, '  height: ', matrix_height, '  resolution: ', resolution, '  scale: ', scale_denominator)

                    level = i

                    i += 1

                    tile_matrix = compute_tile_matrix(level, resolution, map_minx, map_miny, map_maxx, map_maxy,
                                                      top_left_minx, top_left_maxy, tile_size)

                    tile_level_matrix.append(tile_matrix)

                break

    return tile_level_matrix

# get meters per degree
def get_meters_per_degree(wkid):
    meters_per_degree = 1
    if wkid == 4326 or wkid == 4490:
        meters_per_degree = 2 * 3.14 * 6371004 / 360

    return meters_per_degree

# enter port for get tile matrix
def get_start_end_tile_from_wmts(url):
    wmts_capabilitis_url = get_wmts_capabilities_url(url)
    print(wmts_capabilitis_url)
    tmsi = get_tmsi_from_url(url)
    print(tmsi)
    request_url, r = request_wmts_capabilities(wmts_capabilitis_url)
    # print(r)
    tile_level_matrix = decode_wmts_xml(r, tmsi)

    return tile_level_matrix

# generate random level, row and column for test
def generate_random_test_lrc(url):
    tile_level_matrix = get_start_end_tile_from_wmts(url)

    l = len(tile_level_matrix)

    level = random.randint(0, l - 1)

    select = tile_level_matrix[level][level];

    up_row = select['up_row']
    down_row = select['down_row']
    left_col = select['left_col']
    right_col = select['right_col']

    width = right_col - left_col
    height = down_row - up_row

    if width > 8 or height > 8:
        col = random.randint(left_col + int(width / 4), right_col - int(width / 4))
        row = random.randint(up_row + int(height / 4), down_row - int(height / 4))
    else:
        row = random.randint(up_row, down_row)
        col = random.randint(left_col, right_col)
    return level, row, col


