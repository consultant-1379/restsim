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
# Version no    :  NSS 18.08
# Purpose       :  This script is responsible to maintain all CONSTANTS variables used in GenStats.
# Jira No       :  NSS-17777
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/3468368/
# Description   :  Genstats DDP Support
# Date          :  09/04/2018
# Last Modified :  mathur.priyank@tcs.com
####################################################

import sys, os
from confGenerator import getCurrentDateTime, run_shell_command
from DataAndStringConstants import NETSIM_CFG_FILE

def exit_logs(number):
    print (getCurrentDateTime() + ' INFO: Exiting process.')
    sys.exit(number)

def fetchNetsimCfgParam(param):
    """ This function will fetch params from netsim_cfg file and return the value"""
    paramValue=''
    with open(NETSIM_CFG_FILE) as netsim_cfg:
        for line in netsim_cfg:
            if line.startswith(param):
                return line.split("=")[1].strip()


def get_hostname():
    command = "hostname"
    hostName = run_shell_command(command).strip()
    if os.path.isfile("/.dockerenv"):
        hostName = "netsim"
    return hostName

