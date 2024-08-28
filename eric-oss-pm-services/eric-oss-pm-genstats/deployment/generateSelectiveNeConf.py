#!/usr/bin/python

import sys
from getopt import getopt, GetoptError
from _collections import defaultdict

from utilityFunctions import Utility

util = Utility()

SUPPORTED_NE_LIST = ['R6672', 'R6675', 'SPITFIRE']

sim_name, rop_period, node_count, node_type, node_list = None, None, None, None, None
previous_config = defaultdict(lambda : defaultdict(lambda : defaultdict(lambda : defaultdict())))


def help_message():
    print ('\npython /netsim_users/auto_deploy/bin/generateSelectiveNeConf.py -s <sim_name> -r <rop_duration> -c <selective_node_count>\n\nOR\n\npython /netsim_users/auto_deploy/bin/generateSelectiveNeConf.py --sim <sim_name> --rop <rop_duration> --count <selective_node_count>')
    sys.exit()
    

def updateStoredInformation():
    global previous_config
    if sim_name in previous_config.keys():
        if node_type in previous_config[sim_name].keys():
            if rop_period in previous_config[sim_name][node_type].keys():
                del previous_config[sim_name][node_type][rop_period]


def storePreviousConfiguration():
    global previous_config
    selective_ne_obj = None
    try:
        selective_ne_obj = open(util.selective_ne_conf, 'r')
        for line in selective_ne_obj:
            line = line.split('\n')[0]
            line_element = line.split('|')
            ''' previous_config[sim_name][node_type][rop_period][node_count] = node_name_space_seperated '''
            previous_config[line_element[0]][line_element[1]][line_element[2]][line_element[3]] = line_element[4]
    except Exception as x:
        util.printStatements('Exception while reading configuration from ' + util.selective_ne_conf, 'ERROR', True)
        print (x)
    finally:
        selective_ne_obj.close()


def generateSelectiveNeConfigFile():
    selective_file_writer = None
    try:
        selective_file_writer = open(util.selective_ne_conf, 'w')
        for sim, c_map in previous_config.items():
            for ne_type, s_c_map in c_map.items():
                for rop, s_s_c_map in s_c_map.items():
                    for ne_count, ne_list in s_s_c_map.items():
                        selective_file_writer.write(sim + '|' + ne_type + '|' + rop + '|' + ne_count + '|' + ne_list + '\n')
        util.printStatements(util.selective_ne_conf + ' file has been updated successfully.', 'INFO') 
    except Exception as x:
        util.printStatements('Issue while writing ' + util.selective_ne_conf + ' file.', 'ERROR')
        print (x)
    finally:
        selective_file_writer.flush()
        selective_file_writer.close()


def modifySelectiveNeConfFile():
    global previous_config
    if util.checkFileExistance(util.selective_ne_conf):
        storePreviousConfiguration()
        if len(previous_config.keys()) > 0:
            updateStoredInformation()
    previous_config[sim_name][node_type][rop_period][node_count] = node_list
    generateSelectiveNeConfigFile()


def processInputInformation():
    global node_type, node_list
    if util.checkFileExistance(util.sim_info_file):
        node_type, status = util.fetchNodeTypeInformation(sim_name)
        if not status:
            util.printStatements('Can not produce selective node config file.', 'INFO', True)
    else:
        util.printStatements(util.sim_info_file + ' not present. Can not produce selective node config file.', 'ERROR', True)
    if node_type not in SUPPORTED_NE_LIST:
        util.printStatements('Node Type ' + node_type + ' not supported for Selective node configuration. Terminating process.', 'INFO', True)
    else:
        util.printStatements('Node Type ' + node_type + ' identified and it is supported for Selective FDN PM generation.', 'INFO')
    sim_dir_path = util.netsim_dbdir + sim_name + '/'
    node_list = util.fetchNeList(sim_dir_path)
    if len(node_list) == 0:
        util.printStatements('No nodes found in location : ' + sim_dir_path + '. No selective configuration changes needed.', 'WARNING', True)
    else:
        node_list.sort()
        if len(node_list) < int(node_count):
            util.printStatements('Input node count greater than actual no of nodes present in simulation. Setting selective node configuration for all nodes present in simulation ' + sim_name, 'WARNING')
        node_list = ' '.join(node_list[:int(node_count)])
        

def main(argv):
    global sim_name, rop_period, node_count
    
    try:
        opts, args = getopt(argv,'h:s:r:c:', ['help', 'sim=', 'rop=', 'count='])
    except GetoptError:
        help_message()

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            help_message()
        else:
            arg = arg.strip()
            if opt in ('-s', '--sim'):
                if not arg:
                    util.printStatements('Argument value can not be empty for param ' + opt, 'ERROR')
                    help_message()
                sim_name = arg
            elif opt in ('-r', '--rop'):
                if not arg:
                    util.printStatements('Argument value can not be empty for param ' + opt, 'ERROR')
                    help_message()
                if not arg.isdigit():
                    util.printStatements('Argument value must be Integer for param ' + opt, 'ERROR')
                    help_message()
                rop_period = arg
            elif opt in ('-c', '--count'):
                if not arg:
                    util.printStatements('Argument value can not be empty for param ' + opt, 'ERROR')
                    help_message()
                if not arg.isdigit():
                    util.printStatements('Argument value must be Integer for param ' + opt, 'ERROR')
                    help_message()
                if int(arg) <= 0:
                    util.printStatements('Argument value must be greater than 0 (Zero) for param ' + opt, 'ERROR')
                    help_message()
                node_count = arg
        
    if not sim_name or not rop_period or not node_count:
        util.printStatements('Script takes 3 arguments : sim_name, rop_period and node_count.', 'WARNING')
        help_message()
    
    processInputInformation()
    modifySelectiveNeConfFile()
    

if __name__ == '__main__':
    main(sys.argv[1:])

