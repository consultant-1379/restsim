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
# Version no    :  NSS 17.8
# Purpose       :  Script fetches the delta list of simulations present on the box and in sim_data.txt
# Jira No       :  NSS-11521, NSS-11522
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/2304796/
# Description   :  Added auto detection facility of simulation list
# Date          :  4/28/2017
# Last Modified :  arwa.nawab@tcs.com
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
DELTA_SIM_LIST = []
SIM_LIST = []

def main():
    sim_data_list = genTemplates.get_sim_data()
    for sim in sim_data_list:
        sim_data = sim.split()
        sim_name = sim_data[1]
        SIM_LIST.append(sim_name)
    NETSIM_DBDIR_SIMS = NetsimInfo.fetchSimListToBeProcessed()

    for sim_name in NETSIM_DBDIR_SIMS:
        if any(sim in sim_name for sim in SIM_LIST):
            continue
        else:
            DELTA_SIM_LIST.append(sim_name)
    return DELTA_SIM_LIST

if __name__ == "__main__": main()

