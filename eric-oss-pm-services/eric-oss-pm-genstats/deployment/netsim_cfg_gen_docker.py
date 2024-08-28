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
# Version no    :  NSS 17.10
# Purpose       :  Script is responsible for creating netsim_cfg file for docker.
# Jira No       :  NSS-12488
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/2390323
# Description   :  Adding change for creating netsim_cfg file for docker.
# Date          :  06/12/2017
# Last Modified :  g.multani@tcs.com
####################################################

from mako.template import Template
import os
import logging
import datetime
import sys
import shutil

LOG_DIR="/netsim_users/pms/logs"
SIMULATION_DIR = "/netsim/netsim_dbdir/simdir/netsim/netsimdir/"
PLAYBACK_CFG = "/netsim_users/pms/bin/playback_cfg"
SIM_DATA_FILE = "/netsim/genstats/tmp/sim_data.txt"
GET_SIM_DATA_SCRIPT = "/netsim_users/auto_deploy/bin/getSimulationData.py"


def upload_cfg(nssRelease, sim_data_list):
    sims = []
    mmes = []
    default_LTE_UETRACE_LIST = ["LTE01", "LTE02", "LTE03", "LTE04", "LTE05"]
    LTE_NE_map = {"LTE_UETRACE_LIST": [], "MSRBS_V1_LTE_UETRACE_LIST": [], "MSRBS_V2_LTE_UETRACE_LIST": [] }
    PM_file_paths = {}
    playback_sim_list = ""
    bsc_sim_list = []

    for sim_info in sim_data_list :
             sim_data = sim_info.split()
             sim_name = sim_data[1]
             ne_type = sim_data[5]
             stats_dir = sim_data[9]
             trace_dir = sim_data[11]

             if ne_type not in PM_file_paths:
                if "PRBS" in ne_type:
                   PM_file_paths["MSRBS_V1"] = [stats_dir, trace_dir]
                PM_file_paths[ne_type] = [stats_dir, trace_dir]

             if "LTE" in sim_name:
                sim_ID = sim_name.split()[-1].split('-')[-1]
                if "LTE" in sim_ID:
                    sims.append(sim_ID)
                else:
                    sims.append(sim_name)
                if "PRBS" in ne_type or "MSRBS-V1" in ne_type:
                    LTE_NE_map["MSRBS_V1_LTE_UETRACE_LIST"].append(sim_ID)
                    if sim_ID in default_LTE_UETRACE_LIST:
                        default_LTE_UETRACE_LIST.remove(sim_ID)
                elif "MSRBS-V2" in ne_type:
                      LTE_NE_map["MSRBS_V2_LTE_UETRACE_LIST"].append(sim_ID)
                      if sim_ID in default_LTE_UETRACE_LIST:
                          default_LTE_UETRACE_LIST.remove(sim_ID)
             elif "RNC" in sim_name:
                  sims.append(sim_name.split()[-1].split('-')[-1])
             elif "SGSN" in sim_name:
                  mmes.append(sim_name.split()[-1])
             else:
                  sims.append(sim_name.split()[-1])

    if get_playback_list():
            for nes in get_playback_list():
                sim_list = []
                result = os.system("ls " + SIMULATION_DIR + " | grep {0}".format(nes))
                sim_list = result.split("\n")
                for sim_name in sim_list:
                    playback_sim_list = playback_sim_list + " " + sim_name.strip()

    bsc_sim_list = get_bsc_list()
    if bsc_sim_list:
            for sim_name in bsc_sim_list:
                    sims.append(sim_name.strip())


    sims = list(set(sims))
    LTE_NE_map["LTE_UETRACE_LIST"] = default_LTE_UETRACE_LIST
    create_netsim_cfg(
        get_hostname(), nssRelease, ' '.join(sims), ' '.join(mmes), PM_file_paths, playback_sim_list.strip())
    shutil.copy2(get_hostname(), "/tmp")
    os.remove(get_hostname())

def get_bsc_list():
    bsc_sim_list = []
    bsc_sim_list = str(os.system('ls ' + SIMULATION_DIR + ' | grep BSC')).split("\n")
    if bsc_sim_list:
        return bsc_sim_list
    else:
        return None

def get_playback_list():
    if os.path.isfile(PLAYBACK_CFG):
       playback_content=os.system("grep NE_TYPE_LIST " + PLAYBACK_CFG).strip()
    else:
       getCurrentLog(" cannot find " + PLAYBACK_CFG,'WARN')
       return None
    PLAYBACK_SIM_LIST = []
    PLAYBACK_SIM_LIST = playback_content.split("=")[-1].replace("\"","").split()
    return PLAYBACK_SIM_LIST

def getCurrentLog(message,type):
    '''Generates  current log as per the log message and log type provided'''
    #os.system('mkdir /netsim/pms/logs')
    # os.system('chmod 755 /netsim/pms/logs')
    curDateTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if type == 'INFO':
       logging.info(curDateTime + message)
       print 'INFO: ' + curDateTime + message
    elif type == 'WARN':
       logging.warning(curDateTime + message)
       print 'WARNING: ' + curDateTime + message

def get_hostname():
    netsim_cfg_file = os.environ['HOST'].split('.')[0]
    if "atvts" in netsim_cfg_file:
        netsim_cfg_file = "netsim"
    return netsim_cfg_file

def get_sim_data():
    if os.path.isfile(SIM_DATA_FILE):
        p = open(SIM_DATA_FILE)
        sim_data_list = [line for line in p.readlines()]
    else:
        getCurrentLog(" cannot find " + SIM_DATA_FILE,'WARN')
        getCurrentLog("Run getSimulationData.py to generate " + SIM_DATA_FILE,'INFO')
        os.system('python ' + GET_SIM_DATA_SCRIPT)
        p = open(SIM_DATA_FILE)
        sim_data_list = [line for line in p.readlines()]
    return sim_data_list



def create_netsim_cfg(server_name, nssRelease, simulations, mmes, pm_file_paths, playback_sim_list):
    mytemplate = Template(filename="/netsim_users/auto_deploy/bin/netsim_cfg_template")
    with open(server_name, 'w+') as f:
        f.write(mytemplate.render(release=nssRelease, servers=server_name, server=server_name.replace(
            "-", "_"), simulation_list=simulations, mme_list=mmes, pm_file_locations=pm_file_paths, playback_sim_list=playback_sim_list ))

def main():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    logging.basicConfig(filename="/netsim_users/pms/logs/netsim_cfg.log", level=logging.INFO)
    getCurrentLog(" netsim_cfg file generation is started",'INFO')
    sim_data_list = get_sim_data()
    upload_cfg("16.8", sim_data_list)
    getCurrentLog(" netsim_cfg file is generated",'INFO')

main()