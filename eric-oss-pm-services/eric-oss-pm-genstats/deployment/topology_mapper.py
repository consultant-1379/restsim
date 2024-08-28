#!/usr/bin/python
################################################################################
# COPYRIGHT Ericsson 2021
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS-21.06
# Purpose       :  Script maps the stats file with topology data 
# Jira No       :  NSS-34210
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/9256907/
# Description   :  Adding support for DO simulation SGSN node
# Date          :  03/03/2021
# Last Modified :  manali.singh@tcs.com
####################################################


import sys
import os
import json
import getopt
from shutil import copy, move


DO_SUPPORTED_NODE_TYPES=['SGSN']
TOPOLOGY_DATA_DIR="/netsim_users/pms/etc/topology_info/"
CONFIG_JSON="/netsim_users/pms/etc/node_template_map/topology_config.json"


def create_mo_config_list():
    """load config json file and create required MO list to be mapped"""
    global config_mo_list
    config_mo_list = []
    with open(CONFIG_JSON) as config_json:
        config_node_mo_dict = json.load(config_json)
    if node_type in config_node_mo_dict:
        config_mo_list = config_node_mo_dict[node_type]
    else:
        print "ERROR : No configuration found for " + node_type + " in file : " + CONFIG_JSON + \
              "for " + sim_name  + " :: " + node_name


def create_topology_dict():
    """load parsed topology JSON file and create Node to MO dictionary"""
    global node_topology_dict
    with open(topology_json_file) as json_file:
        topology_dict = json.load(json_file)
    if node_name in topology_dict:
        node_topology_dict = topology_dict[node_name]
    else:
        print "ERROR : No configuration found for sim : " + sim_name + " : node name : "+ node_name + \
              " in file : " + topology_json_file  
        sys.exit(1)

def update_template():
    """update xml template file for the node"""
    tmp_template_file=template_file + "_tmp"
    with open(tmp_template_file, 'w') as out_file:
        with open(template_file, 'r') as in_file:
            for line in in_file:
                if line.strip().startswith("<measValue measObjLdn="):
                    line_element=line.replace('\n', '').split(',')
                    mo_key=line_element[-1].split('=')[0]
                    if mo_key in node_topology_dict and mo_key in config_mo_list:
                        line=""
                        for element in line_element:
                            mo_name=element.split('=')[0]
                            if mo_name in node_topology_dict[mo_key]:
                                line += mo_name + '=' + node_topology_dict[mo_key][mo_name].pop(0) + ','
                            else:
                                line += element + ','
                        line = line.rstrip(',') +  '">\n'
                out_file.write(line)
                out_file.flush()
    if os.path.isfile(tmp_template_file):
        os.remove(template_file)
        move(tmp_template_file, template_file)
    else:
        print "ERROR : Issue while creation of mapped template file : " + template_file + "for " + \
              " SIM : " + sim_name + " node name : " + node_name

def usage ():
    """Script usage"""
    print "python topology_mapper.py -t <node_type> -n <node_name> -s <sim_name> -f <template_file>"

def main(argv):
    """Main Method"""
    global node_type, sim_name, node_name, template_file, topology_json_file
    try:
        opts, args = getopt.getopt(sys.argv[1:], 't:n:s:f:h', ['node_type=', 'node_name=',
                                                              'sim_name=', 'template_file=', 'help'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-t', '--node_type'):
            node_type = arg
        elif opt in ('-n', '--node_name'):
            node_name = arg
        elif opt in ('-s', '--sim_name'):
            sim_name = arg
        elif opt in ('-f', '--template_file'):
            template_file = arg
        elif opt in ('-h', '--help'):
            usage();
            sys.exit()
        else:
            usage()
            sys.exit(2)

    if node_type in DO_SUPPORTED_NODE_TYPES:
        if os.path.isfile(template_file):
            if os.path.isfile(CONFIG_JSON):
                create_mo_config_list()
                topology_json_file = TOPOLOGY_DATA_DIR + sim_name + '.json'
                if os.path.isfile(topology_json_file):
                    create_topology_dict()
                    update_template()
                else :
                    print "ERROR : " + topology_json_file + " not present for topology mapping!!"
                    sys.exit(1)
            else:
                print "WARNING : " + CONFIG_JSON + " not present for topology mapping!! No topology mapping will " \
                                                   "be done !!"
                sys.exit(1)
        else:
            print "ERROR : " + template_file + " not present for topology mapping for sim : " + sim_name + \
                  " node name : " + node_name + "!!"
            sys.exit(1)
    else:
        print "ERROR : " + node_type + " not supported for topology mapping!!"
        sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])
