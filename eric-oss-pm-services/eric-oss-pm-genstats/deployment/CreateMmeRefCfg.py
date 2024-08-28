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
# Version no    :  NSS 18.12
# Purpose       :  Script to create /netsim_users/pms/etc/sgsn_mme_ebs_ref_fileset.cfg
# Jira No       :  
# Gerrit Link   :  
# Description   :  
# Date          :  2/7/2018
# Last Modified :  abhishek.mandlewala@tcs.com
####################################################

import sys, os, re, socket
from TemplateGenerator import get_sim_data
from confGenerator import run_shell_command
import DataAndStringConstants as Constants

def get_node_names(sim_dir):
    return [node for node in os.listdir(sim_dir) if os.path.isdir(os.path.join(sim_dir, node))]


def findRealDataOnServer():
    command = 'find / -maxdepth 3 -type d 2>&1 | grep -v -i "Permission denied" | grep ' + Constants.realDataDir + ' | head -1'
    storage_dir = run_shell_command(command).strip()
    if storage_dir:
        return storage_dir
    return '/store/EBM_Sample_Templates'
        

def writeMMEConfFile(_list, inputPath):
    with open(Constants.MME_REF_CFG, 'w') as file:
        for sim in _list:
            sim_name = sim.split()[1]
            if 'SGSN' in sim_name:
                print ("INFO : Creating " + Constants.MME_REF_CFG + " for sim : " + sim_name)
                for node_name in get_node_names(Constants.NETSIM_DBDIR + sim_name):
                    file.write(sim_name + ':' + node_name + ':' + inputPath + '\n')


def main():
    sim_data_list = get_sim_data()
    if sim_data_list:
        storageDir = findRealDataOnServer()
        writeMMEConfFile(sim_data_list, storageDir)
    else:
        print ('WARNING : No SGSN simulation detail found in sim_data.txt')
    

if __name__ == "__main__":
    main()

