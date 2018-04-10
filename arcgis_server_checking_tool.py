#! /usr/bin/env
# _*_ coding:utf-8 _*_
#__author__ = 'keling ma'

import os, sys, time, json, getopt
import common_utils

def main(argv=None):
    opts, args = getopt.getopt(argv, "e:a:u:p:")
    output_path = ""
    url = ""
    username = ""
    password = ""
    repair_times = 3

    if len(opts) < 3:
        print("Please input required parameters first!!! \n")
        print('[requied] -a : The arcgis server url address, eg: -a https://yourhost.domain.com:6443/arcgis')
        print('[requied] -u : The arcgis server administrator user name, eg: -u arcgis')
        print('[requied] -p: The arcgis server administrator password, eg: -p 123456')
        print(
            '[options] -e : The directory of stored check result file. The default value is create a new directory with name "as_check" relative to current path. \n')
        print('[options] -t: Repair times, the default value is 3 times')
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
                username = value
            else:
                print("Please input required parameter -u ")
                return
        elif op == "-p":
            if value != "":
                password = value
            else:
                print("Please input required parameter -p ")
                return
        elif op == "-t":
            if value != "":
                repair_times = int(value)


    # export_file_p = create_result_file(output_path, "as_check_", 'json')
    export_file_h = create_result_file(output_path, "as_check_", 'txt')

    print(common_utils.printSplitLine('Start testing......'))



    current_path = os.getcwd()
    server_config = current_path + os.sep + 'ags_pms.conf'

    token = check_login(export_file_h, url, username, password)

    service_count, full_services_list, folders = get_services_list(export_file_h, url, token)

    check_service_status(export_file_h, url, token, full_services_list, int(repair_times))

    check_instance_statistics(export_file_h,url,token,full_services_list,int(repair_times))

#check service instance status, then return error list and try to repair by restart service.
def check_instance_statistics(export_file,url,token,service_list,repair_times):
    try:
        file = open(export_file, 'a+')

        error_log = "位于{0}目录下的服务{1}在服务器{2}创建实例异常: 应创建最小实例数：{3}, 实际创建实例数：{4}。\n服务地址：{5} \n"

        error_services = {}

        common_utils.print_file_write_format(file, "\n")

        common_utils.print_file_write_format(file, common_utils.print_sub_title("start checking instance statistics", ""))


        for service in service_list:
            folder = service['folderName']
            serviceName = service['serviceName']
            type = service['type']

            if folder == "/":
                base_url = url + "/admin/services/"
            else:
                base_url = url + "/admin/services/" + folder + "/"

            params = {'token': token, 'f': 'json'}

            service_url = base_url + serviceName + "." + type

            common_utils.print_file_write_format(file, "checking service: " + service_url)

            responsetime, service_detail = common_utils.submit_post_request(service_url,params)

            # print(service_detail)

            min_instance_config = service_detail['minInstancesPerNode']

            stat_url = service_url + "/statistics"

            response = common_utils.submit_post_request(stat_url, params)

            statistics = response[1]
            summary = statistics['summary']
            machines = statistics['perMachine']
            m_count = len(machines)

            for machine in machines:
                machineName = machine['machineName']
                if machine['isStatisticsAvailable']:
                    # print(machine)
                    running_ins = int(machine['free']) + int(machine['busy'])

                    if running_ins < min_instance_config:
                        common_utils.print_file_write_format(file, error_log.format(folder, serviceName, machineName, min_instance_config, running_ins,
                                               service_url) + "\n")


                        error_services[serviceName] = service_url
                    else:
                        common_utils.print_file_write_format(file, "check " + machineName +" result : normal" )

            common_utils.print_file_write_format(file, "\n")

        file.close()

        if len(error_services.keys()) > 0 :
            file = open(export_file, "a+")
            common_utils.print_file_write_format(file, "check finished，continue to repair the instances")

            for service in error_services.keys():
                serviceName = service
                service_url = error_services[service]
                common_utils.print_file_write_format(file, "repairing service :" + service_url)

                result = repair_bugs(repair_times,serviceName,service_url,token)

                common_utils.print_file_write_format(file, "repair result :" + str(result))

            common_utils.print_file_write_format("repair instance status finished!")

            file.close()

        file = open(export_file, "a+")

        common_utils.print_file_write_format(file, "check finished!")

        file.close()


    except:
        common_utils.print_file_write_format(file, "check instanse failed!")
        file.close()
        return

#check service status, then export the status list and try to repair the bug.
def check_service_status(export_file,url,token,service_list,repair_times):
    try:
        error_log = "位于{0}目录下的服务{1}启动异常: 配置状态：{2}, 实际状态：{3}。\n服务地址：{4} \n"

        file = open(export_file, 'a+')

        common_utils.print_file_write_format(file, "\n")

        common_utils.print_file_write_format(file, common_utils.print_sub_title('start checking service status', ""))

        i = 0

        for service in service_list:
            folder = service['folderName']
            serviceName = service['serviceName']
            type = service['type']

            if folder == "/":
                base_url = url + "/admin/services/"
            else:
                base_url = url + "/admin/services/" + folder + "/"

            service_url = base_url + serviceName + "." + type

            common_utils.print_file_write_format(file, "checking service :" + service_url)

            check_url = service_url + "/status"

            params = {'token': token, 'f': 'json'}


            response = common_utils.submit_post_request(check_url,params)

            status = response[1]

            configuredState = status['configuredState']
            realTimeState = status['realTimeState']

            if configuredState != realTimeState:
                common_utils.print_file_write_format(file, error_log.format(folder, serviceName, configuredState, realTimeState, service_url))
                common_utils.print_file_write_format(file, "repairing service ..." )
                # restart service if check found the start status is abnormal
                repair_bugs(export_file,repair_times,serviceName,service_url,token)
            else:
                common_utils.print_file_write_format(file, "check result : normal")

            common_utils.print_file_write_format(file, "\n")

        common_utils.print_file_write_format(file, 'check and repair service start status finished!')
        file.close()

    except:
        common_utils.print_file_write_format(file, "check arcgis server service start status failed!")
        file.close()
        return

# this method will try many times(descided by repair_times param) to repair the bug.
def repair_bugs(repair_times, serviceName, service_url, token):
    try:
        result = ""
        for j in range(repair_times):
            result = restart_service(serviceName, service_url, token)
            # print("result:", result)
            if (result == "success"):
                print('restart service success!')
                return result

        if result != "success":
            print('trying to restart service failed, please inform administrator to help repair this problem!')

        return result

    except:
        print( "try to repair the bug failed!")
        return "failed"

# method for restart arcgis server service
def restart_service(service_Name,url,token):
    try:

        # print("restart service...")
        stop_url = url + "/stop"
        start_url = url + "/start"
        params = {'token': token, 'f': 'json'}
        response = common_utils.submit_post_request(stop_url, params)
        status_stop = response[1]["status"]
        # print("stop",service_Name,"service",status_stop,"!")
        if status_stop == "success":
            response = common_utils.submit_post_request(start_url,params)
            status_start = response[1]["status"]
            # print("start",service_Name,"service",status_start,"!")
        return response[1]["status"]
    except:
        print("restart the arcgis server services failed!")
        return


#----------------------------------common methods-----------------------------------------
# get folder list and services list in every folder.
def get_services_list(export_file, url, token):
    try:
        file = open(export_file, 'a+')

        common_utils.print_file_write_format(file,"\n")

        common_utils.print_file_write_format(file, common_utils.print_sub_title('getting full service list',""))

        request_url = url + "/admin/services"
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

        common_utils.print_file_write_format(file, "services_count:" + str(count))
        file.write("\n")

        file.close()
        return count, services_list,folders
    except:
        common_utils.print_file_write_format(file, "get services list failed!")
        file.close()
        return

# check if input user could login enterprise portal.
def check_login(export_file_h, url, username, password):
    file = open(export_file_h, 'a+')
    tokenurl, result= generate_token(url, username, password)

    common_utils.print_file_write_format(file, '-------------------------------ArcGIS Server cluster checking start------------------------------')


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


# create a new dir in the input path and a new file to store the export logs.
def create_result_file(path,filename,filetype):
    try:

        if len(path) == 0:
            path = os.getcwd() + os.sep + "as_check" + os.sep
        else:
            path = path + os.sep + "as_check" + os.sep

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



if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))