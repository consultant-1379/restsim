#!/usr/bin/python

################################################################################
# COPYRIGHT Ericsson 2017
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 18.1
# Purpose       :  Script generates stats templates for CPP and COM/ECIM nodes
# Jira No       :  EQEV-47160
# Gerrit Link   :
# Description   :  Update the regex for PRBS nodes as per fabtask.py
# Date          :  23/03/2018
# Last Modified :  mahesh.lambud@tcs.com
####################################################


import logging
import sys,getopt
import os
import shutil
from datetime import datetime
from subprocess import Popen, PIPE

logging.basicConfig(filename="/netsim_users/pms/logs/GetEutranData.log", level=logging.INFO)
EUTRANCELL_DATA_FILE = "/netsim/genstats/eutrancellfdd_list.txt"
DEST_EUTRANCELL_DATA_FILE = "/netsim_users/pms/etc/eutrancellfdd_list.txt"
SIM_DATA_FILE = "/netsim/genstats/tmp/sim_data.txt"
GET_SIM_DATA_SCRIPT = "/netsim_users/auto_deploy/bin/getSimulationData.py"
eutrancell_data = ""
incorrect_data_list = []
has_lte = 0

def run_shell_command(input):
    """ This is the generic method, Which spawn a new shell process to get the job done
    """
    output = Popen(input, stdout=PIPE, shell=True).communicate()[0]
    return output

def getEutranData():
    '''Delete the existing EUTRANCELL_DATA_FILE'''
    if not isSingleRollout:
        if os.path.isfile(EUTRANCELL_DATA_FILE):
            os.remove(EUTRANCELL_DATA_FILE)
            os.system('touch ' + EUTRANCELL_DATA_FILE)
        if os.path.isfile(DEST_EUTRANCELL_DATA_FILE):
            os.remove(DEST_EUTRANCELL_DATA_FILE)
            os.system('touch ' + DEST_EUTRANCELL_DATA_FILE)

    '''Read sim_data.txt to obtain desired eutran data for each LTE node info'''
    global has_lte
    with open(SIM_DATA_FILE) as sim_data_list:
        missing_utran = False
        for sim_info in sim_data_list:
            sim_data=' '.join(sim_info.split())
            sim_name=sim_data.split()[1]
            node_name = sim_data.split()[3]
            if "LTE" in sim_name and "ERBS" in node_name:
                getCurrentLog(" Processing " + sim_name,'INFO')
                has_lte = 1
                eutrancell_data = "/netsim/netsimdir/" + sim_name + "/SimNetRevision/EUtranCellData.txt"
                if os.path.isfile(eutrancell_data):
                    os.system("grep -E -v 'pERBS00.*\-1[3-9]' '" + eutrancell_data + "' " + ' >> ' + EUTRANCELL_DATA_FILE )
                    os.system("grep -E -v 'pERBS00.*\-1[3-9]' '" + eutrancell_data + "' " + ' >> ' + DEST_EUTRANCELL_DATA_FILE ) 
                else:
                    getCurrentLog(" Cannot find " + eutrancell_data,'WARN')
                    missing_utran = True

    if not os.path.isfile('/netsim/netsim_cfg'):
        getCurrentLog("Cannot find netsim_cfg", 'ERROR')

    command = 'cat /netsim/netsim_cfg | grep TYPE= | cut -d\'\"\' -f2'
    deployment = run_shell_command(command).strip()
    command = 'cat /netsim/netsim_cfg | grep ERBS_CELLS_CONFIG_LIST'
    erbs_list_val = run_shell_command(command).strip()

    if missing_utran:
        if deployment == 'NRM1.2':
            if erbs_list_val:
                os.system("cat /netsim/netsim_cfg | grep -v ERBS_CELLS_CONFIG_LIST > /tmp/netsim_cfg_backup")
                os.system("mv /tmp/netsim_cfg_backup /netsim/netsim_cfg")
        else:
            getCurrentLog("Eutran file missing for LTE sims for deployment " + deployment.strip(), 'ERROR')
    elif not missing_utran and has_lte == 1:
        if deployment == 'NRM1.2':
            if not erbs_list_val:
                os.system("cat /netsim/netsim_cfg > /tmp/netsim_cfg_backup")
                os.system("echo '' >> /tmp/netsim_cfg_backup")
                os.system("echo 'ERBS_CELLS_CONFIG_LIST=\"1 3 6 12\"' >> /tmp/netsim_cfg_backup")
                os.system("mv /tmp/netsim_cfg_backup /netsim/netsim_cfg")
            
    remove_duplicate_entry(EUTRANCELL_DATA_FILE)
    remove_duplicate_entry(DEST_EUTRANCELL_DATA_FILE)
    if has_lte == 0:
        getCurrentLog(" Cannot find any LTE node in " + SIM_DATA_FILE,'WARN')


def remove_duplicate_entry(file_name):
    backup_file = file_name + "_backup"
    if os.path.isfile(file_name):
        os.system("cat " + file_name + " | sort -u > " + backup_file)
        os.system("rm -f " + file_name)
        os.system("mv " + backup_file + " " + file_name)
        

def getCurrentLog(message,type):
    '''Generates  current log as per the log message and log type provided'''
    curDateTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if type == 'INFO':
       logging.info(curDateTime + message)
       print('INFO: ' + curDateTime + message)
    elif type == 'WARN':
       logging.warning(curDateTime + message)
       print('WARNING: ' + curDateTime + message)
    elif type == 'ERROR':
        logging.error(curDateTime + message)
        print('ERROR: ' + curDateTime + message)
        sys.exit(1)

def main(argv):

    global isSingleRollout
    isSingleRollout = False
    opts, args = getopt.getopt(argv, "s", ["s="])
    for opt, arg in opts:
        if opt in ("-s", "--s"):
            isSingleRollout = True

    getCurrentLog(" Generating " + EUTRANCELL_DATA_FILE,'INFO')
    if os.path.isfile(SIM_DATA_FILE):
        getEutranData()
    else:
        getCurrentLog(" Cannot find " + SIM_DATA_FILE,'WARN')
        getCurrentLog(" Generating " + SIM_DATA_FILE,'INFO')
        os.system('python ' + GET_SIM_DATA_SCRIPT)
        getEutranData()
    getCurrentLog(" Process completed",'INFO')

if __name__ == "__main__":
    main(sys.argv[1:])

