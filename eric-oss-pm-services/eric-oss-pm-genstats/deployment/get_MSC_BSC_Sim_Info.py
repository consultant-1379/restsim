#!/usr/bin/python
################################################################################
# COPYRIGHT Ericsson 2018
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS-18.14
# Purpose       :  This script is used to create mapping file which includes mapping of <SIM_NAME>:<NODE_NAME>:<NODE_TYPE> as one time activity to remove sim name & node name dependency at run time
# Jira No       :  NSS-21254
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/4349112/
# Description   :  Genstats support for MSC-BC(IS/BSP) and HLR-FE(BC/IS) for Blade and Cluster nodes
# Date          :  29/10/2018
# Last Modified :  kumar.dhiraj7@tcs.com
####################################################

import os
import sys
import socket
from _collections import defaultdict
from confGenerator import run_shell_command
from DataAndStringConstants import NETSIM_DBDIR, NETSIM_DIR

server_name = socket.gethostname()
bsc_msc_sim_info = '/netsim/genstats/tmp/bsc_msc_sim_info.txt'
netsim_script = "/netsim/inst/netsim_shell"
node_types = {'BSC' : ["BSC"], 'MSC' : ["vMSC-HC", "vMSC", "MSCv", "MSC-vIP-STP", "MSC-IP-STP", "CTC-MSC-BC-BSP","MSC-DB-BSP", "MSC-BC-BSP", "MSC-DB", "MSC-BC-IS" ], 'HLR' : ["vHLR-BS", "HLR-FE-IS", "HLR-FE-BSP", "HLR-FE"]}
simToNodeTypeMap = defaultdict(lambda : defaultdict(list))
simToSimTypeMap = defaultdict()

#Method to write mapping <SIM_NAME>:<NODE_NAME>:<NODE_TYPE> in file bsc_msc_sim_info.txt
def writeSimInfo():
    with open(bsc_msc_sim_info, 'w') as file:
        for sim_name, sim_info in simToNodeTypeMap.items():
            sim_type = simToSimTypeMap[sim_name]
            for node_type, node_list in sim_info.items():
                for node_name in node_list:
                    file.write(sim_name + '|' + node_name + "|" + node_type + "|" + sim_type + '\n')

#Method to generate mapping
def generateMapping(sim_name, sim_type_key):
    global simToNodeTypeMap, simToSimTypeMap
    netsim_cmd = "printf '.open " + sim_name + "\n.select network\n.show simnes' | " + netsim_script
    netsim_output = run_shell_command(netsim_cmd)
    sim_nodes = netsim_output.split("\n")

    for node_info in sim_nodes:
        if server_name in node_info:
            node_info_list = node_info.split()
            node_name = node_info_list[0]
            node_type = node_info_list[2]
            sim_type = None
            if node_type == "MSRBS-V2":
                node_type = "BSC_MSRBS_V2"
            if node_type in node_types[sim_type_key]:
                sim_type = node_type
                if node_type == "MSC-DB" and "BSP" in sim_name:
                    sim_type = "MSC-DB-BSP"
            simToNodeTypeMap[sim_name][node_type].append(node_name)
            if sim_type:
                simToSimTypeMap[sim_name] = sim_type
            #Debug Log
            #print "Node " + node_name + " Node type: " + node_type + " Sim type: " + sim_type


#Main function
def main():
    if os.path.isfile(bsc_msc_sim_info):
        os.remove(bsc_msc_sim_info)
    else:
        #Listing BSC MSC simulations present under netsim_dbdir location
        sims = os.listdir(NETSIM_DBDIR)
        netsimdir_sims = os.listdir(NETSIM_DIR)

        for sim in sims:
            sim_type_key = None
            for _type in node_types:
                if _type in sim.upper() and sim in netsimdir_sims:
                    sim_type_key = _type
                    if sim_type_key == "BSC" and "MSC" in sim:
                        sim_type_key = "MSC"
            if sim_type_key:
                generateMapping(sim, sim_type_key)

        if simToNodeTypeMap:
            writeSimInfo()

if __name__ == '__main__':
    main()

