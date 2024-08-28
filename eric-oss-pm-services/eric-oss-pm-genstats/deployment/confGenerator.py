#!/usr/bin/python

################################################################################
# COPYRIGHT Ericsson 2018
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program (s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 22.08
# Purpose       :  Take MiniLink sim argument and write it in /netsim/genstats/transport_sim_details file.
# Jira No       :  NSS-39124
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/12249429/
# Description   :  MINI-LINK Indoor - Genstats support for ML6371 node(PM)
# Date          :  18/04/2022
# Last Modified :  surendra.mattaparthi@tcs.com
####################################################

import os
from subprocess import Popen, PIPE
import subprocess
import sys
import datetime
from time import strftime, gmtime
import logging

TRANSPORT_FILE = "/netsim/genstats/transport_sim_details"
GENSTATS_SCRIPT = "/netsim_users/pms/bin/genStats"
MINILINK_TEMPLATE_DIR = '/netsim_users/pms/minilink_templates'
MINILINK_MO_TYPE = None
ARG_SEPARATOR = ";"
DOUBLE_COLON_SEPARATOR = "::"
SAMPLE_FILESIZE = {'Small' : ['CN510', 'CN810', 'CN210'], '4_4_FP7' : ['AMM6pD'], 'Large' : ['AMM20pB', 'ML-LH', 'LH', 'ML-TN', 'TN' ,'AMM2pB'], '66xx' : ['ML6651', 'ML6691', 'ML6692', 'ML6693', 'ML6366', 'ML6200', 'ML6371']}
arg_map = {}
INFO = 'info'
WARN = 'warning'
ERROR = 'error'
process_id = None


def initialize_logger():
    global CONF_LOG_FILE, formatter
    CONF_LOG_FILE = '/netsim_users/pms/logs/minilink_file_generation.log'
    formatter = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(filename=CONF_LOG_FILE, format=formatter, level=logging.INFO)


def run_shell_command(input):
    """ This is the generic method, Which spawn a new shell process to get the job done
    """
    output = Popen(input, stdout=PIPE, shell=True).communicate()[0]
    return output


def conf_file_permission(permission):
    """ This is the generic method to change the permission of files
    """
    command = "chmod " + permission + "  " + TRANSPORT_FILE
    run_shell_command(command)


def getCurrentDateTime():
    """ Creates date time in formatted way for logging.
    """
    return strftime("%Y-%m-%d %H:%M:%S", gmtime())


def argument_parser(input_args):
    """ Take input arguments and store attribute name and it's value in map by parsing it
            {arg_map} : {attr_name : attr_value}
    """
    global arg_map
    arg_list = input_args.split(ARG_SEPARATOR)

    if not len(arg_list) > 2:
        printLogs('Invalid number of argument.', ERROR)

    sim_name = ""
    node_name = ""

    for arg_data in arg_list:
        attr_name = arg_data.split(DOUBLE_COLON_SEPARATOR)[0]
        attr_value = arg_data.split(DOUBLE_COLON_SEPARATOR,1)[1]

        if "sim_name" == attr_name:
            if not sim_name:
                arg_map[attr_name] = attr_value
            else:
                printLogs('Multiple simulation name given.', ERROR)
        elif "node_name" == attr_name:
            if not node_name:
                arg_map[attr_name] = attr_value
            else:
                printLogs('Multiple node name given in argument.', ERROR)
        elif "node_type" == attr_name:
            if 'nodeType' not in arg_map.keys():
                arg_map["nodeType"] = attr_value
            else:
                printLogs('Multiple node type given in argument.', ERROR)
        else:
            arg_map[attr_name] = attr_value

    """ Check for node_type, node_name, node_category, sim_name for Minilink
        Create and validate different attributes value by calling various methods (like, gran period, rcID, start and end time , etc..)
    """
    if 'sim_name' in arg_map.keys() and 'node_name' in arg_map.keys():
        if 'nodeType' in arg_map.keys() and 'Mini-Link' in arg_map.get('nodeType'):
            if not os.path.isdir(MINILINK_TEMPLATE_DIR):
                printLogs('Minilink templates directory' + MINILINK_TEMPLATE_DIR + ' is not exists. Exiting process.', ERROR)
            if 'rcID' in arg_map.keys():
                global MINILINK_MO_TYPE
                if int(arg_map.get('rcID')) < 100:
                    MINILINK_MO_TYPE = 'ETHERNET'
                elif int(arg_map.get('rcID')) > 99:
                    MINILINK_MO_TYPE = 'SOAM'
                # checking for request, whether it is for Indoor or Outdoor Minilink
                if 'node_category' in arg_map.keys():
                    if arg_map.get('node_category').upper() == 'OUTDOOR':
                        change_arg_map('OUTDOOR')
                        printLogs('PM file generation requested for MiniLink Outdoor node having process id : ' + process_id + '.', INFO)
                    elif arg_map.get('node_category').upper() == 'SWITCH':
                        change_arg_map('SWITCH')
                        printLogs('PM file generation requested for Switch node having process id : ' + process_id + '.', INFO)
                    process_minilink_outdoor_request()
                    sys.exit(0)
                printLogs('PM file generation requested for MiniLink Indoor node.', INFO)
                arg_map['node_category'] = 'INDOOR'
                arg_map['file_name'] = getAttributeValue('filename')
                printLogs('Minilink PM file requested : ' + arg_map.get('file_name'), INFO)
                arg_map['start_time'] = arg_map.get('file_name')[1:][:18]
                arg_map['end_time'] = getEndInterval(arg_map.get('file_name'))
                setUserLableAndLocalDn(arg_map.get('file_name'))
                arg_map['gran_period'] = getAttributeValue('gran_period')
            else:
                printLogs('rcID is not present. Exiting code.', ERROR)

            if arg_map.get('gran_period') == '0':
                if not arg_map.get('fileType') == 'A':
                    printLogs('File type ' + arg_map.get('fileType') + ' is not valid for granularity period ' + arg_map.get('gran_period') + '. Exiting process.', ERROR)
                arg_map["fileToBeAssembled"] = 'Small'
            else:
                arg_map["fileToBeAssembled"] = getFileSize(arg_map.get("fileToBeAssembled"))

            createGenstatsArgument()
        else:
            printLogs('Invalid node type. Exiting process.', ERROR)
    else:
        printLogs('Simulation name or Node name is not present in input argument.' + '\n' + 'Exiting process.', ERROR)


def change_arg_map(ne_category):
    global arg_map
    del arg_map['node_category']
    arg_map['node_category'] = ne_category


def process_minilink_outdoor_request():
    """ This method is responsible for ML outdoor and switch nodes, which generates filename and start and end date time.
    """
    global arg_map
    end_datetime = generate_end_date_time()
    command = 'date -d "' + end_datetime + ' -1 days"'
    start_datetime = run_shell_command(command).strip()
    arg_map['end_time'] = end_datetime
    arg_map['start_time'] = start_datetime
    formatted_start_datetime = convert_datetime_format(start_datetime)
    formatted_start_datetime = formatted_start_datetime[:-2] + '_' + formatted_start_datetime[-2:]
    formatted_end_datetime = convert_datetime_format(end_datetime)
    formatted_end_datetime = formatted_end_datetime[:-2] + '_' + formatted_end_datetime[-2:]
    a_filename, c_filename = create_outdoor_filename(formatted_start_datetime, formatted_end_datetime)
    createGenstatsArgument(a_filename, c_filename)


def create_outdoor_filename(start_date, end_date):
    """ This method generates A and C file name for ML Outdoor and Switch nodes.
    """
    global arg_map
    node_ip = arg_map['node_IP']
    long_ip = ''
    arg_map["userLabel"] = str(arg_map.get('node_name'))
    if '.' not in node_ip:
        long_ip = convert_ipv6_address(node_ip)
    else:
        long_ip = node_ip.replace('.','-')
    arg_map["localDn"] = node_ip.replace(':', '#').replace('.','-') + '_' + arg_map.get("userLabel")
    filename = start_date + '-' + end_date + '-PT-' + long_ip + '_' + arg_map.get("userLabel") + '_-_' + arg_map.get('rcID') + '.xml'
    printLogs('\nA type filename : A' + filename + '\nC type filename : C' + filename, INFO)
    return 'A' + filename, 'C' + filename


def generate_end_date_time():
    """ This method create end datetime by linux command
    """
    minute = trigger_date.split(':')[1]
    minute = str(15 - int(minute) % 15)
    seconds = trigger_date.split(':')[2].split()[0]
    command = 'date --d "' + trigger_date + ' +' + minute + ' min -' + seconds + ' sec"'
    end_date = run_shell_command(command).strip()
    return end_date


def convert_datetime_format(date_time):
    """ This method is responsible for changing format of datetime, which required in filename generation for Outdoor nodes.
    """
    command = 'date -d "' + date_time + '" +"%Y-%m-%dT%H_%M_00%z"'
    return run_shell_command(command).strip()


def convert_ipv6_address(ipAddress):
    """ This method will convert a given ipv6Address to its longform containing all 8 sets of 4 hexadecimal digits.
    """
    elements = ipAddress.split('::')
    padding_needed = (8 - len(elements[0].split(':')) - len(elements[1].split(':'))) * 4
    newIpAddress = ''
    for i in elements[0].split(':'):
        newIpAddress += i.upper().zfill(4)
    if padding_needed > 0:
        newIpAddress = newIpAddress + str(0)*padding_needed
    for i in elements[1].split(':'):
        newIpAddress += i.upper().zfill(4)
    return newIpAddress


def getAttributeValue(str_):
    """ This method acknowledge the input argument and based on that it will convert in generic argument for parameter like filename and gran period.
    Delete original parameter from map and save the value with generic name as a key in map.
    """
    attr = ''
    value = ''
    global arg_map
    if MINILINK_MO_TYPE == 'ETHERNET':
        if 'filename' == str_:
            attr = 'xfPMFileName'
        elif 'gran_period' == str_:
            attr = 'xfPMFileGranularityPeriod'
    elif MINILINK_MO_TYPE == 'SOAM':
        if 'filename' == str_:
            attr = 'xfServiceOamPmFileName'
        elif 'gran_period' == str_:
            attr = 'xfServiceOamPmFileGranularityPeriod'
    value = arg_map.get(attr)
    del arg_map[attr]
    return value


def createGenstatsArgument(a_filename='', c_filename=''):
    """ This method is responsible for creating arguments for genStats script for generation of Indoor, Switch and Outdoor nodes.
    Includes calling of genstats
    """
    script_argument = ''

    for arg_name, arg_value in arg_map.items():
        script_argument = script_argument + arg_name + '::' + arg_value + ';'

    if arg_map.get('node_category') == 'INDOOR':
        printLogs('Calling Genstats to generate Minilink PM files with below requested attribute value.', INFO)
        printLogs('File name : ' + arg_map.get('file_name'), INFO)
        printLogs('ROP period : ' + arg_map.get('gran_period'), INFO)
        printLogs('RC ID : ' + arg_map.get('rcID'), INFO)

        script_argument = '"' + script_argument[:-1] + '"'

        if arg_map.get('gran_period') == '2':
            script_argument = GENSTATS_SCRIPT + ' -r 1440 -l "' + arg_map.get('nodeType') + '" -n ' + script_argument
        elif arg_map.get('gran_period') == '1':
            script_argument = GENSTATS_SCRIPT + ' -r 15 -l "' + arg_map.get('nodeType') + '" -n ' + script_argument
        elif arg_map.get('gran_period') == '0':
            support_for_1_min_ML_1KB_filesize(arg_map.get('sim_name'), arg_map.get('node_name'), arg_map.get('file_name'))
            sys.exit(0)
        else:
            printLogs('Invalid value of Granularity period. Exiting process.', ERROR)

    elif arg_map.get('node_category') == 'OUTDOOR' or arg_map.get('node_category') == 'SWITCH':
        printLogs('Calling genstats to generate PM files for Minilink ' + arg_map.get('node_category').upper(), INFO)

        script_argument = GENSTATS_SCRIPT + ' -r 1440 -l "' + arg_map.get('nodeType') + '" -n ' + '"' + script_argument[:-1] + ';A_Filename::' + a_filename + ';C_Filename::' + c_filename + '"'

    script_argument = script_argument + ' >> ' + CONF_LOG_FILE
    subprocess.call(script_argument, shell=True)
    printLogs('File generation completed having process id : ' + process_id + '.\n', INFO)


def support_for_1_min_ML_1KB_filesize(simulation, node, file):
    """ This is a special method which generate ML outdoor nodes PM file of file size 1KB for only 1 minute ROP.
    """
    path = '/pms_tmpfs/' + simulation + '/' + node + '/c/pm_data/'
    if not os.path.isdir(path):
        os.system('mkdir -p ' + path)
    os.system('dd if=/dev/zero of=' + path + file + ' bs=1024 count=1')
    printLogs('File generation completed.', INFO)


def getEndInterval(file_name):
    """This method returns end date for ML indoor nodes by parsing filename whether it is A or C.
    """
    end_date = ""
    end_time = ""
    end_date_time = ""
    global arg_map
    start_date = file_name[1:][:8]
    start_time = file_name[10:][:4]
    start_offset = file_name[14:][:5]
    end_offset = file_name[24:][:5]
    arg_map["fileType"] = file_name[:1]

    if arg_map.get('fileType') == 'A':
        end_time = file_name[20:][:4]
        if start_time == end_time or int(end_time) < int(start_time):
            if start_offset == end_offset:
                end_date = datetime.datetime.strptime(start_date, "%Y%m%d") + datetime.timedelta(days=1)
                end_date = datetime.datetime.strftime(end_date, "%Y%m%d")
            else:
                end_date = start_date
        else:
            end_date = start_date
        end_date_time = end_date + "." + end_time + end_offset
    elif arg_map.get('fileType') == 'C':
        end_date_time = file_name[20:][:18]
    else:
        printLogs('Invalid file type.' + '\nExiting process.', ERROR)

    return end_date_time


def getIndexIdForFile(infile):
    """ Return index number for file after date-time value.
    """
    if infile.startswith('A'):
        return 30
    elif infile.startswith('C'):
        return 39
    else:
        printLogs('File name should start with "A" or "C". Here it is starting with "' + infile[:1] + '". Exiting process.', ERROR)


def setUserLableAndLocalDn(file_name):
    """ Set value of USER_LABLE and LOCAL_DN in arg_map {dict}
    """
    global arg_map
    node_info = filter(None, file_name[getIndexIdForFile(file_name):].split('_-_')[0].split('_'))
    if len(node_info) == 1:
        arg_map["userLabel"] = node_info[0]
        arg_map["localDn"] = '-'.join(node_info[0].split('-')[1:]) + '_'
    else:
        arg_map["userLabel"] = node_info[1]
        arg_map["localDn"] = '-'.join(node_info[0].split('-')[1:]) + '_' + node_info[1]


def getFileSize(_filesize):
    """ Take node family as input argument and determine the sample template based on it from SAMPLE_FILESIZE map.
    """
    default_filesize = "Small"
    for key, values in SAMPLE_FILESIZE.items():
        for value in values:
            if _filesize == value:
                printLogs(key + ' template size has been selected.', INFO)
                return key
    printLogs('Default template selected.', WARN)
    return default_filesize


def printLogs(msg, msg_type):
    """ Generic logging method, exit/terminate the script if msg_type is ERROR.
    """
    if msg_type == INFO:
        logging.info(msg)
    elif msg_type == WARN:
        logging.warning(msg)
    elif msg_type == ERROR:
        logging.error(msg)
        print(getCurrentDateTime() + ' ' + msg_type.upper() + ': ' + msg)
        sys.exit(1)
    print(getCurrentDateTime() + ' ' + msg_type.upper() + ': ' + msg)


trigger_date = run_shell_command('date').strip()


def main():
    """ Main method. Script initialization.
    """
    global process_id
    process_id = str(os.getpid())
    initialize_logger()
    printLogs('Starting execution with having process id : ' + process_id + '.', INFO)
    if os.path.isfile(GENSTATS_SCRIPT):
        printLogs('Collected arguments from Netsim trigger is : \n' + sys.argv[1], INFO)
        argument_parser(sys.argv[1])
    else:
        printLogs('Genstats scripts not found. Exiting process.', ERROR)


if __name__ == "__main__":
    main()

