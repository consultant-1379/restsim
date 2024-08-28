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
# Version no    :  NSS 21.17
# Purpose       :  Script fetches details of file location MO attribute for started nodes
# Jira No       :  NSS-37218
# Gerrit Link   :  https://gerrit.ericsson.se/10757934
# Description   :  Adding support for cIMS node in MT
# Date          :  30/09/2021
# Last Modified :  vadim.malakhovski@tcs.com
####################################################


import os
import re
import socket
import subprocess
from subprocess import PIPE, Popen
server_name = socket.gethostname()
import TemplateGenerator as genTemplates
import getSimulationData as NetsimInfo

SIM_DATA_FILE = "/netsim/genstats/tmp/sim_data.txt"
NETSIM_CFG = "/netsim/netsim_cfg"
FIXED_PATH_SIMS = ["WMG", "EPG", "SGSN"]
STARTED_NODES_FILE = "/tmp/showstartednodes.txt"
OUT_ROOT = "/pms_tmpfs/"
PLAYBACK_CFG = "/netsim_users/pms/bin/playback_cfg"
SIMULATION_DIR = "/netsim/netsim_dbdir/simdir/netsim/netsimdir/"
RADIO_NODE_NE = ["VTFRADIONODE", "5GRADIONODE", "TLS", "VRM", "VRSM","VSAPC", "VTIF", "PCC", "PCG", "SHARED-CNF", "CCSM", "CCDM", "CCRC", "CCPC", "SC", "CCES", "SMSF", "CIMS"]

def update_netsim_cfg_file(fileLocation,paramName):
    if '5GRADIONODE' in fileLocation:
        fileLocation = fileLocation.replace('5GRADIONODE','FIVEGRADIONODE')
    shell_command = "tail -c 1 " + NETSIM_CFG
    result = run_shell_command(shell_command)

    if result.strip():
        shell_command = "echo >> " + NETSIM_CFG
        run_shell_command(shell_command)

    shell_command = cmd = "echo " + fileLocation + "=" + "'\"" + paramName + "\"' >> " + NETSIM_CFG
    run_shell_command(shell_command)

def run_shell_command(command):
    command_output = Popen(command, stdout=PIPE, shell=True).communicate()[0]
    return command_output

def get_node_names(sim_dir):
    return [node for node in os.listdir(sim_dir)
            if os.path.isdir(os.path.join(sim_dir, node))]

def get_playback_list():
    if os.path.isfile(PLAYBACK_CFG):
       playback_content = run_shell_command("grep NE_TYPE_LIST " + PLAYBACK_CFG).strip()
    else:
       return None
    PLAYBACK_SIM_LIST = []
    PLAYBACK_SIM_LIST = playback_content.split("=")[-1].replace("\"", "").split()
    return PLAYBACK_SIM_LIST

def main():

    if os.path.isfile(STARTED_NODES_FILE):
        print ("INFO : Fetching file location MO for started nodes")
        sim_data_list = genTemplates.get_sim_data()
        for sim in sim_data_list:
             absolute_sim_name = ''
             sim_data = sim.split();
             sim_name = sim_data[1]
             absolute_sim_name = sim_name
             if any(sim in sim_name for sim in FIXED_PATH_SIMS):
                 continue
             else:
                 if sim_name in open(STARTED_NODES_FILE).read():
                     node_type = sim_data[5].upper()
                     node_type = node_type.replace("-", "_")
                     stats_dir_param = ''
                     trace_dir_param = ''
                     if node_type == 'PRBS':
                         stats_dir_param = 'MSRBS_V1_PM_FileLocation'
                         trace_dir_param = 'MSRBS_V1_PMEvent_FileLocation'
                     else:
                         stats_dir_param = node_type + "_PM_FileLocation"
                         trace_dir_param = node_type + "_PMEvent_FileLocation"
                     if "LTE" in sim_name or "RNC" in sim_name:
                         sim_ID = sim_name.split()[-1].split('-')[-1]
                         if 'RNC' in sim_ID:
                             sim_name = sim_ID
                         else:
                             if not any(radio_ne in sim_name.upper() for radio_ne in RADIO_NODE_NE):
                                 sim_name = sim_ID
                     for node_name in get_node_names(OUT_ROOT + sim_name):
                         if 'RNC' in sim_name.upper() and 'BSC' in node_name.upper():
                             continue
                         if node_name in open(STARTED_NODES_FILE).read():
                             if node_type in NetsimInfo.CPP_NE_TYPES:
                                 data_dir = "performanceDataPath"
                             else:
                                 data_dir = "fileLocation"
                             if stats_dir_param not in open(NETSIM_CFG).read():
                                 stats_dir = NetsimInfo.get_pmdata_mo_attribute_value(data_dir, absolute_sim_name, node_name, node_type, "").strip()
                                 if "/c/pm_data" not in stats_dir:
                                     print ("INFO : " + sim_name + " >> Updating Stats File Location")
                                     update_netsim_cfg_file(stats_dir_param,stats_dir)
                             if trace_dir_param not in open(NETSIM_CFG).read():
                                 trace_dir = NetsimInfo.get_pmdata_mo_attribute_value("outputDirectory", absolute_sim_name, node_name, node_type, "").strip()
                                 if "/c/pm_data" not in trace_dir:
                                     print ("INFO : " + sim_name + " >> Updating Events File Location")
                                     update_netsim_cfg_file(trace_dir_param,trace_dir)
                             break
        if get_playback_list():
           for nes in get_playback_list():
               if "GNODEBRADIO" not in nes.upper():
                   sim_list = []
                   nes_bck = nes.replace('-','_')
                   result = run_shell_command("ls " + SIMULATION_DIR + " | grep {0}".format(nes))
                   sim_list = filter(None,result.split("\n"))
                   for sim_name in sim_list:
                       if sim_name in open(STARTED_NODES_FILE).read():
                           pm_stats_dir = run_shell_command('python /netsim_users/pms/bin/getPMFileLocation.py --data_dir "fileLocation" --sim_name '+ sim_name +' --node_type '+ nes.upper()).strip()
                           stats_dir_param = nes_bck + "_PM_FileLocation"
                           if stats_dir_param not in open(NETSIM_CFG).read():
                               if "/c/pm_data" not in pm_stats_dir:
                                   print ("INFO : " + sim_name + " >> Updating Stats File Location")
                                   update_netsim_cfg_file(stats_dir_param,pm_stats_dir)

    else:
        print ("WARN : /tmp/showstartednodes.txt file not found")

if __name__ == "__main__": main()

