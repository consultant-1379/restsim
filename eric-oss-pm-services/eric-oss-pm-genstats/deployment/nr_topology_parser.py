#!/usr/bin/python

'''
Owner : xmanabh
'''

import os.path
import sys
import configparser
import random
import json
from math import ceil
config_file = '/netsim_users/pms/etc/topology_config.ini'
config_json = '/etc/config/.simulated_network_enm_0.json'
result_dir = '/netsim_users/pms/etc/'
nodes_required = 0
network_size = 0

config_dict = {}
cell_wise_ne_count = {}
format_map = {}
network_list = []

static_map = {1: 1, 3: 10, 6: 17, 12: 19}
#             1: 0.45, 3: 0.35, 6: 0.10, 12: 0.10
nr_gnb_cell_rel_map = {'GNBDUFunction': 'NRCellDU', 'GNBCUCPFunction': 'NRCellCU'}


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
        print('INFO : Deriving ne count from cell ratio.')
        global cell_wise_ne_count, static_map
        sim_round_off = 0
        node_round_off = 0
        count = 0
        #cell_structure = 1:45,3:35,6:10,12:10
        cell_type_list = [int(x.split(':')[0]) for x in (input_map.get('cell_info', 'cell_structure')).strip().split(',')]
        cell_type_list.sort()
        for value in (input_map.get('cell_info', 'cell_structure')).strip().split(','):
            value_ele = value.split(':')
            cell_type, ratio = int(value_ele[0]), ((float(value_ele[1])*1.0)/100)
            node_ratio = network_size * ratio
            node_round_off += abs(node_ratio - int(node_ratio))
            node_count = int(node_ratio)
            cell_wise_ne_count[cell_type] = node_count
            #static_map[count] 
        cell_wise_ne_count[cell_type_list[0]] += int(round(node_round_off))
        print('INFO : Ne count has been derived.')
        for key, value in cell_wise_ne_count.items():
            print('INFO : Number of nodes ' + str(value) + ' has been created with ' + str(key) + ' cell structure.')
    except Exception as e:
        print('ERROR : Issue while deriving ne count from cell ratio.')
        terminate_script(1)


def parse_configuration():
    try:
        global config_dict, format_map
        config_map = configparser.ConfigParser()
        config_map.read(config_file)
        # Capturing line formats
        format_map['ne_to_cell_format'] = (config_map.get('format', 'ne_to_cell_format')).strip()
        # Capturing cell_info section
        process_cell_structure(config_map)
    except Exception as e:
        print ('ERROR : Issue while loading configuration.')
        terminate_script(1)


def write_topology_information(info):
    try:
        print ('INFO : Writing topology information.')
        result_file = result_dir + 'nr_cell_data.txt'
        with open(result_file, 'w') as out:
            for line in info:
                out.write(line)
        print ('INFO : Writing completed.')
    except Exception as e:
        print ('ERROR : Issue while writing topology information.')
        terminate_script(1)


def produce_topology():
    try:
        #ManagedElement=NR01gNodeBRadio00001,GNBDUFunction=1,NRCellDU=NR01gNodeBRadio00001-1
        #ManagedElement=NR01gNodeBRadio00001,GNBCUCPFunction=1,NRCellCU=NR01gNodeBRadio00001-1
        print ('INFO : Producing topology information...')
        line_format = format_map['ne_to_cell_format']
        #ne_start_index, ne_end_index = 1, config_dict['ne_per_sim']
        #sim_start_index = config_dict['sim_start_index']
        topology_info = []
        for cell_type in sorted(cell_wise_ne_count.keys()):
            for i in range(0, cell_wise_ne_count[cell_type]):
                ne_name = network_list.pop(0) 
                sim_id = ne_name.split('gNodeBRadio')[0].replace('NR','') 
                for j in range(1, cell_type+1):
                    for gnb_fun, cell_fun in nr_gnb_cell_rel_map.items():
                        line = line_format.replace('<nr_ne_full_name>', ne_name).replace('<nr_gnb_function>', gnb_fun) \
                             .replace('<nr_cell_function>', cell_fun).replace('<cell_sequence>', str(j))
                        topology_info.append(line + '\n')
        print ('INFO : Topology information has been produced.')
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
            if 'GNODEBRADIO' in json_object.keys():
                for l in json_object['GNODEBRADIO']:
                    element = l.split('|')
                    network_list.append(element[1])
                network_size = len(network_list)
                random.shuffle(network_list)
            if network_size == 0:
                print('WARNING : No GNODEBRADIO found.')
                terminate_script(1)
    except Exception as e:
        print('ERROR : Issue parsing file: ' + json_file)
        terminate_script(1)

def main(args):
    print ('INFO : Initiating process for NR Cell Mapping...')
    if len(args) == 1:
        if validate_file(args[0]):
            network_info = args[0]
            print ('INFO : Reading network info from file: ' + network_info)
            read_network_information(network_info)
            print ('INFO : Reading network info complete.')
            parse_configuration()
            produce_topology()
            print ('INFO : Process completed.')
        else:
            print('ERROR : Either provided config file or output dir invalid')
            terminate_script(1)
    else:
        print('ERROR : 2 argument expected, given ' + str(len(args)))
        help_message(1)


if __name__ == '__main__':
    ''' config_location = W:/pythonProjects/config/topologyConfig.ini '''
    main(sys.argv[1:])

