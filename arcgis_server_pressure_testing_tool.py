#! /usr/bin/env
# _*_ coding:utf-8 _*_
#__author__ = 'keling ma'

import os,sys,time,json,random, getopt
import common_utils


##-----------------------enter port------------------------------
# main entry for receive input args to determine execute which patten
def main(argv=None):
    opts, args = getopt.getopt(argv, "e:a:u:p:i:t:")
    output_path = ""
    url = ""
    portal_username = ""
    portal_password = ""
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

    export_file_p = create_result_file(output_path, "as_test_",'json')
    export_file_h = create_result_file(output_path, "as_test_", 'txt')

    print(common_utils.printSplitLine('Start testing......'))

    # url = r'https://123linux106.esrichina.com/portal'
    # portal_username = 'arcgis'
    # portal_password = 'Super123'

    test_key = 'owner:'+ portal_username

    #1 登陆server
    token = check_login(export_file_h, url, portal_username, portal_password)

    if token != 'failed':

        # 获取服务列表
        service_count, full_services_list, folders = get_services_list(export_file_h, url, token)

        dynamic_list, cache_list = classify_services(url, full_services_list, token)

        dynamic_dict = {}
        cache_dict = {}

        # i = 0
        # j = 0
        #
        # for service in dynamic_list:
        #     i += 1
        #     print(i, " ", service)
        #
        # for service in cache_list:
        #     j += 1
        #     print(j, " ", service)

        if len(dynamic_list) > 0:
            dynamic_dict = random_test_map_service(export_file_h, url, token, "Dynamic Map Service",dynamic_list, num, interval)
            print(dynamic_dict)

        if len(cache_list) > 0:
            cache_dict = random_test_map_service(export_file_h, url, token, "Cache Map Service", cache_list, num, interval)
            print(cache_dict)

            # 将结果写入json
            export_json = {"dynamic_service":dynamic_dict, "cache_service":cache_dict}

            json_file_write_format(export_file_p, export_json)





##----------------------checking login in-----------------------------

# check if input user could login enterprise portal.
def check_login(export_file_h, url, username, password):
    file = open(export_file_h, 'a+')
    tokenurl, result= generate_token(url, username, password)


    token = result[1]
    response_time = result[0]

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

##----------------------testing map service---------------------------------
def random_test_map_service(export_file_h, url, token, message, service_list, nums, interval):
    if len(service_list) > 0:
        dict = random_testing_services(export_file_h, url, token, message, service_list, nums, interval)

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
    params = {'token': token, 'f': 'json'}

    item = 'initialExtent'

    result = common_utils.submit_post_request(url,params,item)

    return result[1]

def request_map_service_query(url, token):
    try:
        request_url = url + '/export'
        bbox = get_initialExtents(url, token)

        if bbox == 'failed':
            return

        else:
            random_bbox = generate_random_bbox(bbox)
            params = {'token': token, 'f': 'json','format':'png','transparent':False,'bbox':random_bbox}
            r = common_utils.submit_post_request(request_url, params)


            return request_url, r
    except:
        return request_url, "failed"

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


##----------------------common methods-----------------------------
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
            request_url,result = request_map_service_query(submit_url, token)

            if request_url != None:
                common_utils.print_file_write_format(file, "Test url: " + request_url)

            response_time = result[0]

            if result[1] != "failed":
                common_utils.print_file_write_format(file, "response time: " + response_time)
                total_time += float(response_time[:-1])
                request_num += 1
            else:
                common_utils.print_file_write_format(file, "checking failed!")

            common_utils.print_file_write_format(file, "\n")
            time.sleep(interval)



    if int(request_num) > 0:
        common_utils.print_file_write_format(file, "The total test requests nums :" + str(request_num))
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