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
# Purpose       :  To fetch site location information from netsim for Radio nodes.
# Jira No       :  NSS-11471
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/2277206/
# Description   :  Added support to get information of sile location for Radio nodes from netsim_shell
# Date          :  4/20/2017
# Last Modified :  abhishek.mandlewala@tcs.com
####################################################

from _collections import defaultdict
import os
from DataAndStringConstants import NETSIM_DBDIR
from confGenerator import run_shell_command, getCurrentDateTime, conf_file_permission
import sys


TRANSPORT_FILE = "/netsim/genstats/transport_sim_details"
netsim_script = "/netsim/inst/netsim_shell"
started_node_file = "/tmp/showstartednodes.txt"
sim_info = []

def write_site_location_data():
    conf_file_permission('666')
    for site_data in sim_info:
        content_replacer(site_data, ">>")
    conf_file_permission('777')
    print (getCurrentDateTime() + ' INFO: Site location data writing completed.')
    print (getCurrentDateTime() + ' INFO: Site location fetching completed.')

def content_replacer(input_value, breaker):
    cmd = "sed -i '/" + input_value.split(breaker)[0] + "/d' " + TRANSPORT_FILE
    run_shell_command(cmd)
    cmd = 'echo \"' + input_value.split(breaker)[0] + '>>\\\"' + input_value.split(breaker)[1].split("\"")[1] + '\\\"\" >> ' + TRANSPORT_FILE
    run_shell_command(cmd)

def grep_file_content(name):
    cmd = "cat " + started_node_file + " | grep {0}".format(name)
    result = run_shell_command(cmd).strip()
    return result

def get_site_data(DB_DIR):
    site_cmd = "dumpmotree:moid=\"1\",printattrs, scope=0, includeattrs=\"site\";"
    cmd = "ls " + DB_DIR + " | grep -v .zip | grep LTE"
    sim_list = filter(None, run_shell_command(cmd).strip().split('\n'))
    if not os.path.isfile(started_node_file):
        print (getCurrentDateTime() + ' WARN: ' + started_node_file + ' file is not present. Exiting process.')
        sys.exit(1)
    for sim_name in sim_list:
        result = grep_file_content(sim_name)
        if not result:
            continue
        cmd = "ls " + DB_DIR + sim_name + " | grep dg2"
        node_list = filter(None, run_shell_command(cmd).strip().split('\n'))
        if node_list:
            print (getCurrentDateTime() + ' INFO: Fetching site location data for ' + sim_name + ' simulation.')
            for node_name in node_list:
                result = grep_file_content(node_name)
                if not result:
                    continue
                cmd = "printf '.open " + sim_name + "\n.select " + node_name.strip() + "\n" + site_cmd + "' | " + netsim_script + " | grep site | sed -n '1!p' | cut -d\"=\" -f2"
                location = run_shell_command(cmd).strip()
                if location and "null" not in location and "\"\"" not in location :
                    sim_info.append(sim_name.replace('-', '_').replace('.', '_') + "_location=" + node_name + ">>\"" + location + "\"")
    if sim_info:
        if not os.path.isfile(TRANSPORT_FILE):
            cmd = "echo '#!/bin/bash' > " + TRANSPORT_FILE
            run_shell_command(cmd)
            cmd = "echo >> " + TRANSPORT_FILE
            run_shell_command(cmd)
        print (getCurrentDateTime() + ' INFO: Writing site location data in ' + TRANSPORT_FILE + ' file.')
        write_site_location_data()
    else:
        print (getCurrentDateTime() + ' INFO: No site location information available to write in ' + TRANSPORT_FILE + ' file.')

def main():
    get_site_data(NETSIM_DBDIR)

if __name__ == "__main__":
    main()

