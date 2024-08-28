#!/usr/bin/python

# Owner : xmanabh


import configparser
import json
import os.path
import random
import sys

input_ne_type = None

config_file = '/netsim_users/pms/etc/topology_config.ini'
result_dir = '/netsim_users/pms/etc/'

network_size = 0

config_dict = {}
cell_wise_ne_count = {}
format_map = {}

network_list = []

# Default ratio ==> 1: 0.45, 3: 0.35, 6: 0.10, 12: 0.10

SUPPORTED_TOPOLOGY_NES = ['GNODEBRADIO', 'LTE', 'GNODEBRADIO_EBSN']

cell_relation_map = {'GNBDUFunction': 'NRCellDU', 'GNBCUCPFunction': 'NRCellCU'}


def terminate_script(status):
    print('INFO : Terminating process.')
    sys.exit(status)


def help_message(status):
    print('INFO : Script calling structure...')
    print('python <script>.py <config_file> <output_folder>')
    terminate_script(status)


def validate_file(file, file_type='file'):
    if file_type == 'file':
        if os.path.isfile(file):
            return True
    elif file_type == 'dir':
        if os.path.isdir(file):
            return True
    return False


def process_cell_structure(input_map):
    try:
        global cell_wise_ne_count
        node_round_off, node_ratio = 0, 0
        cell_param = ''
        if input_ne_type == 'GNODEBRADIO':
            cell_param = 'nr_cell_structure'
        elif input_ne_type == 'GNODEBRADIO_EBSN':
            cell_param = 'nr_ebsn_cell_structure'
        elif input_ne_type == 'LTE':
            cell_param = 'lte_dg2_cell_structure'
        cell_type_list = [int(x.split(':')[0]) for x in str(input_map.get('cell_info', cell_param)).strip().split(',')]
        cell_type_list.sort()
        for value in str(input_map.get('cell_info', cell_param)).strip().split(','):
            value_ele = value.split(':')
            cell_type, ratio = int(value_ele[0]), ((float(value_ele[1]) * 1.0) / 100)
            if network_size > 0:
                node_ratio = network_size * ratio
            node_round_off += abs(node_ratio - int(node_ratio))
            node_count = int(node_ratio)
            cell_wise_ne_count[cell_type] = node_count
        cell_wise_ne_count[cell_type_list[0]] = (cell_wise_ne_count[cell_type_list[0]] + int(round(node_round_off)))
        for key, value in cell_wise_ne_count.items():
            print('INFO : Number of nodes ' + str(value) + ' has been created with ' + str(key) + ' cell structure.')
        return cell_param
    except Exception as e:
        print('ERROR : Issue while deriving ne count from cell ratio.')
        terminate_script(1)


def parse_configuration():
    try:
        global config_dict, format_map
        config_map = configparser.ConfigParser()
        config_map.read(config_file)
        # Capturing line formats
        format_param = ''
        if input_ne_type == 'GNODEBRADIO':
            format_param = 'nr_ne_to_cell_format'
        elif input_ne_type == 'GNODEBRADIO_EBSN':
            format_param = 'nr_ebsn_ne_to_cell_format'
        elif input_ne_type == 'LTE':
            format_param = 'lte_dg2_ne_to_cell_format'
        format_map[format_param] = (config_map.get('format', format_param)).strip()
        # Capturing cell_info section
        process_cell_structure(config_map)
        return format_param
    except Exception as e:
        print ('ERROR : Issue while loading configuration.')
        terminate_script(1)


def write_topology_information(info):
    file_name = result_dir
    try:
        if input_ne_type == 'GNODEBRADIO':
            file_name += 'nr_cell_data.txt'
        elif input_ne_type == 'GNODEBRADIO_EBSN':
            file_name += 'nr_ebsn_cell_data.txt'
        elif input_ne_type == 'LTE':
            file_name += 'eutrancellfdd_list.txt'
        with open(file_name, 'w') as out:
            for line in info:
                out.write(line)
    except Exception as e:
        print ('ERROR : Issue while writing topology information in file {}.'.format(file_name))
        terminate_script(1)


def produce_topology(format_param):
    try:
        '''
        NR =>  ManagedElement=NR01gNodeBRadio00001,GNBDUFunction=1,NRCellDU=NR01gNodeBRadio00001-1
                ManagedElement=NR01gNodeBRadio00001,GNBCUCPFunction=1,NRCellCU=NR01gNodeBRadio00001-1
        LTE => SubNetwork=NETSimW,MeContext=LTE01dg2ERBS00001,ManagedElement=LTE01dg2ERBS00001,ENodeBFunction=1,EUtranCellTDD=LTE01dg2ERBS00001-1
        NR_EBSN =>  ManagedElement=NR01EBSRadio00001,GNBDUFunction=1,NRCellDU=NR01EBSRadio00001-1
                ManagedElement=NR01EBSRadio00001,GNBCUCPFunction=1,NRCellCU=NR01EBSRadio00001-1
        '''
        topology_info = []
        line_format = format_map[format_param]
        sorted_cell_types = sorted(cell_wise_ne_count.keys())
        for cell_type in sorted_cell_types:
            for i in range(0, cell_wise_ne_count[cell_type]):
                ne_name = network_list.pop(0)
                '''
                sim_id = ''
                if input_ne_type == 'GNODEBRADIO':
                    sim_id = ne_name.split('gNodeBRadio')[0].replace('NR', '')
                elif input_ne_type == 'GNODEBRADIO_EBSN':
                    sim_id = ne_name.split('EBSRadio')[0].replace('NR', '')
                elif input_ne_type == 'LTE':
                    sim_id = ne_name.split('dg2ERBS')[0].replace('LTE', '')
                '''
                for j in range(1, cell_type + 1):
                    if input_ne_type == 'LTE':
                        line = line_format.replace('<dg2_ne_full_name>', ne_name).replace('<cell_sequence>', str(j))
                        topology_info.append(line + '\n')
                    elif input_ne_type in ['GNODEBRADIO', 'GNODEBRADIO_EBSN']:
                        for gnb_fun, cell_fun in cell_relation_map.items():
                            line = line_format.replace('<nr_ne_full_name>', ne_name).replace('<nr_gnb_function>',
                                                                                             gnb_fun).replace(
                                '<nr_cell_function>', cell_fun).replace('<cell_sequence>', str(j))
                            topology_info.append(line + '\n')
        topology_info.sort()
        write_topology_information(topology_info)
    except Exception as e:
        print ('ERROR : Issue while producing topology information.')
        terminate_script(1)


def correct_dir_path():
    global result_dir
    if not result_dir.endswith('/'):
        result_dir = result_dir + '/'


def read_network_information(json_file):
    global network_list, network_size
    try:
        with open(json_file, 'r') as f:
            json_object = json.load(f)
            if input_ne_type in json_object.keys():
                for l in json_object[input_ne_type]:
                    element = l.split('|')
                    network_list.append(element[1])
                network_size = len(network_list)
                random.shuffle(network_list)
            if network_size == 0:
                print('WARNING : No network found for ne type : {}'.format(input_ne_type))
                terminate_script(1)
    except Exception as e:
        print('ERROR : Issue parsing file: ' + json_file)
        terminate_script(1)


def main(args):
    if len(args) == 2:
        global input_ne_type
        if args[0] is not None and args[0].upper().strip() != '':
            global input_ne_type
            input_ne_type = args[0].upper().strip()
            if input_ne_type not in SUPPORTED_TOPOLOGY_NES:
                print('ERROR : Ne type {} is not supported for topology generation.'.format(input_ne_type))
                terminate_script(1)
        else:
            print('ERROR : Invalid ne type given.')
            terminate_script(1)
        if validate_file(args[1]):
            print('INFO : Starting process of topology generation for ne type : {}'.format(input_ne_type))
            network_info = args[1]
            read_network_information(network_info)
            produce_topology(parse_configuration())
            print ('INFO : Process completed.')
        else:
            print('ERROR : Please provide proper network file.')
            terminate_script(1)
    else:
        print('ERROR : 2 argument expected, given ' + str(len(args)))
        help_message(1)


if __name__ == '__main__':
    main(sys.argv[1:])
