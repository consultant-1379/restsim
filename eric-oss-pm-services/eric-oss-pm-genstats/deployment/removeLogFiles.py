#!/usr/bin/python
###############################################################################
# COPYRIGHT Ericsson 2020
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
###############################################################################

###############################################################################
# Version no    :  NSS 19.03
# Purpose       :  This Script removes and archive all logs from /netsim_users/pms/logs/.
# Jira No       :
# Gerrit Link   :
# Description   :  Improvement of Logrotate utility in Genstats for minilink logs
# Date          :  21/1/2019
# Last Modified :  abhishek.mandlewala@tcs.com
###############################################################################
'''
This script removes all logs except scanners.log, limitbw.log and rmFiles.log
from /netsim_users/pms/logs. The script is invoked from system crontab.
'''
import os, traceback
from utilityFunctions import Utility


# Creating Objects
util = Utility()

LOG_DIRECTORY = "/netsim_users/pms/logs/"
ARCHIVED_LOG_DIR = "/netsim_users/pms/logs/archived"
NOT_TO_BE_MANAGED = ["scanners.log","limitbw.log", "sim_pm_path.log"]
LOGROTATE_CONF = "/etc/logrotate.d/genstats"
LOG_LIST, MANAGE_LOGS = [], []
LOGROTATE_CMD = "/usr/sbin/logrotate --force /etc/logrotate.d/genstats"

DATA = '# logrotate configuration file for genstats pms logs\nLOG_FILES_LIST_PATTERN {\nolddir ' + ARCHIVED_LOG_DIR + '\ncompress\nrotate 20\ndaily\ncreate 644 netsim netsim\nmissingok\nnotifempty\n}\n'


def create_conf_file():
    """ create logrotate configuration file
    """
    if not util.checkDirectoryExistance(ARCHIVED_LOG_DIR):
        os.mkdir(ARCHIVED_LOG_DIR)

    try:
        with open(LOGROTATE_CONF, "w") as conf:
            conf.write(DATA.replace('LOG_FILES_LIST_PATTERN', ' '.join(create_log_files_path())))
            util.giveReadWritePermission('644', LOGROTATE_CONF, True)
            util.giveUserPermission('netsim', LOGROTATE_CONF, True)
    except:
        traceback.print_exc()


def create_log_files_path():
    """ create list of managed logs with full path
    """
    util.removeDirectoryIfExists(LOG_DIRECTORY + '.logs')
    return [ LOG_DIRECTORY + logfile for logfile in MANAGE_LOGS]


def run_logrotate():
    """ run logrotate utility
    """
    util.run_shell_command(LOGROTATE_CMD)


def checkPreCondition():
    if not util.checkDirectoryExistance(LOG_DIRECTORY):
        util.printStatements('Log directory ' + LOG_DIRECTORY + ' not present. Creating it.', 'WARNING')
        util.createRecursiveDirectory(LOG_DIRECTORY)
        util.giveUserPermission('netsim', LOG_DIRECTORY, True)
        util.giveReadWritePermission('755', LOG_DIRECTORY, True)


checkPreCondition()
LOG_LIST = filter(None, os.listdir(LOG_DIRECTORY))
MANAGE_LOGS = [log_file for log_file in LOG_LIST if log_file.endswith('.log') and log_file not in NOT_TO_BE_MANAGED]
HARD_CODED_LOGS = ['minilink_file_generation.log', 'minilink_precook_data.log', 'rmFiles.log', 'ml_pm_service.log', 'ml_pm_service_instrumentation.log']
for hard_coded_log in HARD_CODED_LOGS:
    if hard_coded_log not in MANAGE_LOGS:
        MANAGE_LOGS.append(hard_coded_log)
if util.checkFileExistance(LOGROTATE_CONF):
    util.printStatements('Deleting Logrotate conf file ' + LOGROTATE_CONF + '.', 'INFO')
    util.removeFilesIfExists(LOGROTATE_CONF)
create_conf_file()
run_logrotate()
