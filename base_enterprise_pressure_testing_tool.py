#! /usr/bin/env
# _*_ coding:utf-8 _*_
#__author__ = 'keling ma'

import os,sys,time,json,random, getopt
import common_utils
import wmts_utils


##-----------------------enter port------------------------------
# main entry for receive input args to determine execute which patten
def main(argv=None):
    opts, args = getopt.getopt(argv, "e:a:u:p:i:t:")
    output_path = ""
    url = ""
    portal_username = ""
    portal_password = ""
    interval = 0
    num = 50

    if len(opts) < 3:
        print("Please input required parameters first!!! \n")
        print('[requied] -a : The portal url address, eg: -a https://yourhost.domain.com/portal')
        print('[requied] -u : The portal administrator user name, eg: -u arcgis')
        print('[requied] -p: The portal administrator password, eg: -p 123456')
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
                portal_username = value
            else:
                print("Please input required parameter -u ")
                return
        elif op == "-p":
            if value != "":
                portal_password = value
            else:
                print("Please input required parameter -p ")
                return
        elif op == "-i":
            if value != "":
                interval = int(value)
        elif op == "-t":
            if value != "":
                num = int(value)

    export_file_p = create_result_file(output_path, "be_test_",'json')
    export_file_h = create_result_file(output_path, "be_test_", 'txt')

    print(common_utils.printSplitLine('Start testing......'))

    # url = r'https://123linux106.esrichina.com/portal'
    # portal_username = 'arcgis'
    # portal_password = 'Super123'

    test_key = 'owner:'+ portal_username

    #1 登陆portal
    token = check_login(export_file_h, url, portal_username, portal_password)

    if token != 'failed':

        # 获取服务列表
        item_list = random_portal_searh_engine(export_file_h, url, token, test_key)

        if len(item_list) > 0:
            # 返回各类服务列表
            fs_list, ss_list, ms_list, wmts_list = classify_items(item_list)

            # 随机抽检hosting feature service健康状态
            fs_dict = random_test_hosting_feature_service(export_file_h, token, fs_list, num, interval)

            # 随机抽检map service健康状态
            ms_dict = random_test_map_service(export_file_h, token, ms_list, num, interval)

            # 随机抽检scene service健康状态
            ss_dict = random_test_scene_service(export_file_h, token, ss_list, num, interval)

            # 随机抽检WMTS服务健康状态
            ws_dict = random_test_wmts_service(export_file_h, token, wmts_list, num, interval)

            # 将结果写入json
            export_json = {"feature_service":fs_dict, "map_service":ms_dict, "scene_service":ss_dict, "wmts_service":ws_dict}

            json_file_write_format(export_file_p, export_json)





##----------------------checking login in-----------------------------

# check if input user could login enterprise portal.
def check_login(export_file_h, url, username, password):
    file = open(export_file_h, 'a+')
    tokenurl, result= generate_token(url, username, password)




    token = result[1]
    response_time = result[0]

    common_utils.print_file_write_format(file,"-----------------------------Base Enterprise platform testing start------------------------------")

    if result[1] != "failed":
        common_utils.print_file_write_format(file, "login success, token: " + token)
        common_utils.print_file_write_format(file, "response time: " + response_time)

    else:
        common_utils.print_file_write_format(file, "User '"+username + "' login portal failed!")
    file.close()

    return token


# generate token by portal rest api
def generate_token(url, username, password):
    try:

        tokenUrl = url + '/sharing/rest/generateToken'

        referer = url[:-6]

        # , 'ip':'192.168.100.85'
        params = {'username': username, 'password': password, 'client': 'referer', 'referer': referer, 'f': 'json'}
        item = 'token'

        r = common_utils.submit_post_request(tokenUrl, params, item)

        return tokenUrl,r
    except:
        print("get token failed, please check url, username, password.")
        return


##----------------------get services list by search-----------------------------
def random_portal_searh_engine(export_file_h, url, token,test_key):
    file = open(export_file_h, 'a+')

    num = 1

    request_url, result = request_search(url, token, test_key,num)


    response_time = result[0]

    total_item = result[1]['total']

    common_utils.print_file_write_format(file, "Total items:" + str(total_item))

    if total_item > 0:
        r_url, r = request_search(url, token, test_key, total_item)

    if r[1]!= "failed":
        common_utils.print_file_write_format(file, "Get services list success!")
    else:
        common_utils.print_file_write_format(file, "Get services list success! failed!")


    return r[1]['results']

def request_search(url, token, test_key,num):
    request_url = url + '/sharing/rest/search'

    params = {'f': 'json', 'token': token, 'q':test_key, 'num':num}

    r = common_utils.submit_get_request(request_url, params)

    return request_url, r

##----------------------testing feature service-----------------------------
def random_test_hosting_feature_service(export_file_h, token, service_list, nums, interval):
    if len(service_list) > 0:
        dict = random_testing_services(export_file_h,token,service_list, '1',nums, interval)
        return dict
    else:
        return


def request_feature_service_query(url, token):
    l = len(url)

    where = "objectid < 100"

    if (url[l - 2:l] == '/0'):
        request_url = url + '/query'
        params = {'f': 'json', 'where': where}
    else:
        request_url = url + '/0/query'
        params = {'f': 'json', 'token': token, 'where': where}

    r = common_utils.submit_post_request(request_url, params)

    return request_url, r


##----------------------testing scene service-------------------------------
def random_test_scene_service(export_file_h, token, service_list, nums, interval):
    if len(service_list) > 0 :
        dict = random_testing_services(export_file_h, token, service_list, '3', nums, interval)
        return dict
    else:
        return


def request_scene_service_query(url, token):
    request_url = url

    params = {'f': 'json', 'token': token}

    r = common_utils.submit_post_request(request_url, params)

    return request_url, r

##----------------------testing map service---------------------------------
def random_test_map_service(export_file_h, token, service_list, nums, interval):
    if len(service_list) > 0:
        dict = random_testing_services(export_file_h, token, service_list, '2', nums, interval)
        return dict
    else:
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
    params = {'f': 'json'}

    item = 'initialExtent'

    result = common_utils.submit_post_request(url,params,item)

    return result[1]

def request_map_service_query(url, token):
    request_url = url + '/export'
    bbox = get_initialExtents(url, token)

    if bbox == 'failed':
        return

    else:
        random_bbox = generate_random_bbox(bbox)
        params = {'f': 'json','format':'png','transparent':False,'bbox':random_bbox}
        r = common_utils.submit_post_request(request_url, params)
        return request_url, r


##----------------------testing wmts service----------------------------------------
def random_test_wmts_service(export_file_h, token, service_list, nums, interval):
    if len(service_list) > 0:
        dict = random_testing_services(export_file_h, token, service_list, '4', nums, interval)
        return  dict
    else:
        return


def request_wmts_service_query(url, token):
    try:
        level,row,col = wmts_utils.generate_random_test_lrc(url)

        request_url = str(url).replace('{level}', level).replace('{row}', row).replace('{col}', col)

        params = {'f': 'json'}

        r = common_utils.submit_get_request_img(request_url, params)

        return request_url, r
    except:
        return url,None


##----------------------common methods-----------------------------
def classify_items(item_list):
    fs_list = []
    ss_list = []
    ms_list = []
    wmts_list = []
    for item in item_list:
        type = item['type']
        if type == 'Feature Service':
            fs_list.append(item)
        elif type == 'Scene Service':
            ss_list.append(item)
        elif type == 'Map Service':
            ms_list.append(item)
        elif type == 'WMTS':
            wmts_list.append(item)
    return fs_list, ss_list,ms_list, wmts_list


# common method for deal random checking services
def random_testing_services(export_file_h, token, service_list,seq, nums,interval):
    file = open(export_file_h, 'a+')
    type = service_list[0]['type']
    common_utils.print_file_write_format(file, common_utils.print_sub_title("\n\n" + seq + " Testing " + type, ""))

    count = len(service_list)
    total_time = 0.0
    request_num = 0
    dict = {}

    for i in range(nums):
        s = random.randint(0, count - 1)
        service = service_list[s]
        service_url = service['url']
        if type == "Feature Service":
            request_url, result = request_feature_service_query(service_url,token)
        elif type == "Scene Service":
            request_url, result = request_scene_service_query(service_url, token)
        elif type == "Map Service":
            request_url, result = request_map_service_query(service_url, token)
        elif type == "WMTS":
            request_url, result = request_wmts_service_query(service_url, token)

        if request_url != None:
            common_utils.print_file_write_format(file, "Test url: " + request_url)

        response_time = result[0]

        if result != None:
            if result[1] != "failed":
                common_utils.print_file_write_format(file, "response time: " + response_time)
                # common_utils.print_file_write_format(file, "response result: " + str(result[1]))
                # common_utils.print_file_write_format(file, "checking passed!")
                total_time += float(response_time[:-1])
                request_num += 1
            else:
                common_utils.print_file_write_format(file, "checking failed!")

        common_utils.print_file_write_format(file, "\n")
        time.sleep(interval)


    if int(request_num) != 0:
        common_utils.print_file_write_format(file, "The total test requests nums :" + str(request_num))
        mean_time = total_time / request_num
        common_utils.print_file_write_format(file, 'All the requests consumed: ' + str("%.4f" % total_time) + 's')
        common_utils.print_file_write_format(file, 'Average response time: ' + str("%.4f" % mean_time) + 's')

        common_utils.print_file_write_format(file, "Test " + type + " finished!")
        dict['type'] = type
        dict['nums'] = request_num
        dict['sum_time'] = "%.4f" % total_time
        dict['mean_time'] = "%.4f" % mean_time
        return dict
    else:
        common_utils.print_file_write_format(file, "Test " + type + " failed!")
        return


# create a new dir in the input path and a new file to store the export logs.
def create_result_file(path,filename,filetype):
    try:

        if len(path) == 0:
            path = os.getcwd() + os.sep + "be_pressure" + os.sep
        else:
            path = path + os.sep + "be_pressure" + os.sep

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