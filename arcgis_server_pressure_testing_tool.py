#! /usr/bin/env
# _*_ coding:utf-8 _*_
#__author__ = 'keling ma'

import os,sys,time,json,random, getopt
import common_utils
import math


##-----------------------enter port------------------------------
# main entry for receive input args to determine execute which patten
def main(argv=None):
    opts, args = getopt.getopt(argv, "e:a:u:p:i:t:")
    output_path = ""
    url = ""
    server_username = ""
    server_password = ""
    interval = 0
    num = 20

    if len(opts) < 3:
        print("Please input required parameters first!!! \n")
        print('[requied] -a : The arcgis server url address, eg: -a https://yourhost.domain.com:6443/arcgis')
        print('[requied] -u : The arcgis server administrator user name, eg: -u arcgis')
        print('[requied] -p: The arcgis server administrator password, eg: -p 123456')
        print(
            '[options] -e : The directory of stored check result file. The default value is create a new directory with name "be_check" relative to current path. \n')
        print('[options] -i : The interval of requests, unit - (s), the default value is 0 seconds')
        print('[options] -t: The request times, the default value is 20 times')
        print('\n')
        return


    for op, value in opts:
        if op == "-e":
            output_path = value
        elif op == "-a":
            if value != "":
                url = value
            else:
                print("Please input required parameter -a ")
                return
        elif op == "-u":
            if value != "":
                server_username = value
            else:
                print("Please input required parameter -u ")
                return
        elif op == "-p":
            if value != "":
                server_password = value
            else:
                print("Please input required parameter -p ")
                return
        elif op == "-i":
            if value != "":
                interval = int(value)
        elif op == "-t":
            if value != "":
                num = int(value)

    export_file_p = create_result_file(output_path, "as_test_",'json')
    export_file_h = create_result_file(output_path, "as_test_", 'txt')

    print(common_utils.printSplitLine('Start testing......'))


    #1 登陆server
    token = check_login(export_file_h, url, server_username, server_password)

    if token != 'failed':

        # 获取服务列表
        service_count, full_services_list, folders = get_services_list(export_file_h, url, token)

        dynamic_list, cache_list = classify_services(url, full_services_list, token)

        dynamic_dict = {}
        cache_dict = {}


        if len(dynamic_list) > 0:
            dynamic_dict = random_test_map_service(export_file_h, url, token, "Dynamic Map Service",dynamic_list, num, interval)
            # print(dynamic_dict)

        if len(cache_list) > 0:
            cache_dict = random_test_cache_service(export_file_h, url, token, "Cache Map Service", cache_list, num, interval)

            # 将结果写入json
            export_json = {"dynamic_service":dynamic_dict, "cache_service":cache_dict}

            json_file_write_format(export_file_p, export_json)


##----------------------login in server site-----------------------------

# check if input user could login server site.
def check_login(export_file_h, url, username, password):
    file = open(export_file_h, 'a+')
    tokenurl, result= generate_token(url, username, password)

    common_utils.print_file_write_format(file, '\n------------------------------ArcGIS Server cluster testing start------------------------------\n')


    token = result[1]
    response_time = result[0]

    if result[1] != "failed":
        common_utils.print_file_write_format(file, "login success, token: " + token)
        common_utils.print_file_write_format(file, "response time: " + response_time)

    else:
        common_utils.print_file_write_format(file, "User '"+username + "' login portal failed!")
    file.close()

    return token


# generate token by server admin api
def generate_token(url, username, password):
    try:

        tokenUrl = url + '/admin/generateToken'

        print(tokenUrl)

        # , 'ip':'192.168.100.85'
        params = {'username': username, 'password': password, 'client': 'requestip', 'f': 'json'}

        item = 'token'

        r = common_utils.submit_post_request(tokenUrl, params, item)

        return tokenUrl,r
    except:
        print("get token failed, please check url, username, password.")
        return


##----------------------get services list -----------------------------
# get folder list and services list in every folder.
def get_services_list(export_file, url, token):
    try:
        file = open(export_file, 'a+')

        request_url = url + "/rest/services"
        folders = ['/']
        params = {'token': token, 'f': 'json'}
        item = 'folders'
        result = common_utils.submit_post_request(request_url, params, item)

        if result != "failed":
            for f in result[1]:
                if str.upper(f) == "SYSTEM" or str.upper(f) == "UTILITIES" or str.upper(f) == "HOSTED":
                    continue
                else:
                    folders.append(f)

        common_utils.print_file_write_format(file, "All the folders:" + str(folders))

        services_list = []
        if folders != None:
            for folder in folders:
                if folder == '/':
                    folder_url = request_url
                else:
                    folder_url = request_url + "/" + folder
                item = 'services'
                services = common_utils.submit_post_request(folder_url, params, item)
                for i in services[1]:
                    services_list.append(i)
        count = len(services_list)

        common_utils.print_file_write_format(file, 'Get services list success!')

        common_utils.print_file_write_format(file, "services_count:" + str(count))

        file.write("\n")

        file.close()
        return count, services_list,folders
    except:
        common_utils.print_file_write_format(file, "get services list failed!")
        file.close()
        return

##----------------------testing dynamic map service---------------------------------
def random_test_map_service(export_file_h, url, token, message, service_list, nums, interval):
    if len(service_list) > 0:
        dict = random_testing_services(export_file_h, url, token, message, service_list, nums, interval)

        return dict
    else:
        return

def request_map_service_query(url, token):
    request_url = url + '/export'
    try:
        bbox = get_initialExtents(url, token)

        if bbox == 'failed':
            return request_url, None
        else:
            random_bbox = generate_random_bbox(bbox)
            params = {'token': token, 'f': 'json','format':'png','transparent':False,'bbox':random_bbox}
            r = common_utils.submit_post_request(request_url, params)


            return request_url, r
    except:
        return request_url, None

##----------------------testing cache map service-------------------
#compute tilematrix json
def compute_tile_matrix(tiling_schema, full_extent):
    tile_matrix = {}
    tile_size = tiling_schema['rows']

    ora_xmin = tiling_schema['origin']['x']
    ora_ymax = tiling_schema['origin']['y']

    map_xmin = full_extent['xmin']
    map_xmax = full_extent['xmax']
    map_ymin = full_extent['ymin']
    map_ymax = full_extent['ymax']

    if map_xmin < ora_xmin:
        map_xmin  = ora_xmin
    if map_ymax > ora_ymax:
        map_ymax = ora_ymax

    col_left_len = map_xmin - ora_xmin
    col_right_len = map_xmax - ora_xmin
    row_up_len = ora_ymax - map_ymax
    row_down_len = ora_ymax - map_ymin

    for level in tiling_schema['lods']:
        resolution = level['resolution']
        level_id = level['level']
        col_left_num = int(col_left_len  / (resolution * tile_size))
        col_right_num = int(col_right_len  / (resolution * tile_size))
        row_up_num =int(row_up_len  / (resolution * tile_size))
        row_down_num = int(row_down_len  / (resolution * tile_size))
        tile_matrix[level_id] = {'up_row': row_up_num, 'left_col':col_left_num, 'down_row':row_down_num, 'right_col':col_right_num}

    return tile_matrix

def random_test_cache_service(export_file_h, url, token, message, service_list, nums, interval):
    if len(service_list) > 0:
        file = open(export_file_h, 'a+')
        common_utils.print_file_write_format(file, common_utils.print_sub_title("\n\n" + "Testing " + message, ""))

        count = len(service_list)

        service_num = int(nums/count) + 1

        print('service_count:', count)
        # common_utils.print_file_write_format(file, message + " count: " + str(count))
        total_time = 0.0
        request_num = 0

        request_num = 0

        dict = {}
        sta_dict = {}


        for service in service_list:
            service_name = service['name']
            response = request_service_schema(url, token, service_name)

            fullExtent = response[1]['fullExtent']
            tile_schema = response[1]['tileInfo']
            tile_matrix = compute_tile_matrix(tile_schema, fullExtent)
            dict[service_name] = tile_matrix
            # print("service_name:", service_name)
            # for k in tile_matrix.keys():
            #     print(k, tile_matrix[k])


        for i in range(service_num):
            s = random.randint(0, count-1)
            service = service_list[s]
            service_name = service['name']

            for j in range(int(nums/service_num)):
                service_schema = dict[service_name]
                level = random.randint(0, len(service_schema)-1)
                right_col = service_schema[level]['right_col']
                left_col = service_schema[level]['left_col']
                up_row = service_schema[level]['up_row']
                down_row = service_schema[level]['down_row']
                width = right_col - left_col
                height = down_row - up_row
                if width >= 8 and height >= 8:
                    col = random.randint(left_col + int(width / 4), right_col - int(width / 4))
                    row = random.randint(up_row + int(height / 4), down_row - int(height / 4))
                else:
                    row = random.randint(service_schema[level]['up_row'], service_schema[level]['down_row'])
                    col = random.randint(service_schema[level]['left_col'], service_schema[level]['right_col'])
                request_url,response = request_cache_service_query(url, token, service_name, level, row, col)
                # print("level: ", level, " row: ",row, " col: ", col)
                # print(request_url)
                # print(r)

                common_utils.print_file_write_format(file, "Test url: " + request_url)

                if response != None:
                    response_time = response[0]
                    common_utils.print_file_write_format(file, "request result: " + str(response[1]))
                    common_utils.print_file_write_format(file, "response time: " + response_time)
                    if response[1] != "failed":
                        total_time += float(response_time[:-1])
                        request_num += 1
                else:
                    common_utils.print_file_write_format(file, "request failed!")
                    common_utils.print_file_write_format(file, "\n")

                time.sleep(interval)
                common_utils.print_file_write_format(file, "\n")

        if int(request_num) > 0:
            common_utils.print_file_write_format(file, "The total number of requests responding successfully : " + str(request_num))
            mean_time = total_time / request_num
            common_utils.print_file_write_format(file, 'All the requests consumed: ' + str("%.4f" % total_time) + 's')
            common_utils.print_file_write_format(file, 'Average response time: ' + str("%.4f" % mean_time) + 's')

            common_utils.print_file_write_format(file, "Test Map Service finished!")
            sta_dict['type'] = message
            sta_dict['nums'] = request_num
            sta_dict['sum_time'] = "%.4f" % total_time
            sta_dict['mean_time'] = "%.4f" % mean_time
            return sta_dict
        else:
            common_utils.print_file_write_format(file, "Test Map Service failed!")
            return

        file.close()
        return dict
    else:
        return

def request_cache_service_query(url, token, service_name, level, row, col):
    request_url = url + "/rest/services/" + service_name + "/MapServer" + '/tile/' + str(level) + '/' + str(
        row) + '/' + str(col)
    try:
        params = {}

        r = common_utils.submit_get_request_img(request_url, params)

        return request_url, r
    except:
        return request_url,None


##----------------------common methods-----------------------------
def request_service_schema(url, token, service_name):
    try:
        request_url = url + "/rest/services/" + service_name + "/MapServer"

        params = {'token': token, 'f': 'json'}

        r = common_utils.submit_post_request(request_url, params)
        return r

    except:
        return

def request_service_cache_status(url, service_name,token):
    try:
        request_url = url + "/admin/services/" + service_name + ".MapServer"

        params = {'token': token, 'f': 'json'}
        r = common_utils.submit_post_request(request_url, params)

        if r[1] != "failed":
            isCached = r[1]['properties']['isCached']

        return isCached
    except:
        return

#assistant method for generate random bbox by initial Extent.
def generate_random_bbox(bbox):

    minx = bbox['xmin']
    miny = bbox['ymin']
    maxx = bbox['xmax']
    maxy = bbox['ymax']

    xmin = minx
    ymin = miny
    xmax = maxx
    maxy = maxy

    x1 = random.uniform(minx,maxx)
    x2 = random.uniform(minx,maxx)
    if x1 > x2:
        xmax = x1
        xmin = x2
    else:
        xmax = x2
        xmin = x1

    y1 = random.uniform(miny,maxy)
    y2 = random.uniform(miny,maxy)

    if y1 > y2:
        ymin = y2
        ymax = y1
    else:
        ymin = y1
        ymax = y2

    param_bbox = str(xmin)+","+str(ymin)+","+str(xmax)+","+str(ymax)

    return param_bbox

# request get initial extents
def get_initialExtents(url,token):
    try:
        params = {'token': token, 'f': 'json'}

        item = 'initialExtent'

        result = common_utils.submit_post_request(url,params,item)

        return result[1]
    except:
        return 'failed'

def classify_services(url, service_list, token):
    dynamic_list = []
    cache_list = []
    for service in service_list:
        type = service['type']
        service_name = service['name']
        if type == 'MapServer':
            isCached = request_service_cache_status(url, service_name,token)
            if isCached == "true":
                cache_list.append(service)
            elif isCached == "false":
                dynamic_list.append(service)

    return dynamic_list, cache_list

# common method for deal random checking services
def random_testing_services(export_file_h, url, token, message,service_list,nums,interval):
    file = open(export_file_h, 'a+')
    common_utils.print_file_write_format(file, common_utils.print_sub_title("\n\n" + "Testing " + message, ""))

    count = len(service_list)
    common_utils.print_file_write_format(file, message + " count: " + str(count) )
    total_time = 0.0
    request_num = 0
    dict = {}
    request_num = 0

    for i in range(nums):
        s = random.randint(0, count - 1)
        service = service_list[s]

        if service['type'] == 'MapServer':
            submit_url = url + "/rest/services/" + service['name'] + "/" + service['type']

            common_utils.print_file_write_format(file, "submit_url" + str(submit_url))

            request_url,result = request_map_service_query(submit_url, token)


            if request_url != None:
                common_utils.print_file_write_format(file, "Test url: " + str(request_url))

            if result != None:
                response_time = result[0]
                common_utils.print_file_write_format(file, "response time: " + response_time)
                if result[1] != "failed":
                    common_utils.print_file_write_format(file, "response result: " + str(result[1]))
                    total_time += float(response_time[:-1])
                    request_num += 1
                else:
                    common_utils.print_file_write_format(file, "request failed!")


            common_utils.print_file_write_format(file, "\n")
            time.sleep(interval)



    if int(request_num) > 0:
        common_utils.print_file_write_format(file, "The total number of requests responding successfully :" + str(request_num))
        mean_time = total_time / request_num
        common_utils.print_file_write_format(file, 'All the requests consumed: ' + str("%.4f" % total_time) + 's')
        common_utils.print_file_write_format(file, 'Average response time: ' + str("%.4f" % mean_time) + 's')

        common_utils.print_file_write_format(file, "Test Map Service finished!")
        dict['type'] = message
        dict['nums'] = request_num
        dict['sum_time'] = "%.4f" % total_time
        dict['mean_time'] = "%.4f" % mean_time
        return dict
    else:
        common_utils.print_file_write_format(file, "Test Map Service failed!")
        return
    file.close()

# create a new dir in the input path and a new file to store the export logs.
def create_result_file(path,filename,filetype):
    try:

        if len(path) == 0:
            path = os.getcwd() + os.sep + "as_pressure" + os.sep
        else:
            path = path + os.sep + "as_pressure" + os.sep

        if os.path.exists(path) == False:
            os.mkdir(path)

        timeStamp = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))

        export_file = path + os.sep + filename + timeStamp + "." + filetype

        file = open(export_file, 'w')

        file.write("\n")
        file.close()


        return export_file
    except:
        print("create the result folder or result file failed!")
        return

def generate_txt_statistics(export_file_h, stats):
    file_h = open(export_file_h, 'a+')


    file_h.close()

def json_file_write_format(export_file, input_str):
    try:
        file = open(export_file, 'w')
        item = json.dumps(input_str)
        file.write(item)

        file.close()
    except:
        print("export file does not exist, please check!")

# script start
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))