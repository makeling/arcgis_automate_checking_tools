#! /usr/bin/env
# _*_ coding:utf-8 _*_
#__author__ = 'keling ma'

import psutil
import time
import os
import json
import sys, getopt
import platform
import collections

##-----------------------enter port------------------------------
# main entry for receive input args to determine execute which patten
def main(argv=None):
    opts, args = getopt.getopt(argv, "p:i:t:")
    output_path = ""
    interval = 2
    times = 3

    if len(opts) == 0:
        print("You could input parameters to control the behavior : eg: -p c:\esriMonitor . \n")
        print(
            '[options] -p : Input the directory of stored system statistics file. The default value is create a new directory with name "stats" relative to current path. \n')
        print('[options] -i : The interval of requests, unit - (s), the default value is 2 seconds')
        print('[options] -t: The request times, the default value is 3 times')
        print('\n')
        print('Good Luck!')


    for op, value in opts:
        if op == "-p":
            output_path = value
        elif op == "-i":
            interval = int(value)
        elif op == "-t":
            times = int(value)

    export_file_p = create_result_file(output_path, "sys_check_",'json')
    export_file_h = create_result_file(output_path, "sys_check_", 'txt')

    # print('正在进行数据采集，请耐心等待......')
    print(printSplitLine('正在进行数据采集，请耐心等待......'))
    stats = write_simple_system_statistics(times, interval)

    json_file_write_format(export_file_p, stats)

    generate_txt_statistics(export_file_h, stats)

##----------------------core methods-----------------------------

#write a simple system statistics json to a file
def write_simple_system_statistics(times, interval):
    user = psutil.users()[0][0]
    boot_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.boot_time()))
    coll_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    # netTitle = ["packets_sent", "packets_recv", ]
    net_ps = []
    net_pr = []
    cpu_list = []
    mem_list = []
    disk_list = []
    net_list = []
    for i in range(times):
        time.sleep(interval)
        cpu_list.append(psutil.cpu_percent(1))
        mem_list.append(psutil.virtual_memory()[2])
        disk_list.append(psutil.disk_usage('/')[3])
        net = psutil.net_io_counters()
        net_ps.append(net[2])
        net_pr.append(net[3])

    cpu_mean = compute_average(cpu_list)
    mem_mean = compute_average(mem_list)
    disk_mean = compute_average(disk_list)
    net_ps_mean = compute_average(net_ps)
    net_pr_mean = compute_average(net_pr)

    net_list = {"net_ps": net_ps, "net_pr": net_pr}
    all_list = {"cpu":cpu_list,"cpu_mean":cpu_mean,"mem":mem_list,"mem_mean":mem_mean, "dis":disk_list,
                "disk_mean":disk_mean,"net":net_list,"net_ps_mean":net_ps_mean,"net_pr_mean":net_pr_mean}

    all_json = {"user":user,"boot_time":boot_time,"coll_time":coll_time,"sta":all_list}

    return all_json

def compute_average(list):
    count = 0.0
    for i in list:

        count += float(i)

    mean = round(count/len(list), 2)

    return mean

##-----------------------system information-----------------------

def write_system_common_info(stats):
    result = ""
    result += "登陆用户: "
    result += str(stats['user'])
    result += '    '
    result += "登陆时间: "
    result += str(stats['boot_time'])
    result += '    '
    result += "采集时间: "
    result += str(stats['coll_time'])
    result += "\n"
    result += "操作系统版本: " + platform.platform()
    return result

def cpu_common_info(stats):
    result = ""
    cpu_count_l = str(psutil.cpu_count())
    cpu_count_p = str(psutil.cpu_count(logical=False))

    result = '逻辑cpu核数 ：'+ cpu_count_l
    result += '\n'
    result += '物理cpu核数 ：'+ cpu_count_p
    result += '\n'
    result += "cpu使用率均值："
    result += str(stats['cpu_mean']) + "%"
    return result

def mem_common_info(stats):
    result = ""
    result += '内存总量: '
    result += "%.2f" % float(psutil.virtual_memory()[0]/ 1024 / 1024)
    result += "M"
    result += "\n"
    result += '虚拟内存总量: '
    result += str(psutil.swap_memory()[0]/ 1024 / 1024)
    result += "M"
    result += "\n"
    result += '物理内存使用占比均值: '
    result += str(stats['mem_mean']) + "%"
    return result

def disk_common_info(stats):
    result = ""
    result += '监测硬盘总量: '
    result += "%.2f" % float(psutil.disk_usage('/')[0] / 1024 / 1024 / 1024)
    result += "G"
    result += "\n"
    result += '硬盘使用占比均值: '
    result += str(stats['disk_mean']) + "%"
    return result

def net_common_info(stats):
    result = ""
    result += '网络发送数据包均值: '
    result += str(stats['net_ps_mean'])
    result += "\n"
    result += '网络接收数据包均值: '
    result += str(stats['net_pr_mean'])
    return result


##-------------------------common tools-----------------------------

# create a new dir in the input path and a new file to store the export logs.
def create_result_file(path,filename,filetype):
    try:

        if len(path) == 0:
            path = os.getcwd() + os.sep + "stats" + os.sep
        else:
            path = path + os.sep + "stats" + os.sep

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

# print a dash line for format the different printing part.
def printSplitLine(comment):
    splitline = ""
    count = 0

    space_num = int((100 - len(comment)) / 2)
    space = ""
    for i in range(space_num):
        space += "*"

    if len(comment) % 2 == 0:
        splitline +=  space + comment + space[:-1]

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
        splitline += '-'

    splitline += "\n"
    splitline += content
    splitline += "\n"

    return splitline

def generate_txt_statistics(export_file_h, stats):
    file_h = open(export_file_h, 'a+')
    print_file_write_format(file_h, print_sub_title("系统基本信息:", write_system_common_info(stats)))
    print_file_write_format(file_h, print_sub_title("cpu：", cpu_common_info(stats['sta'])))
    print_file_write_format(file_h, print_sub_title("内存：", mem_common_info(stats['sta'])))
    print_file_write_format(file_h, print_sub_title("硬盘：", disk_common_info(stats['sta'])))
    print_file_write_format(file_h, print_sub_title("网络：", net_common_info(stats['sta'])))
    file_h.close()

def json_file_write_format(export_file, input_str):
    try:
        file = open(export_file, 'w')
        item = json.dumps(input_str)
        file.write(item)

        file.close()
    except:
        print("export file does not exist, please check!")

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

# script start
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

