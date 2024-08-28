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
# Version no    :  NSS 17.17
# Purpose       :  Script to support and trigger Genstats rollout pre execution
# Jira No       :
# Gerrit Link   :
# Description   :  pre execution of genStats
# Date          :  10/11/2017
# Last Modified :  tejas.lutade@tcs.com
####################################################

'''
This script is used to perform pre-execution steps of genstats rollout automatically

'''

import sys,getopt
import os
from subprocess import Popen, PIPE
from StringIO import StringIO
from shlex import split
import subprocess

from GenstatsLib import command_run

RPM_PACKAGE = "ERICnetsimpmcpp_CXP9029065.rpm"
SIMULATION_DIR = "/netsim/netsim_dbdir/simdir/netsim/netsimdir/"
TMPFS_DIR = "/pms_tmpfs/"
MASTER_ROLLOUT_SCRIPT = "bash /netsim_users/pms/bin/pm_setup_stats_recordings.sh"
GENSTATS = "bash /netsim_users/pms/bin/genStats"
EUTRANCELL_DATA_FILE = "/netsim/genstats/eutrancellfdd_list.txt"
CHECK_DEPL_TYPE = "/netsim/simdepContents/"
PLAYBACK_CFG = "/netsim_users/pms/bin/playback_cfg"
SIM_DIR = "/netsim/netsim_dbdir/simdir/netsim/"
VFARM_TYPE_DIR = "/netsim/simdepContents/"
QA_LOG_FILE = "/netsim/genstats/logs/genstatsQA.log"
RADIO_NODE_NE = ["VTFRADIONODE", "5GRADIONODE", "TLS", "VRM"]
SIM_DATA_FILE = "/netsim/genstats/tmp/sim_data.txt"
LOGS_DIR = "/netsim/genstats/logs/"
SGSN_REAL_DATA = "/real_data/HSTNTX01LT9/"
RHOSTS_FILE = "/netsim_users/auto_deploy/etc/.rhosts"


def auto_rollout(rpm_version="RELEASE", nssRelease="16.8", recording_file_version="17.15.1",deplType="NSS",edeStatsCheck="False"):
    if deplType == 'NRM3':
        if os.path.exists(SGSN_REAL_DATA):
            result = set_permission_for_ebs_realdata()
            if result != 0:
                sys.exit(1)
    upload_rhosts()
    if get_hostname() != "netsim" and deplType == "NSS":
        remove_unstarted_node_tmpfs_dirs()
    download_record_file(recording_file_version)
    unzip_record_file()

def download_record_file(recording_file_version):
    bashCommand = "curl -L \"https://arm901-eiffel004.athtem.eei.ericsson.se:8443/nexus/service/local/repositories/nss/content/com/ericsson/nss/Genstats/recording_files/" + \
        recording_file_version + "/recording_files-" + \
        recording_file_version + ".zip\" -o recording_files.zip"
    #command_run("netsim", bashCommand, section="download_record_file")
    os.system(bashCommand)

def get_hostname():
    netsim_cfg_file = os.uname()[1]
    if "atvts" in netsim_cfg_file:
        netsim_cfg_file = "netsim"
    return netsim_cfg_file

def remove_unstarted_node_tmpfs_dirs():
    # 1.8K VFARMs to have only first five nodes in every sim
    # Node deletion after 5 nodes to be done for 1.8K VFARM and VAPP
    # A file with name Simnet_15K / Simnet_1.8K helps to identify if the VFARM is 15K or 1.8K
    type_list = []
    if os.path.isdir(VFARM_TYPE_DIR):
        bashCommand = "ls " + VFARM_TYPE_DIR + " | grep -i content | egrep -i 'Simnet_1.8K|Simnet_5K'"
        type_list = run_shell_command(bashCommand).split()

    if type_list or get_hostname() == "netsim":
        mounted_sim_dir_list = run_shell_command('ls ' + TMPFS_DIR + ' | xargs -n 1 basename | grep -v xml_step').split()
        for sim_dir in mounted_sim_dir_list:
            sim_path = TMPFS_DIR + sim_dir
            run_shell_command('cd ' + sim_path + ' && ls |sort | perl -ne \'print if $.>5\' | xargs rm -rf; cd -')

def run_shell_command(input):
    """ This is the generic method, Which spawn a new shell process to get the job done
    """
    output = Popen(input, stdout=PIPE, shell=True).communicate()[0]
    return output


def set_permission_for_ebs_realdata():
    user_name = "root"
    bashCommand = "chown -R netsim " + SGSN_REAL_DATA
    command_run(user_name, bashCommand, section="set_permission_for_ebs_realdata")
    bashCommand = "chgrp -R netsim " + SGSN_REAL_DATA
    command_run(user_name, bashCommand, section="set_permission_for_ebs_realdata")
    bashCommand = "chmod 777 -R " + SGSN_REAL_DATA
    command_run(user_name, bashCommand, section="set_permission_for_ebs_realdata")
    return 0

def unzip_record_file():
    run_shell_command("mkdir -p /netsim/genstats")
    run_shell_command("rm -rf " + LOGS_DIR)
    run_shell_command("mkdir -p " + LOGS_DIR + "rollout_console")
    run_shell_command("unzip -o recording_files.zip -d /netsim/genstats > /dev/null 2>&1")

def upload_rhosts():
    if os.path.isfile(RHOSTS_FILE):
        os.system("cp " + RHOSTS_FILE + " ~/")

def install_miniconda():
    if not os.path.exists('/netsim/miniconda'):
        os.system('curl -L "https://arm901-eiffel004.athtem.eei.ericsson.se:8443/nexus/service/local/repositories/nss/content/com/ericsson/nss/Genstats/Miniconda2/16.14.3/Miniconda2-16.14.3.zip" -o /netsim/Miniconda2.sh')
        os.system('bash /netsim/Miniconda2.sh -b -p /netsim/miniconda')
        os.system('/netsim/miniconda/bin/conda install -y mako')

def install_rpm(rpm_version):
    download_rpm(rpm_version)
    user_name = "root"
    bashCommand = "rpm -Uvh --force /tmp/" + RPM_PACKAGE
    command_run(user_name, bashCommand, section="install_rpm")
    bashCommand = "chown netsim:netsim /netsim_users/ -R"
    command_run(user_name, bashCommand, section="change_permission")
    bashCommand = "rm /tmp/" + RPM_PACKAGE
    command_run(user_name, bashCommand, section="remove_rpm")
    bashCommand = "chown -R netsim:netsim /pms_tmpfs/"
    command_run(user_name, bashCommand, section="chown_section")


def download_rpm(rpm_version="RELEASE"):
    if 'SNAPSHOT' in rpm_version:
        os.system("curl  -L \"https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/service/local/artifact/maven/redirect?r=snapshots&g=com.ericsson.cifwk.netsim&a=ERICnetsimpmcpp_CXP9029065&p=rpm&v=" + rpm_version + "\" -o /tmp/ERICnetsimpmcpp_CXP9029065.rpm")
    else:
        os.system("curl  -L \"https://arm1s11-eiffel004.eiffel.gic.ericsson.se:8443/nexus/service/local/artifact/maven/redirect?r=releases&g=com.ericsson.cifwk.netsim&a=ERICnetsimpmcpp_CXP9029065&p=rpm&v=" + rpm_version + "\" -o /tmp/ERICnetsimpmcpp_CXP9029065.rpm")

def usage():
    print "Usage:"
    print "pre_execution.py -r <RPM_VERSION>"

def main(argv):
    rpm_version = "RELEASE"
    nssRelease = "16.8"
    recording_file_version = "17.15.1"
    deplType = "NSS"
    edeStatsCheck = "False"
    try:
        opts, args = getopt.getopt(argv, 'r:n:c:d:e:h', ['rpm_version=', 'nssRelease=', 'recording_file_version=', 'deplType=', 'edeStatsCheck=','help'])
    except getopt.GetoptError:
         usage()
         sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print "pre_execution.py -r <RPM_VERSION>"
            sys.exit()
        elif opt in ("-r", "rpm_version"):
            rpm_version = arg
        elif opt in ("-n", "nssRelease"):
            nssRelease = arg
        elif opt in ("-c", "recording_file_version"):
            recording_file_version = arg
        elif opt in ("-d", "deplType"):
            deplType = arg
        elif opt in ("-e", "edeStatsCheck"):
            edeStatsCheck = arg

    install_miniconda()
    #install_rpm(rpm_version)
    auto_rollout(rpm_version, nssRelease, recording_file_version, deplType, edeStatsCheck)

if __name__ == "__main__":
    main(sys.argv[1:])