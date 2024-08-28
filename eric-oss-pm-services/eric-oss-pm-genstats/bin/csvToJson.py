#!/usr/bin/python -u

# Created on October 9, 23 by @xmanabh

import csv
import json
import os.path
import sys
from collections import defaultdict

json_path = '/netsim_users/pms/config/pm_config/'

XML, XML_GZ, MEAS_OBJ = '.xml', '.xml.gz', 'ManagedElement='
COLON = ':'

SUPPORTED_NE_LIST = ['EBSN_REPLAY']

final_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict())))


def terminate_script(status=0):
    sys.exit(status)


def validate_and_refactor_csv(csv_obj):
    file_data, is_first_line = '', True
    try:
        print('INFO : Validating and Refactoring file...')
        for line in csv_obj:
            check_line = line.replace('\n', '').replace(' ', '').replace(',', '')
            if check_line is None or check_line == '':
                continue
            else:
                if is_first_line:
                    is_first_line = False
                    if 'filename' in line.lower():
                        print('INFO : Ignored first line header content.')
                        continue
                line = line.replace('\n', '').rstrip(',')
                file_data += line + '\n'
        print('INFO : Validation and Refactoring of file completed.')
    except Exception as e:
        print('ERROR : Issue while validating csv file.')
        print(e)
        terminate_script(1)
    return file_data


def import_csv_in_module(csv_str):
    csv_reader = None
    print('INFO : Importing csv file data...')
    try:
        csv_reader = csv.reader(csv_str.split('\n'), delimiter=',')
        print('INFO : Import complete.')
    except Exception as e:
        print('ERROR : Issue while importing csv data. Terminating csv conversion process.')
        print(e)
        terminate_script(1)
    return csv_reader


def process_csv_information(csv_obj):
    global final_dict
    file_name, meas_obj, pm_counter_name = '', '', ''
    taking_counter_value, flag_enabled = False, True
    begin_time_list = []
    try:
        print('INFO : Converting csv information in JSON format...')
        for row in csv_obj:
            for r_index, r_ele in enumerate(row):
                if r_index == 0:
                    if r_ele.endswith(XML_GZ) or r_ele.endswith(XML):
                        fdn_name = '_'.join(r_ele.split('_')[1:]).replace(XML_GZ, '').replace(XML, '')
                        flag_enabled = True
                elif r_index == 1:
                    if flag_enabled:
                        if not r_ele.strip().startswith(MEAS_OBJ):
                            print('WARNING : Meas Obj not found in second position for file name {}.'.format(fdn_name))
                            terminate_script(1)
                        else:
                            flag_enabled = False
                    if MEAS_OBJ in r_ele:
                        meas_obj = r_ele
                        if len(row) < 3:
                            if len(begin_time_list) == 0:
                                print(
                                    'WARNING : Begin Time value not found in starting of file. Terminating conversion process.')
                                terminate_script(1)
                        else:
                            taking_counter_value = False
                            begin_time_list = []
                    else:
                        pm_counter_name = r_ele
                        taking_counter_value = True
                elif r_index >= 2:
                    if not taking_counter_value:  # This is where we will consume begin time
                        offset_splitter = '+'
                        if '-' in r_ele:
                            offset_splitter = '-'
                        time_element = ''.join(r_ele.split(offset_splitter)[0].split(COLON)[:2])
                        offset_element = ''.join(r_ele.split(offset_splitter)[1].split(COLON))
                        begin_time_list.append(time_element + offset_splitter + offset_element)
                    else:
                        if (r_index - 2) < len(begin_time_list):
                            if fdn_name != '' and meas_obj != '' and len(begin_time_list) > 0:
                                if r_ele is not None and r_ele != '':
                                    final_dict[fdn_name][meas_obj][begin_time_list[r_index - 2]][
                                        pm_counter_name] = r_ele
                        else:
                            print(
                                'WARNING : Ignoring counter value for counter name {} with meas obj {} for file {} as it does not have begin time association.'.format(
                                    pm_counter_name, meas_obj, fdn_name))
                            break
        print('INFO : Conversion completed.')
    except Exception as e:
        print('ERROR : Issue while doing conversion from csv to JSON.')
        terminate_script(1)


def write_data_in_json_file(file_name):
    if not os.path.exists(json_path) or not os.path.isdir(json_path):
        print('INFO : Creating path {}.'.format(json_path))
        try:
            os.makedirs(json_path, 0o755)
            print('INFO : Directory {} created successfully.'.format(json_path))
        except Exception as e:
            print('ERROR : Issue while creating path {}.'.format(json_path))
            terminate_script(1)
    json_file_name = json_path + file_name
    try:
        print('INFO : Writing JSON information in file {}'.format(json_file_name))
        with open(json_file_name, 'w') as jsonf:
            json.dump(final_dict, jsonf, indent=2)
            jsonf.flush()
            print('INFO : Writing JSON information compeleted.')
    except Exception as e:
        print('ERROR : Issue while writing JSON information in file {}.'.format(json_file_name))
        terminate_script(1)


def parse_csv_for_ebsn_replay(csv_file):
    if os.path.exists(csv_file) and os.path.isfile(csv_file):
        print('INFO : Processing csv file {} for EBSN REPLAY'.format(csv_file))
        try:
            with open(csv_file, 'r') as csvf:
                csv_file_data_str = validate_and_refactor_csv(csvf)
                if csv_file_data_str is None or csv_file_data_str == '':
                    print('WARNING : No content found after refactoring. Terminating csv conversion process.')
                    terminate_script(1)
                csv_reader = import_csv_in_module(csv_file_data_str)
                if csv_reader is not None:
                    process_csv_information(csv_reader)
                else:
                    print(
                        'WARNING : None object received while importing csv data. Terminating csv conversion process.')
                    terminate_script(1)
        except Exception as e:
            print('ERROR : Issue while reading file {}.'.format(csv_file))
            terminate_script(1)
        if len(final_dict.keys()) > 0:
            write_data_in_json_file('ebsn_replay_counter_info.json_bkp')
        else:
            print(
                'WARNING : No useful information found in file {}. Process will skip counter info json file switching.'.format(
                    csv_file))
    else:
        print('ERROR : Csv file {} does not exists.'.format(csv_file))
        terminate_script(1)


def main(args):
    '''
    :param args: ne_type (str), csv_file (str)
    :return: status of execution (int)
    '''
    if args[0] in SUPPORTED_NE_LIST:
        if args[0] == 'EBSN_REPLAY':
            print('INFO : Processing csv information for EBSN REPLAY.')
            parse_csv_for_ebsn_replay(args[1])
            print('INFO : Csv information processed for EBSN REPLAY.')
    else:
        print('ERROR : Invalid node type {} given.'.format(args[0]))
        terminate_script(1)
    terminate_script(0)


if __name__ == '__main__':
    main(sys.argv[1:])

