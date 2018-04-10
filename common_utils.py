#-*- coding: UTF-8 -*-
#!/usr/bin/python
#__author__ = 'keling ma'

import requests
import os,json,sys
import time
import collections
import math

# method for get the connection parameters from a json file
def get_server_conns_params(config_file):
    try:
        file = open(config_file)
        params = json.load(file)
        # print(params)
        conns = params['conns']
        # print(conns)
        file.close()
        return conns
    except:
        print("open ags_pms.conf file failed, please check the path.")
        return

# method for get the config parameters from a json file
def get_config_params(config_file):
    try:
        file = open(config_file)
        params = json.load(file)
        # print(params)
        settings = params['settings']
        # print(settings)
        file.close()
        return settings
    except:
        print("open ags_pms.conf file failed, please check the path.")
        return

# print a dash line for format the different printing part.
def printSplitLine(comment):
    splitline = ""
    count = 0

    space_num = int((100 - len(comment)) / 2)
    space = ""
    for i in range(space_num):
        space += "*"

    if len(comment) % 2 == 0:
        splitline += space + comment + space[:-1]

    else:
        splitline += space + comment + space

    splitline += "\n"

    return splitline

# print a dash line for format the different part.
def print_sub_title(sub_title, content):
    splitline = ""

    splitline += sub_title

    splitline += "\n"

    for i in range(25):
        splitline += '='

    splitline += "\n"
    if content != "":
        splitline += content
        splitline += "\n"

    return splitline

def file_write_format(file, input_str):
    try:
        if isinstance(getattr(file, "read"), collections.Callable) \
                and isinstance(getattr(file, "close"), collections.Callable):
            file.write(input_str + "\n")
    except AttributeError:
        pass

#format the export informations
def print_file_write_format(file,input_str):
    print(input_str)
    file_write_format(file, input_str)

# generate token by arcgis server
def generate_token(url, username, password):
    try:
        tokenUrl = url + '/admin/generateToken'

        params = {'username': username, 'password': password, 'client': 'requestip', 'f': 'json'}

        item = 'token'

        r = submit_post_request(tokenUrl, params, item)

        return r[1]
    except:
        print("get token failed, please check url, username, password.")
        return

def submit_get_request_img(url, params):
    ssl = url[:5]
    err_flag = 'failed'
    elapse_time = '0.0 s'
    try:
        if ssl == "https":
            r = requests.get(url, params, verify=False)
        else:
            r = requests.get(url, params)

        if (r.status_code != 200):
            r.raise_for_status()
            print('request failed.')
            return err_flag
        else:
            data = r.content
            elapse_time = str("%.4f" % float(r.elapsed.microseconds / 1000 / 1000)) + 's'

            return elapse_time, data
    except:
        return elapse_time, err_flag

def submit_get_request(url, params, item=""):
    err_flag = 'failed'
    elapse_time = '0.0 s'
    try:
        r = requests.get(url, params, verify=False)

        if (r.status_code != 200):
            r.raise_for_status()
            print('request failed.')
            return err_flag
        else:
            data = r.text
            elapse_time = str("%.4f" % float(r.elapsed.microseconds / 1000 / 1000)) + 's'
            # Check that data returned is not an error object
            if not assertJsonSuccess(data):
                return
            # Extract service list from data
            result = json.loads(data)

            if item != "":
                last_result = result[item]
            else:
                last_result = result
            return elapse_time, last_result
    except:
        return elapse_time, err_flag

# assistant method for submit request
def submit_post_request(url, params, item=""):
    err_flag = 'failed'
    elapse_time = '0.0 s'
    try:
        r = requests.post(url, data=params, verify=False)

        if (r.status_code != 200):
            r.raise_for_status()
            print('request failed.')
            return err_flag
        else:
            data = r.text
            elapse_time = str("%.4f" % float(r.elapsed.microseconds / 1000 / 1000)) + 's'
            # Check that data returned is not an error object
            if not assertJsonSuccess(data):
                return
            # Extract service list from data
            result = json.loads(data)

            if item != "":
                last_result = result[item]
            else:
                last_result = result
            return elapse_time, last_result
    except:
        return elapse_time,err_flag


# assert response json
def assertJsonSuccess(data):
    obj = json.loads(data)
    if 'status' in obj and obj['status'] == "error":
        print('Error: JSON object returns an error.' + str(obj))
        sys.exit(False)
    else:
        return True


def generate_export_file():

    print(printSplitLine('creating export result file'))
    current_path = os.getcwd()
    export_file = create_result_file(current_path)
    print(export_file)
    file = open(export_file, 'a+')

    file_write_format(file, "export_file: " + str(export_file))

    file.close()


    return export_file

# create a new dir in the current path for store the check result file.
def create_result_file(current_path):
    try:
        export_result_folder = current_path + os.sep + "check_results"
        if os.path.exists(export_result_folder) == False:
            os.mkdir(export_result_folder)
        timeStamp = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))

        export_file = export_result_folder + os.sep + "result_" + timeStamp + ".txt"

        file = open(export_file, 'w')

        time_log = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

        file.write("\n")
        file_write_format(file, "update time：" + time_log)
        file.write("\n")

        file.close()
        # export_result_name = service_status

        return export_file
    except:
        print("create the check_results folder or result file failed!")
        return


# url = "https://192.168.100.95:6443/arcgis/rest/services/sms/tileTest/MapServer/tile/0/73/105"
# token= "cOUG1vHWfxG1FV7wo0aBd2tU-x0wYBpa9t0-LI4e8map0JOuN4QpjwzvLGQJ_Hoo"
#
# param = {'token':token}
#
# r = submit_get_request_img(url, param)
#
# print(r)


t = 3.2


print(math.ceil(t))




