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
# Purpose       :  Script parses topology data to store in JSON file 
# Jira No       :  NSS-34210
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/9256907/
# Description   :  Adding support for DO simulation SGSN node
# Date          :  03/03/2021
# Last Modified :  manali.singh@tcs.com
####################################################

import sys
import os
import json
import copy
from _collections import defaultdict
from shutil import rmtree

DO_SUPPORTED_NE_TYPES=['SGSN']
NETSIM_DBDIR="/netsim/netsim_dbdir/simdir/netsim/netsimdir"
NETSIM_DIR="/netsim/netsimdir/"
TOPOLOGY_FILE="/SimnetRevision/TopologyData.txt"
NODE_TYPE_MO_TOPOLOGY_CONFIG="/netsim_users/pms/bin/node_type_mo_config.txt"
SIM_INFO_FILE = "/netsim/genstats/tmp/sim_info.txt"
TOPOLOGY_DATA_DIR="/netsim_users/pms/etc/topology_info/"
NODE_TEMPLATE_MAP_DIR="/netsim_users/pms/etc/node_template_map/"

sim_info_file_map = defaultdict(lambda : defaultdict(list))
topology_mo_map = defaultdict(lambda : defaultdict(lambda : defaultdict(list)))
node_type_mo_dict = {}
topology_data_list=[]

def read_sim_info():
    '''This method will read sim_info file and create global map '''
    if(os.path.isfile(SIM_INFO_FILE)):
        with open(SIM_INFO_FILE, "r") as sim_info_file:
            for info in sim_info_file:
                filter_info = info.split(":")
                node_type = filter_info[1].strip()
                if node_type.upper() in node_type_mo_dict and node_type.upper() in DO_SUPPORTED_NE_TYPES:
                    sim_info_file_map[filter_info[0].strip()] = filter_info[1:]

def parse_topology_data():
    '''This method will parse topology data for supported sims and create json files'''
    for sim_name in sim_info_file_map:
        node_type = sim_info_file_map[sim_name][0].strip()
        topology_data = NETSIM_DIR + sim_name + TOPOLOGY_FILE
        if os.path.isfile(topology_data) and os.path.getsize(topology_data) > 0:
            create_topology_data_list(node_type, topology_data)
        else:
            print ("ERROR : " + "Missing " + topology_data + " Topology Data File.")
            continue
        if topology_data_list:
            evaluate_topology_data(sim_name)
        else:
           print ("ERROR : Cannot evaluate topology_data for " + sim_name)
           continue
        #dump sim topology info in json file clear list and dict for next sim
        out_json_file=TOPOLOGY_DATA_DIR + sim_name + ".json"
        dump_json(topology_mo_map, out_json_file)
        del topology_data_list[:]
        topology_mo_map.clear()

def evaluate_topology_data(sim_name):
    '''This method will evaluate the topology data list and will create a node template map.'''
    global topology_data_list, topology_mo_map
    for line_data in topology_data_list:
        element_list = line_data.replace(" ","").split(',')
        node_name = element_list[0].split('=')[1]
        mo_name = element_list[-1].split('=')[0]
        mo_data_list = element_list[1:]
        for mo_data in mo_data_list:
            topology_mo_map[node_name][mo_name][mo_data.split('=')[0].strip()].append(mo_data.split('=')[1].strip())

    node_mo_count_map = defaultdict(lambda : defaultdict(lambda : defaultdict(list)))
    for node, mo_data in topology_mo_map.items():
        for mo, mo_value in mo_data.items():
            mo_count = len(mo_value[mo])
            topology_mo_map[node][mo]['mo_count'] =  mo_count
            #node_mo_count_map[node][mo]['mo_count']=topology_mo_map[node][mo]['mo_count']
            node_mo_count_map[node][mo]['mo_count']= mo_count
    create_node_template_map_file(sim_name, node_mo_count_map)

def create_node_template_map_file(sim_name, node_mo_count_map):
    '''node_template_map.txt file will be created here containing the template count required specific to each simulation'''
    segregate_set = set()
    base_keys = node_mo_count_map.keys()

    for node, mo_data in node_mo_count_map.items():
        temp_list=[]
        for base_key in base_keys:
            if node_mo_count_map.get(base_key) == mo_data:
                temp_list.append(base_key)
        temp_list.sort()
        segregate_set.add(" ".join(temp_list))

    with open(NODE_TEMPLATE_MAP_DIR + "node_template_map.txt", 'a') as node_template_map_file:
        template_num=1
        for element in segregate_set:
            node_template_map_file.write(sim_name + "|" + element  + "|" + str(template_num) + "\n")
            template_num += 1

def create_topology_data_list(node_type,topology_data):
    '''This method reads TopologyData.txt file and create a topology data list 
    only for those mo present in the created  node_type_mo_dict'''
    global topology_data_list
    with open(topology_data) as fin:
        for line in fin:
            if line.startswith('ManagedElement=') : # and line.split(",")[-1].split("=")[0] in node_type_mo_dict[node_type.upper()]:
                topology_data_list.append(line)

def dump_json(my_dict, out_json_file):
    '''This method will dump dictionary to JSON file'''
    json_object = json.dumps(my_dict, indent = 4)
    with open(out_json_file , "w") as outfile:
        outfile.write(json_object)

def parse_node_mo_cofig():
    '''This Method will create a dictionary by reading node_type_mo_config.txt file
       Returns dictionary  {node_name : [list of mo] } '''
    global node_type_mo_dict
    if os.path.isfile(NODE_TYPE_MO_TOPOLOGY_CONFIG) and os.path.getsize(NODE_TYPE_MO_TOPOLOGY_CONFIG) > 0:
        with open (NODE_TYPE_MO_TOPOLOGY_CONFIG) as node_mo_config_file:
            for line in node_mo_config_file :
                line_element =  line.strip().split(':')
                if line_element is not None :
                    node_type_mo_dict[line_element[0]] = line_element[1].split(',')         
        dump_json(node_type_mo_dict, NODE_TEMPLATE_MAP_DIR + "topology_config.json")
    return  node_type_mo_dict

def main(argv):
    '''Main Method'''
    
    if os.path.isdir(TOPOLOGY_DATA_DIR):
        rmtree(TOPOLOGY_DATA_DIR)
    if os.path.isdir(NODE_TEMPLATE_MAP_DIR):
        rmtree(NODE_TEMPLATE_MAP_DIR)
    os.makedirs(TOPOLOGY_DATA_DIR, 0o755)
    os.makedirs(NODE_TEMPLATE_MAP_DIR, 0o755)

    if parse_node_mo_cofig():
        read_sim_info()
        parse_topology_data()

if __name__ == "__main__":
    main(sys.argv[1:])
