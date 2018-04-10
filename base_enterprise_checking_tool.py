#! /usr/bin/env
# _*_ coding:utf-8 _*_
#__author__ = 'keling ma'

import os,sys,time,json,random, getopt
import common_utils
import wmts_utils


##-----------------------enter port------------------------------
# main entry for receive input args to determine execute which patten
def main(argv=None):
    opts, args = getopt.getopt(argv, "e:a:u:p:n:")
    output_path = ""
    url = ""
    portal_username = ""
    portal_password = ""
    num = 3

    if len(opts) < 3:
        print("Please input required parameters first!!! \n")
        print('[requied] -a : The portal url address, eg: -a https://yourhost.domain.com/portal')
        print('[requied] -u : The portal administrator user name, eg: -u arcgis')
        print('[requied] -p: The portal administrator password, eg: -p 123456')
        print(
            '[options] -e : The directory of stored check result file. The default value is create a new directory with name "be_check" relative to current path. \n')
        print('[options] -n: The numbers for select services to check from portal content, the default value is 10')
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
        elif op == "-n":
            if value != "":
                num = int(value)

    # export_file_p = create_result_file(output_path, "beall",'json')
    export_file_h = create_result_file(output_path, "be_check_", 'txt')

    print(common_utils.printSplitLine('开始检测......'))

    # url = r'https://123linux106.esrichina.com/portal'
    # portal_username = 'arcgis'
    # portal_password = 'Super123'

    test_key = 'owner:'+ portal_username

    #1 检测portal是否可以成功登陆
    token = check_login(export_file_h, url, portal_username, portal_password)

    if token != 'failed':
        #2 检测portal健康状态
        check_portal_health(export_file_h, url, token)

        # 3 检测hosting server健康状态
        hosting_server_url = check_hosting_server_status(export_file_h, url, token)
        if hosting_server_url != "":
            # 4 检测关系型数据库的健康状态
            check_relational_db_status(export_file_h, hosting_server_url,token)

        # 5 检测portal搜索引擎的健康状态
        item_list = random_portal_searh_engine(export_file_h, url, token, test_key)

        # i = 0

        # for item in item_list:
        #     i += 1
        #     print(i, " " ,item)

        if len(item_list) > 0:
            # 返回各类服务列表
            fs_list, ss_list, ms_list, wmts_list = classify_items(item_list)

            # print("fs_len:", len(fs_list))
            # print("ss_len:", len(ss_list))
            # print("ms_len:", len(ms_list))
            # print("wmts_len:", len(wmts_list))

            # 随机抽检hosting feature service健康状态
            random_check_hosting_feature_service(export_file_h, token, fs_list, num)

            # 随机抽检map service健康状态
            random_check_map_service(export_file_h, token, ms_list, num)

            # 随机抽检scene service健康状态
            random_check_scene_service(export_file_h, token, ss_list, num)

            # 随机抽检WMTS服务健康状态
            random_check_wmts_service(export_file_h, token, wmts_list, num)



##----------------------checking login in-----------------------------

# check if input user could login enterprise portal.
def check_login(export_file_h, url, username, password):
    file = open(export_file_h, 'a+')
    common_utils.print_file_write_format(file, '---------------------------------Base Enterprise platform checking start--------------------------------')
    common_utils.print_file_write_format(file, common_utils.print_sub_title("1 checking login status",""))
    tokenurl, result= generate_token(url, username, password)
    common_utils.print_file_write_format(file, "checking url: " + tokenurl)

    token = result[1]
    response_time = result[0]

    if result[1] != "failed":
        common_utils.print_file_write_format(file, "response result: " + token)
        common_utils.print_file_write_format(file, "response time: " + response_time)
        common_utils.print_file_write_format(file, "checking passed!")
    else:
        common_utils.print_file_write_format(file, "User '"+username + "' login portal failed!")
    file.close()

    return token


# generate token by portal rest api
def generate_token(url, username, password):
    try:

        tokenUrl = url + '/sharing/rest/generateToken'

        referer = url[:-6]

        print('referer: ',referer)

        # , 'ip':'192.168.100.85'
        params = {'username': username, 'password': password, 'client': 'referer','referer':referer,'f': 'json'}

        item = 'token'

        r = common_utils.submit_post_request(tokenUrl, params, item)

        return tokenUrl,r
    except:
        print("get token failed, please check url, username, password.")
        return

##----------------------check portal health-----------------------------
def check_portal_health(export_file_h, url, token):
    file = open(export_file_h, 'a+')
    common_utils.print_file_write_format(file, common_utils.print_sub_title("\n\n"+"2 checking portal health", ""))

    machines = request_portal_machine(url, token)

    machine = machines['machines'][0]
    machine_name = machine['machineName']

    if machine_name != None:
        request_url, result = request_portal_machine_status(url,token,machine_name)

        common_utils.print_file_write_format(file, "checking url:" + request_url)

        response_time = result[0]

        if result[1] != "failed":
            common_utils.print_file_write_format(file, "response result: " + str(result[1]))
            common_utils.print_file_write_format(file, "response time: " + response_time)
            common_utils.print_file_write_format(file, "checking passed!")
        else:
            common_utils.print_file_write_format(file, "portal machine checking failed!")
        file.close()

def request_portal_machine(url, token):
    request_url = url + '/portaladmin/machines'
    params = {'f':'json', 'token':token}
    r = common_utils.submit_get_request(request_url,params)
    return r[1]

def request_portal_machine_status(url, token, machine_name):
    request_url = url + '/portaladmin/machines/' +"status/"+ machine_name
    params = {'f': 'json', 'token': token}
    r = common_utils.submit_get_request(request_url, params)
    return request_url, r


##----------------------check hosting server health-----------------------

def check_hosting_server_status(export_file_h, url,token):
    file = open(export_file_h, 'a+')
    common_utils.print_file_write_format(file, common_utils.print_sub_title("\n\n" + "3 checking hosting server health", ""))
    machines = request_hosting_server_machine(url, token)

    machine_id = ""
    hosting_server_url = ""

    for machine in machines['servers']:
        isHosted = machine['isHosted']
        if isHosted == True:
            machine_id = machine['id']
            hosting_server_url = machine['adminUrl']

    if machine_id != "":
        request_url, result = request_hosting_server_machine_status(url, token, machine_id)

        common_utils.print_file_write_format(file, "checking url:" + request_url)

        response_time = result[0]

        if result[1] != "failed":
            common_utils.print_file_write_format(file, "response result: " + str(result[1]['messages']))
            common_utils.print_file_write_format(file, "response time: " + response_time)
            common_utils.print_file_write_format(file, "checking passed!")
        else:
            common_utils.print_file_write_format(file, "portal machine checking failed!")
        file.close()

    return hosting_server_url

def request_hosting_server_machine(url, token):
    request_url = url + '/portaladmin/federation/servers'
    params = {'f': 'json', 'token': token}
    r = common_utils.submit_get_request(request_url, params)
    return r[1]

def request_hosting_server_machine_status(url, token, machine_id):
    request_url = url + '/portaladmin/federation/servers/' +  machine_id + '/validate'
    params = {'f': 'json', 'token': token}
    r = common_utils.submit_get_request(request_url, params)
    return request_url, r


##----------------------checking datastore----------------------------------
def check_relational_db_status(export_file_h, url, token):
    file = open(export_file_h, 'a+')
    common_utils.print_file_write_format(file, common_utils.print_sub_title("\n\n" + "4 checking relational datastore health", ""))
    # token = common_utils.generate_token(url,username, password)

    result = request_relational_db_machines(url, token)

    dbs = result['items']

    for db in dbs:
        path = db['path']
        provider = db['provider']
        # print(db['info']['machines'])
        machine_name = db['info']['machines'][0]['name']

        common_utils.print_file_write_format(file, "checking db in machine: " + machine_name)

        if provider == "ArcGIS Data Store":
            request_url, result = request_relational_db_status(url, token, path,machine_name)
            common_utils.print_file_write_format(file, "checking url: " + request_url)

            response_time = result[0]

            if result[1] != "failed":
                common_utils.print_file_write_format(file, "response result: " + str(result[1]))
                common_utils.print_file_write_format(file, "response time: " + response_time)
                common_utils.print_file_write_format(file, "checking passed!")
            else:
                common_utils.print_file_write_format(file, "portal machine checking failed!")
            common_utils.print_file_write_format(file, "\n")

    file.close()

def request_relational_db_machines(url, token):
    request_url = url + '/admin/data/findItems'
    params = {'f': 'json', 'token': token, 'parentPath':'/enterpriseDatabases', 'types':'egdb'}
    r = common_utils.submit_post_request(request_url, params)
    return r[1]

def request_relational_db_status(url, token, path,machine_name):
    request_url = url + '/admin/data/items' + path + '/machines/'+machine_name + '/validate'
    params = {'f': 'json', 'token': token}
    r = common_utils.submit_post_request(request_url, params)
    return request_url, r

##----------------------checking search-----------------------------
def random_portal_searh_engine(export_file_h, url, token,test_key):
    file = open(export_file_h, 'a+')
    common_utils.print_file_write_format(file, common_utils.print_sub_title("\n\n" + "5 checking portal search engine", ""))
    num = 1

    request_url, result = request_search(url, token, test_key,num)
    common_utils.print_file_write_format(file, "checking url: " + request_url)

    response_time = result[0]
    total_item = 0

    if result[1]!= "failed":
        common_utils.print_file_write_format(file, "response result: " + str(result[1]))
        common_utils.print_file_write_format(file, "response time: " + response_time)
        common_utils.print_file_write_format(file, "checking passed!")
        total_item = result[1]['total']
        common_utils.print_file_write_format(file, "\n")
        common_utils.print_file_write_format(file, "Total items:" + str(total_item))
    else:
        common_utils.print_file_write_format(file, "portal search engine checking failed!")

    if total_item > 0:
        r_url, r = request_search(url, token, test_key, total_item)

    # common_utils.print_file_write_format(file, "\n")
    return r[1]['results']

def request_search(url, token, test_key,num):
    request_url = url + '/sharing/rest/search'

    params = {'f': 'json', 'token': token, 'q':test_key, 'num':num}

    r = common_utils.submit_get_request(request_url, params)

    return request_url, r

##----------------------checking feature service-----------------------------
def random_check_hosting_feature_service(export_file_h, token, service_list, nums):
    if len(service_list) > 0:
        random_checking_services(export_file_h,token,service_list, '6',nums)
    else:
        return


def request_feature_service_query(url, token):
    try:
        l = len(url)

        where = "objectid < 100"

        if(url[l-2:l] == '/0'):
            request_url = url + '/query'
            params = {'f': 'json', 'where': where}
        else:
            request_url = url + '/0/query'
            params = {'f': 'json', 'token': token, 'where': where}


        r = common_utils.submit_post_request(request_url, params)

        return request_url, r
    except:
        return "",None


##----------------------checking scene service-------------------------------
def random_check_scene_service(export_file_h, token, service_list, nums):
    if len(service_list) > 0 :
        random_checking_services(export_file_h, token, service_list, '8', nums)
    else:
        return


def request_scene_service_query(url, token):
    try:
        request_url = url

        params = {'f': 'json', 'token': token}

        r = common_utils.submit_post_request(request_url, params)

        return request_url, r
    except:
        return "",None

##----------------------checking map service---------------------------------
def random_check_map_service(export_file_h, token, service_list, nums):
    if len(service_list) > 0:
        random_checking_services(export_file_h, token, service_list, '7', nums)
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
    try:
        params = {'f': 'json'}

        item = 'initialExtent'

        result = common_utils.submit_post_request(url,params,item)

        return result[1]
    except:
        return None

def request_map_service_query(url, token):
    try:
        request_url = url + '/export'
        bbox = get_initialExtents(url, token)

        if bbox == 'failed':
            return

        else:
            random_bbox = generate_random_bbox(bbox)
            params = {'f': 'json','format':'png','transparent':False,'bbox':random_bbox}
            r = common_utils.submit_post_request(request_url, params)
            return request_url, r
    except:
        return "", None


##----------------------checking wmts----------------------------------------
def random_check_wmts_service(export_file_h, token, service_list, nums):
    if len(service_list) > 0:
        random_checking_services(export_file_h, token, service_list, '9', nums)
    else:
        return


def request_wmts_service_query(url, token):
    try:
        level, row, col = wmts_utils.generate_random_test_lrc(url)

        request_url = str(url).replace('{level}', level).replace('{row}', row).replace('{col}', col)

        params = {'f': 'json'}

        r = common_utils.submit_get_request_img(request_url, params)

        return request_url, r
    except:
        return url, None


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
def random_checking_services(export_file_h, token, service_list,seq, nums):
    file = open(export_file_h, 'a+')
    type = service_list[0]['type']
    common_utils.print_file_write_format(file, common_utils.print_sub_title("\n\n" + seq + " checking " + type, ""))

    test_nums = len(service_list)
    count = len(service_list)
    total_time = 0.0
    request_num = 0

    if nums < test_nums:
        test_nums = nums

    for i in range(test_nums):
        s = random.randint(0, count-1)
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
            common_utils.print_file_write_format(file, "checking url: " + request_url)

        response_time = result[0]

        if result != None:
            if result[1] != "failed":
                common_utils.print_file_write_format(file, "response time: " + response_time)
                common_utils.print_file_write_format(file, "response result: " + str(result[1]))
                common_utils.print_file_write_format(file, "checking passed!")
                total_time += float(response_time[:-1])
                request_num += 1
            else:
                common_utils.print_file_write_format(file, "checking failed!")

        common_utils.print_file_write_format(file, "\n")


    if int(request_num) != 0:
        common_utils.print_file_write_format(file, "The total testing service nums :" + str(request_num))
        mean_time = total_time / request_num
        common_utils.print_file_write_format(file, 'All the requests consumed: ' + str("%.4f" % total_time) + 's')
        common_utils.print_file_write_format(file, 'Average response time: ' + str("%.4f" % mean_time) + 's')

        common_utils.print_file_write_format(file, "Check " + type + " passed!")
    else:
        common_utils.print_file_write_format(file, "No validate" + type + " can be checked!")


# create a new dir in the input path and a new file to store the export logs.
def create_result_file(path,filename,filetype):
    try:

        if len(path) == 0:
            path = os.getcwd() + os.sep + "be_check" + os.sep
        else:
            path = path + os.sep + "be_check" + os.sep

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