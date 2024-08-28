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
# Purpose       :  This script is responsible to maintain all CONSTATS variables used in GenStats.
# Jira No       :  NSS-10375
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/2410090/
# Description   :  Addition of variable of PMS_ETC_DIR
# Date          :  06/05/2017
# Last Modified :  abhishek.mandlewala@tcs.com
####################################################

"""
@description:
This script defines the constant used in the GenStats.
"""

EMPTY_STRING=''
NETSIM_DBDIR = "/netsim/netsim_dbdir/simdir/netsim/netsimdir/"
NETSIM_DIR = "/netsim/netsimdir/"
EUTRANCELL_DATA_FILE = "/netsim/genstats/eutrancellfdd_list.txt"
PMS_EUTRANCELL_DATA_FILE = "/netsim_users/pms/etc/eutrancellfdd_list.txt"
MIM_FILES_LOCATION = "/netsim/inst/zzzuserinstallation/mim_files/"
MIB_FILES_LOCATION = "/netsim/inst/zzzuserinstallation/ecim_pm_mibs/"
GENSTATS_TMP_DIR = "/netsim/genstats/tmp/"
PMS_ETC_DIR = "/netsim_users/pms/etc/"
LOGS_DIR = "/netsim/genstats/logs/"
SIM_DATA_FILE = GENSTATS_TMP_DIR + "sim_data.txt"
EQUAL_SIGN = "="
EQUALS_SEPARATOR = "\\="
comma = ","
ZEROSTRING = "0"
SEMICOLON = ";"
COMMA = ","
PIPE = "|"
BACKSLASH = "/"
MINUS_SIGN = "-"
PLUS_SIGN = "+"
NEWLINE_CHAR = "\n"
DOT = "."
UNDER_SCORE = "_"
DEFAULT_PM_DATA_LOCATION='/c/pm_data/'
CFG_FILE_EXTN='.cfg'
COUNTER_PROP_FILE_EXTN='.cntrprop'
GET_STARTED_NODE_SCRIPT='/netsim_users/pms/bin/getStartedNodes'
PMS_TMPFS_LOCATION='/pms_tmpfs/'
NETSIM_CFG_FILE='/netsim/netsim_cfg'
SGSN='SGSN'
LTE='LTE'
RNC='RNC'
TMP_LOCATION='/tmp'
HOSTNAME='hostname'
MME_REF_CFG="/netsim_users/pms/etc/sgsn_mme_ebs_ref_fileset.cfg"
realDataDir = 'HSTNTX01LT9'

