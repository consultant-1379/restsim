#!/usr/bin/python -u

'''
Created on July 21 , 2023

@author: xmanabh
'''

import getopt
import json
import os
import shutil
import sys
from datetime import datetime
from datetime import timedelta
from os import remove
from time import sleep, time

from fileNamingMetadata import FileNamingMetadata

metadata = FileNamingMetadata()

PM_FILE_MODE = 'default'
FLS_SERVICE_PORT = '8080'

DEBUG_MODE = False

PMIC_PATH = '/ericsson/pmic/'
REQUEST_LOOKUP_PATH = '/netsim_users/pms/config/requests/'
JSON_FILE_DIR = '/netsim_users/pms/config/json/'
TOUCH_FILE_PATH = '/netsim_users/pms/config/touch_files/'
NETSIM_CFG = '/netsim/netsim_cfg'

DB_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
LOG_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
EPOCH_DIR_NAMING = '<START_EPOCH>_<END_EPOCH>'
JSON_DIR_NAMING = '<START_EPOCH>|<END_EPOCH>,<PM_TYPES>.json'

PM_STATISTICAL, PM_CELLTRACE = 'PM_STATISTICAL', 'PM_CELLTRACE'

# NR Celltrace
PM_CELLTRACE_DU, PM_CELLTRACE_CUCP, PM_CELLTRACE_CUUP = 'PM_CELLTRACE_DU', 'PM_CELLTRACE_CUCP', 'PM_CELLTRACE_CUUP'
NR_CELLTRACE_NF_LIST = [PM_CELLTRACE_CUUP, PM_CELLTRACE_CUCP, PM_CELLTRACE_DU]

# NR Stats when EBS-N/REPLAY
NR_PM_EBSN_LIST = ['PM_EBSN_CUUP', 'PM_EBSN_CUCP', 'PM_EBSN_DU']

LOOK_UP_PATHS = []

LOOK_UP_WAIT_TIME = 600

ROP_IN_SEC = 900

PM_FILE_EXT = ['gpb.gz', '.xml.gz', '.bin.gz', '.gz', '.xml', '.bin']

RADIO_NODE, RADIO, LTE_DG2, LTE_ERBS, NR, NRAT, PCC, PCG, vDU, vCU_CP, vCU_UP = 'RadioNode', 'RADIO', 'LTE_DG2', 'LTE_ERBS', 'NR', 'NRAT', 'PCC', 'PCG', 'Shared-CNF', 'Shared-CNF', 'Shared-CNF'

FLS_JAR_CALL_STATEMENT = 'java -jar /netsim_users/pms/lib/fls-updator-service.jar "<operation>" "<file_path>" "eric-oss-fls-enm-<PM_POD_ID>" ' + FLS_SERVICE_PORT

WAIT_FOR_PM_GENERATION_IN_SEC = 8 * 60


def log_statement(msg):
    print(get_current_date_time() + msg)


def get_current_date_time():
    return datetime.now().strftime(LOG_TIME_FORMAT) + ' '


def get_host_name_id():
    import socket
    return str(socket.gethostname().split('-')[-2])


def add_entry_in_database(json_file_path):
    call_statement = FLS_JAR_CALL_STATEMENT.replace('<operation>', 'add').replace('<file_path>',
                                                                                  json_file_path).replace('<PM_POD_ID>',
                                                                                                          get_host_name_id())
    log_statement('INFO : Transferring json entries to fls db...')
    try:
        os.system(call_statement)
        #move json file to json_file_done
        os.system('mv "' + json_file_path + '" "' + json_file_path + '_done"')
        log_statement('INFO : Json entries transferred complete.')
    except Exception as e:
        log_statement('ERROR : Issue while calling fls jar.')


def get_requests_files():
    return_req_list = []
    future_found = False
    for x in filter(None, os.listdir(REQUEST_LOOKUP_PATH)):
        if 'FUTURE' in x:
            future_found = True
        file_path = REQUEST_LOOKUP_PATH + x
        if os.path.isfile(file_path):
            return_req_list.append(file_path)
    if future_found:
        return_req_list = [a for a in return_req_list if 'FUTURE' in a]
    return return_req_list


def get_system_time():
    return int(time())


def identify_file_data_type(name):
    data_type = None
    if name.endswith('.xml.gz') or name.endswith('.xml'):
        data_type = PM_STATISTICAL
    elif name.endswith('.bin') or name.endswith('.bin.gz'):
        data_type = PM_CELLTRACE
    elif name.endswith('.gpb') or name.endswith('.gpb.gz'):
        str = name.split(',')[-1].split('_')[1]
        for x in ['CUCP', 'CUUP', 'DU']:
            if str.startswith(x):
                data_type = PM_CELLTRACE + '_' + x
                break
    return data_type


def identify_node_information(data_type, file_name):
    node, node_type, node_name, nf = None, None, None, None
    managed_element = file_name.split(',')[-1].split('=')[-1]
    if data_type == PM_STATISTICAL:
        if 'LTE' in managed_element:
            if 'dg2ERBS' in managed_element:
                node, node_type = LTE_DG2, RADIO_NODE
        if 'L2B' in managed_element:
            node, node_type = LTE_ERBS, RADIO_NODE
        elif 'gNodeBRadio' in managed_element:
            node, node_type = NR, RADIO_NODE
        elif 'PCC' in managed_element:
            node, node_type = PCC, PCC
        elif 'PCG' in managed_element:
            node, node_type = PCG, PCG
        elif 'vDU' in managed_element:
            node, node_type = vDU, vDU
        elif 'vCU-CP' in managed_element:
            node, node_type = vCU_CP, vCU_CP
        elif 'vCU-UP' in managed_element:
            node, node_type = vCU_UP, vCU_UP
        node_name = '_'.join(file_name.replace('_statsfile', '').split('_')[1:]).split('.')[0]
    elif data_type == PM_CELLTRACE:
        if 'LTE' in managed_element:
            if 'dg2ERBS' in managed_element:
                node_name = file_name.split('_')[2]
                node, node_type = LTE_DG2, RADIO_NODE
        pass
    elif data_type in NR_CELLTRACE_NF_LIST:
        # Only NR applicable here
        node_name = file_name.split('_')[2]
        node, node_type = NR, RADIO_NODE
    return node, node_type, node_name


def get_file_time_stamp_parsing_map(node, data_type):
    if node == NR:
        if data_type == PM_STATISTICAL or data_type in NR_PM_EBSN_LIST:
            return metadata.NR_STATS_FILE_METADATA
        if data_type in NR_CELLTRACE_NF_LIST:
            return metadata.NR_CELLTRACE_FILE_METADATA
    elif node in [LTE_ERBS, LTE_DG2]:
        if data_type == PM_STATISTICAL:
            return metadata.LTE_DG2_STATS_FILE_METADATA
        if data_type == PM_CELLTRACE:
            return metadata.LTE_DG2_CELLTRACE_FILE_METADATA
    elif node in [PCC, PCG, vDU, vCU_UP, vCU_UP]:
        return metadata.PCC_STATS_FILE_METADATA
    return None


def get_file_time_stamp_parameters(file_path, file_name, node, data_type):
    file_creation_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime(DB_TIME_FORMAT)
    file_size, file_type = os.path.getsize(file_path), file_name.split('.')[-1]
    ne_map = get_file_time_stamp_parsing_map(node, data_type)

    if ne_map is None:
        log_statement('ERROR : Invalid node or data type for which no time stamp parser found.')
        return None, None, None, None, None

    start_year = int(file_name[ne_map['START_YEAR_START']:ne_map['START_YEAR_END']])
    start_month = int(file_name[ne_map['START_MONTH_START']:ne_map['START_MONTH_END']])
    start_date = int(file_name[ne_map['START_DATE_START']:ne_map['START_DATE_END']])
    start_hour = int(file_name[ne_map['START_HOUR_START']:ne_map['START_HOUR_END']])
    start_min = int(file_name[ne_map['START_MIN_START']:ne_map['START_MIN_END']])

    start_time = datetime(start_year, start_month, start_date, start_hour, start_min)
    end_time = start_time + timedelta(seconds=ROP_IN_SEC)

    return file_creation_time, start_time.strftime(DB_TIME_FORMAT), end_time.strftime(
        DB_TIME_FORMAT), file_size, file_type


def create_map_structure(id, node_name, node_type, file_location, file_creation_time_in_oss, data_type, file_type,
                         start_rop_time_in_oss, end_rop_time_in_oss, file_size):
    return {'id': id, 'nodeName': node_name, 'nodeType': node_type, 'fileLocation': file_location, \
            'fileCreationTimeInOss': file_creation_time_in_oss, 'dataType': data_type, 'fileType': file_type, \
            'startRopTimeInOss': start_rop_time_in_oss, 'endRopTimeInOss': end_rop_time_in_oss, 'fileSize': file_size}


def verify_ebs_n_replay_use_case(full_path_dir):
    data_type = PM_STATISTICAL
    sub_dir = [x for x in filter(None, full_path_dir.split('/'))][-2]
    if sub_dir.startswith('NR_EBSN_'):
        net_fun = sub_dir.split('_')[-1]
        for x in NR_PM_EBSN_LIST:
            if net_fun in x:
                data_type = x
                break
    return data_type


def write_metadata_info_in_json(info_list, file_name):
    temp_json_file_name = file_name + '_writing'
    try:
        log_statement('INFO : Writing metadata information in {} file.'.format(temp_json_file_name))
        with open(temp_json_file_name, 'w') as json_file:
            json.dump(info_list, json_file)
            json_file.flush()
            log_statement(
                'INFO : Json file {} created successfully for {} files.'.format(temp_json_file_name, len(info_list)))
    except Exception as e:
        log_statement('ERROR : Issue while writing information in json file {}'.format(temp_json_file_name))
        return
    try:
        if os.path.exists(temp_json_file_name) and os.path.isfile(temp_json_file_name):
            shutil.move(temp_json_file_name, file_name)
            log_statement('INFO : Json file moved from {} to {} successfully.'.format(temp_json_file_name, file_name))
    except Exception as e:
        log_statement('ERROR : Issue while renaming file from {} to {}.'.format(temp_json_file_name, file_name))


def process_look_up_dirs(dir_list, json_name):
    file_param_map_list = []
    for pm_path in dir_list:
        if not os.path.exists(pm_path) or not os.path.isdir(pm_path):
            if DEBUG_MODE:
                log_statement('WARNING : Either dir {} is not a directory or does not exists.'.format(pm_path))
            continue
        if DEBUG_MODE:
            log_statement('INFO : Fetching file metadata information for directory {}.'.format(pm_path))
        for pm_file in filter(None, os.listdir(pm_path)):
            pm_file_path = pm_path + '/' + pm_file
            if any(pm_file.endswith(ext) for ext in PM_FILE_EXT):
                data_type = identify_file_data_type(pm_file)
                node, node_type, node_name = identify_node_information(data_type, pm_file)
                if node == NR and data_type == PM_STATISTICAL:
                    data_type = verify_ebs_n_replay_use_case(pm_path)
                file_creation_time_in_oss, start_rop_time_in_oss, end_rop_time_in_oss, file_size, file_type = get_file_time_stamp_parameters(
                    pm_file_path, pm_file, node, data_type)
                file_param_map = create_map_structure('null', node_name, node_type, pm_file_path,
                                                      file_creation_time_in_oss, data_type, file_type,
                                                      start_rop_time_in_oss, end_rop_time_in_oss, file_size)
                file_param_map_list.append(file_param_map)
    write_metadata_info_in_json(file_param_map_list, json_name)
    add_entry_in_database(json_name)


def is_directory(path):
    if os.path.isdir(path):
        return True
    return False


def is_exists(path):
    if os.path.exists(path):
        return True
    return False


def wait_for_touch_file(req_pm_type_list, epoch):
    touch_pm_type_list = []
    for i in range(0, WAIT_FOR_PM_GENERATION_IN_SEC):
        tmp_list = lookup_touch_files(epoch)
        tmp_list = [j for j in tmp_list if j in req_pm_type_list]
        touch_pm_type_list.extend(tmp_list)
        touch_pm_type_list = sorted(list(set(touch_pm_type_list)))
        if touch_pm_type_list == req_pm_type_list:
            break
        else:
            sleep(1)
    return touch_pm_type_list


def process_request_parameters(req):
    log_statement('INFO : Processing request {}.'.format(req))
    req_file_name = os.path.basename(req)
    epoch_param_str, pm_type_str = req_file_name.split(',')
    epoch_dir_ele, req_pm_type_list = epoch_param_str.split('|'), pm_type_str.split('|')
    req_pm_type_list.sort()
    log_statement('INFO : Found request pm types [{}]'.format(', '.join(req_pm_type_list)))
    touch_pm_type_list = wait_for_touch_file(req_pm_type_list, int(epoch_dir_ele[0]))
    log_statement('INFO : Found generated pm types [{}]'.format(', '.join(touch_pm_type_list)))
    if len(touch_pm_type_list) == 0:
        log_statement(
            'ERROR : No touch file found at {} for epoch {}. May be issue with data generation.'.format(TOUCH_FILE_PATH,
                                                                                                        epoch_dir_ele[
                                                                                                            0]))
        return
    epoch_dir_name = generate_epoch_dir_name(epoch_dir_ele[0], epoch_dir_ele[1])
    json_name = generate_json_file_name(epoch_dir_ele[0], epoch_dir_ele[1], pm_type_str.split('|'))
    dir_list = []
    for pm_type_dir in touch_pm_type_list:
        pm_type_full_dir = PMIC_PATH + pm_type_dir
        if not is_exists(pm_type_full_dir) or not is_directory(pm_type_full_dir):
            log_statement('ERROR : Either path {} does not exists or not a directory.'.format(pm_type_full_dir))
            continue
        for node_dir in filter(None, os.listdir(pm_type_full_dir)):
            epoch_full_path_dir = pm_type_full_dir + '/' + node_dir + '/' + epoch_dir_name
            if not is_exists(epoch_full_path_dir) or not is_directory(epoch_full_path_dir):
                log_statement('WARNING : Either path {} does not exists or not a directory. Perhaps Node {} has not been started.'.format(epoch_full_path_dir, node_dir))
                continue
            dir_list.append(epoch_full_path_dir)
    process_look_up_dirs(dir_list, json_name)
    log_statement('INFO : Request {} processed.'.format(req))


def delete_request(req):
    log_statement('INFO : Deleting request {}.'.format(req))
    try:
        if os.path.exists(req):
            remove(req)
            log_statement('INFO : Request file {} deleted successfully.'.format(req))
        else:
            log_statement('ERROR : Unable to find request files {}  for deletion.'.format(req))
    except Exception as e:
        log_statement('ERROR : Exception while removing request file {}.'.format(req))


def look_up_on_demand_request_path():
    while True:
        requests_list = get_requests_files()
        if len(requests_list) > 0:
            requests_list.sort(key=os.path.getctime)
            log_statement(
                'INFO : Found Request(s) [{}] at location {}.'.format(', '.join(requests_list), REQUEST_LOOKUP_PATH))
            for request in requests_list:
                delete_request(request)
                process_request_parameters(request)
        else:
            if DEBUG_MODE:
                log_statement('INFO : No request found at {} to process.'.format(REQUEST_LOOKUP_PATH))
        sleep(1)


def get_all_dirs(pm_type_list):
    node_dir_list = []
    for pm_type_dir in pm_type_list:
        full_pm_type_path = PMIC_PATH + pm_type_dir
        if is_exists(full_pm_type_path) and is_directory(full_pm_type_path):
            node_dir_list.extend([full_pm_type_path + '/' + node_dir for node_dir in
                                  filter(None, os.listdir(full_pm_type_path))])
        else:
            log_statement('WARNING : Either location {} does not exists or not a directory.'.format(full_pm_type_path))
    return node_dir_list


def generate_json_file_name(start, end, pm_type_list):
    return JSON_FILE_DIR + JSON_DIR_NAMING.replace('<START_EPOCH>', str(start)).replace('<END_EPOCH>',
                                                                                        str(end)).replace('<PM_TYPES>',
                                                                                                          '|'.join(
                                                                                                              pm_type_list))


def generate_epoch_dir_name(start, end):
    return EPOCH_DIR_NAMING.replace('<START_EPOCH>', str(start)).replace('<END_EPOCH>', str(end))


def generate_epoch_dir_list(epoch_dir, dir_list):
    return [dir + '/' + epoch_dir for dir in dir_list]


def lookup_touch_files(epoch):
    pm_type_list = []
    for touch_file in filter(None, os.listdir(TOUCH_FILE_PATH)):
        full_touch_file_path = TOUCH_FILE_PATH + touch_file
        if touch_file.startswith(str(epoch)):
            for pm_type in touch_file.split(',')[-1].split('|'):
                pm_type_list.append(pm_type)
            if PM_FILE_MODE == 'default':
                '''
                Remove generated pm touch file only in default mode.
                In on_demand user can trigger request multiple times in single 15 minute intervale
                '''
                os.remove(full_touch_file_path)
    return pm_type_list


def get_rounded_epoch(rop_time):
    curr_epoch = get_system_time()
    return int(curr_epoch / rop_time) * rop_time


def run_for_start_up(start_epoch):
    end_epoch = start_epoch + ROP_IN_SEC
    pm_type_dir_list = lookup_touch_files(start_epoch)
    if len(pm_type_dir_list) == 0:
        return
    else:
        log_statement('INFO : PM touch file(s) [{}] found and processing.'.format(', '.join(pm_type_dir_list)))
    node_dir_list = get_all_dirs(pm_type_dir_list)
    json_name = generate_json_file_name(start_epoch, end_epoch, pm_type_dir_list)
    epoch_dir_name = generate_epoch_dir_name(start_epoch, end_epoch)
    epoch_dir_list = generate_epoch_dir_list(epoch_dir_name, node_dir_list)
    process_look_up_dirs(epoch_dir_list, json_name)


def get_debug_mode_value(check_epoch=True):
    global DEBUG_MODE
    if check_epoch:
        current_epoch = get_system_time()
        if current_epoch % 5 == 0:
            check_epoch = False
    if not check_epoch:
        if not is_exists(NETSIM_CFG) or not os.path.isfile(NETSIM_CFG):
            return
        with open(NETSIM_CFG, 'r') as cfg:
            for line in cfg:
                if line.startswith('FILE_METADATA_DEBUG='):
                    if line.split('"')[1].upper().strip() == 'ON':
                        DEBUG_MODE = True
                    break


def initiate_process(start_epoch):
    log_statement('INFO : File Metadata finding service started.')
    get_debug_mode_value(False)
    if start_epoch is None:
        start_epoch = get_rounded_epoch(ROP_IN_SEC)
    else:
        run_for_start_up(start_epoch)
        start_epoch += ROP_IN_SEC
    if PM_FILE_MODE == 'on_demand':
        look_up_on_demand_request_path()
    elif PM_FILE_MODE == 'default':
        while True:
            get_debug_mode_value()
            if start_epoch <= get_system_time() < (start_epoch + ROP_IN_SEC):
                run_for_start_up(start_epoch)
            if get_system_time() >= (start_epoch + ROP_IN_SEC):
                start_epoch += ROP_IN_SEC
            sleep(1)


def help_message():
    print('INFO : Script Usage as below.')
    # For Start up
    print('USAGE : python <script>.py -m on_demand -e <epoch_value>')
    print('USAGE : python <script>.py -m default -e <epoch_value> OR python <script>.py -e <epoch_value>')
    # Other use case with-out loading first pm metadata
    print('USAGE : python <script>.py -m on_demand')
    print('USAGE : python <script>.py -m default OR python <script>.py')
    sys.exit(1)


def main(arguments):
    global PM_FILE_MODE

    try:
        opts, args = getopt.getopt(arguments, 'h:m:e:', ['help', 'mode=', 'epoch='])
    except getopt.GetoptError:
        log_statement('ERROR : Invalid arguments given.')
        help_message()

    start_epoch = None

    for opt, arg in opts:
        arg = arg.replace(' ', '').lower()
        if opt in ("-h", "--help"):
            help_message()
        elif opt in ("-m", "--mode"):
            if arg == 'on_demand':
                PM_FILE_MODE = arg
            elif arg == 'default':
                pass
            else:
                log_statement('ERROR : Invalid mode given.')
                help_message()
        elif opt in ("-e", "--epoch"):
            if arg.isdigit():
                start_epoch = int(arg)
            else:
                log_statement('ERROR : Invalid mode given.')
                help_message()
    initiate_process(start_epoch)


if __name__ == '__main__':
    main(sys.argv[1:])
