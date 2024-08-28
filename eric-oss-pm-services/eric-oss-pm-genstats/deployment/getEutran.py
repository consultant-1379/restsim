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
# Version no    :  NSS 18.02
# Purpose       :  To generate a file /netsim/genstats/eutrancellfdd_list.txt containing the Eutran cell data
#                  of each LTE node mentioned in /netsim/genstats/tmp/sim_data.txt supported by GenStats and
#                  copy the generated file to /netsim_users/pms/etc/eutrancellfdd_list.txt
# Jira No       :  NSS-10977
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/2193182
# Description   :  Generates a file /netsim/genstats/eutrancellfdd_list.txt containing the Eutran cell data
#                  of each LTE node by fetching the sim_name of nodes mentioned in /netsim/genstats/tmp/sim_data.txt
#                  supported by GenStats and copy the generated file to /netsim_users/pms/etc/eutrancellfdd_list.txt
# Date          :  4/4/2017
# Last Modified :  g.multani@tcs.com
####################################################

import logging, getopt
import sys
import os
import shutil
from datetime import datetime
from subprocess import Popen, PIPE

LOG_DIR="/netsim_users/pms/logs/"
if not os.path.exists(LOG_DIR):
      os.system("mkdir -p " + LOG_DIR)

logging.basicConfig(filename="/netsim_users/pms/logs/GetEutranData.log", level=logging.INFO)
EUTRANCELL_DATA_FILE = "/netsim/genstats/eutrancellfdd_list.txt"
DEST_EUTRANCELL_DATA_FILE = "/netsim_users/pms/etc/eutrancellfdd_list.txt"
SIM_DATA_FILE = "/netsim/genstats/tmp/sim_data.txt"
GET_SIM_DATA_SCRIPT = "/netsim_users/auto_deploy/bin/getSimulationData.py"
eutrancell_data = ""
incorrect_data_list = []
has_lte = 0


def get_eutran_data(deplType):
    isLTEpresent = False
    isEUtranDataPresent = False
    eutrancell_data = ""
    sims_without_eutran = []
    os.system("truncate -s 0 " + EUTRANCELL_DATA_FILE)
    with open(SIM_DATA_FILE) as sim_data_list:
         for sim_info in sim_data_list:
             sim_data = sim_info.split()
             sim_name = sim_data[1]
             node_name = sim_data[3]
             if "LTE" in sim_name and 'ERBS' in node_name:
                 isLTEpresent = True
                 eutrancell_data = "/netsim/netsimdir/" + sim_name + "/SimNetRevision/EUtranCellData.txt"
                 if os.path.exists(eutrancell_data):
                     os.system("cat " + eutrancell_data + " >> " + EUTRANCELL_DATA_FILE)
                     isEUtranDataPresent = True
                 else:
                     sims_without_eutran.append(sim_name)
    incorrect_data = run_shell_command("grep -E 'pERBS00.*\-1[3-9]' " + EUTRANCELL_DATA_FILE)
    incorrect_data_list = []
    incorrect_data_list = [x for x in filter(None,incorrect_data.splitlines())]
    for remove_data in incorrect_data_list:
         os.system("sed -i '/" + remove_data + "/d'  '" + EUTRANCELL_DATA_FILE + "' ")

    if sims_without_eutran:
        if deplType != 'NRM1.2':
            logging.error(" cannot find EUtranCellData.txt for " + ','.join(sims_without_eutran))
            print ("ERROR: cannot find EUtranCellData.txt for " + ','.join(sims_without_eutran))
            sys.exit(1)
        else:
            logging.warning(" cannot find EUtranCellData.txt for " + ','.join(sims_without_eutran))
            print ("WARNING: cannot find EUtranCellData.txt for " + ','.join(sims_without_eutran))
    elif not sims_without_eutran and isLTEpresent:
        if deplType == 'NRM1.2':
            netsim_file_name = get_hostname()
            os.system("echo '' >> /tmp/" + netsim_file_name)
            os.system("echo 'ERBS_CELLS_CONFIG_LIST=\"1 3 6 12\"' >> /tmp/" + netsim_file_name)

    if os.path.exists(EUTRANCELL_DATA_FILE):
        backup_eutran = EUTRANCELL_DATA_FILE + "_backup"
        os.system("cat " + EUTRANCELL_DATA_FILE + " | sort -u > " + backup_eutran)
        os.system("rm -f " + EUTRANCELL_DATA_FILE)
        os.system("mv " +  backup_eutran + " " + EUTRANCELL_DATA_FILE)

    if isLTEpresent:
        if deplType != 'NRM1.2':
            if not os.path.exists(EUTRANCELL_DATA_FILE) or not isEUtranDataPresent:
                print ('ERROR: Either ' + EUTRANCELL_DATA_FILE + ' file not present or ' + EUTRANCELL_DATA_FILE + ' file is empty.')
                logging.error("ERROR: Either ' + EUTRANCELL_DATA_FILE + ' file not present or ' + EUTRANCELL_DATA_FILE + ' file is empty.")
                print ('INFO: Exiting process.')
                sys.exit(1)

def getCurrentLog(message,type):
    '''Generates  current log as per the log message and log type provided'''
    curDateTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if type == 'INFO':
       logging.info(curDateTime + message)
       print ('INFO: ' + curDateTime + message)
    elif type == 'WARN':
       logging.warning(curDateTime + message)
       print ('WARNING: ' + curDateTime + message)

def run_shell_command(input):
    """ This is the generic method, Which spawn a new shell process to get the job done
    """
    output = Popen(input, stdout=PIPE, shell=True).communicate()[0]
    return output

def main(argv):
    deplType = "NSS"
    try:
        opts, args = getopt.getopt(argv, 'd', ['deplType='])
    except getopt.GetoptError:
             usage()
             sys.exit(2)
    for opt, arg in opts:
        if opt == '-d':
           deplType = arg
    getCurrentLog(" Generating " + EUTRANCELL_DATA_FILE,'INFO')
    if os.path.isfile(SIM_DATA_FILE):
        get_eutran_data(deplType)
    else:
        getCurrentLog(" Cannot find " + SIM_DATA_FILE,'WARN')
        getCurrentLog(" Generating " + SIM_DATA_FILE,'INFO')
        os.system('python ' + GET_SIM_DATA_SCRIPT)
        get_eutran_data(deplType)
    getCurrentLog(" Process completed",'INFO')

if __name__ == "__main__":
    main(sys.argv[1:])
