#!/usr/bin/python

################################################################################
# COPYRIGHT Ericsson 2016
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 17.5
# Purpose       :  To fetch mo attribute information from netsim for simulations.
# Jira No       :  NSS-9901
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/2097187/
# Description   :  Change in format of sim_data_transport file and netsim_cfg TRANSPORT_SIM_LIST removal solution
# Date          :  2/16/2017
# Last Modified :  abhishek.mandlewala@tcs.com
####################################################

from _collections import defaultdict
import os
import stat
import re
from subprocess import Popen, PIPE
import subprocess

GENSTATS_DIR = "/netsim/genstats/"
SIM_MO_PROP_FILE = GENSTATS_DIR + "mo_attribute_details.cfg"
SIM_MO_PROP_FILE_TMP = GENSTATS_DIR + ".mo_attribute_details.cfg"
NETSIM_CFG = "/netsim/netsim_cfg"
SIM_DATA_TRANSPORT_FILE = GENSTATS_DIR + "sim_data_transport"

sim_prop_map = defaultdict(lambda : defaultdict(list))
""" contains details of mo_attribute_details.cfg file. """
started_node_map = defaultdict(list)
""" contains details of started node on netsim. """
writer_map = defaultdict(lambda : defaultdict(list))
""" contains parsed data which has to be written in sim_data_transport file """
sftp_order_map = {}
""" contains order of files to be sftp for each sim """
mandate_param_list = ["destinationHost", "userName", "password", "directoryPath", "adminState"]

ARROW_SEPARATOR = ">>"
SIM_PROP_NAME_SEPARATOR = "&&"
SCRIPT_EXECUTION_FLAG = True


def run_netsim_cmd(netsim_cmd, pipe_flag=False):
    """ run NETSim commands in the netsim_shell

        Args:
            param1 (string): given NETSim command
            param2 (boolean):

        Returns:
            string: NETSim output command
    """
    p = subprocess.Popen(["echo", "-n", netsim_cmd], stdout=subprocess.PIPE)
    netsim_cmd_out = subprocess.Popen(["/netsim/inst/netsim_shell"], stdin=p.stdout, stdout=subprocess.PIPE)
    p.stdout.close()
    if pipe_flag:
        return netsim_cmd_out
    else:
        return netsim_cmd_out.communicate()[0]


def read_mo_cfg_file():
    """ read the data from /netsim/genstats/.mo_attribute_details.cfg file and store it in map
            (sim_prop_map) : { sim_name : { mo_command : [mo_attribute_list] } }
    """
    sim_key = ""
    with open(os.path.abspath(SIM_MO_PROP_FILE_TMP), 'r') as prop_file:
        for line in prop_file:
            if line:
                if "sim_name" in line:
                    temp_key = line.split(ARROW_SEPARATOR)[1].strip()
                    if temp_key:
                        if temp_key not in sim_prop_map.keys():
                            if sim_prop_map:
                                check_mandate_param_in_cfg(sim_key)
                            sim_key = temp_key
                            temp_key = ""
                            continue
                        else:
                            SCRIPT_EXECUTION_FLAG = False
                            print ('WARNING: Duplicate value of sim ' + sim_key + ' present in file. Exiting process.')
                            break
                else:
                    if sim_key:
                        if "sftp_order" in line:
                            if sim_key not in sftp_order_map.keys():
                                if line.split(ARROW_SEPARATOR)[1].strip():
                                    sftp_order_map[sim_key] = line.split(ARROW_SEPARATOR)[1].strip()
                                    continue
                                else:
                                    print ('WARNING: sftp order field is empty for ' + sim_key + '. Checking sftp order in next field.')
                                    continue
                            else:
                                print ('WARNING: Duplicate sftp order found for ' + sim_key + '. Ignoring current order.')
                                continue
                        mo_command_key = line.split(ARROW_SEPARATOR)[1].strip()
                        sim_prop_list = line.split(ARROW_SEPARATOR)[0].strip()
                        if mo_command_key and sim_prop_list:
                            sim_prop_map[sim_key][mo_command_key].append(sim_prop_list)
                        else:
                            continue
    check_mandate_param_in_cfg(sim_key)


def check_mandate_param_in_cfg(sim_name):
    """
    If all mandatory attributes not present for any sim, that sim will not be processed
    """
    temp_mandate_list = list(mandate_param_list)
    for mo_key in sim_prop_map[sim_name].keys():
        for param_name in sim_prop_map[sim_name][mo_key]:
            for attr in temp_mandate_list:
                if attr in param_name:
                    temp_mandate_list.remove(attr)
    if len(temp_mandate_list) > 0:
        del sim_prop_map[sim_name]
        print ('WARNING: All mandatory attributes are not mentioned for ' + sim_name + ' sim. Hence skipping this simulation.')


def get_started_node_info_from_netsim():
    """ fetch required started node information from netsim and store it in map
            started_node_map : { simulation_name : [node_list]}
    """
    temp_sim = ""
    for sim_name in sim_prop_map.keys():
        if sim_name in sftp_order_map.keys():
            temp_sim = temp_sim + sim_name + "|"
    temp_sim = temp_sim.strip().replace('\n', '')
    if temp_sim:
        input_sim = "'" + temp_sim[:-1] + "'"
        input_cmd = "echo '.show started' | /netsim/inst/netsim_shell | egrep {0}".format(input_sim)
        result = run_shell_command(input_cmd)
        if result.strip():
            rows = result.split("\n")
            for row in rows:
                if not re.match(r'\S', row):
                    if row.strip():
                        node_info = re.sub(' +', ' ', row).split(" ")
                        if len(node_info[12].split("/")) > 1:
                            started_node_map[node_info[12].split("/")[3]].append(node_info[1])
        else:
            SCRIPT_EXECUTION_FLAG = False
    else:
        SCRIPT_EXECUTION_FLAG = False
        print ('WARNING: SFTP order is not defined for any sim. Exiting process.')


def map_simulation_with_sim_name():
    """ Create relation between sim, simulation and node to fetch required Mo attribute value for respected node and write values in map
    """
    for sim_name in sim_prop_map.keys():
        for simulation_name in started_node_map.keys():
            if sim_name in simulation_name:
                node_list = started_node_map[simulation_name]
                for node in node_list:
                    fetch_attribute_from_netsim(sim_name, simulation_name, node)


def fetch_attribute_from_netsim(sim_name, simulation_name, node):
    """ fetch required started node Mo attribute by executing commands and it in map to write in file
            writer_map : { simulation_name : { node_name : [Mo_attribute_value_list] } }
    """
    invalid_value_check = False
    for mo_key, sim_prop_list in sim_prop_map[sim_name].items():
        netsim_cmd = ".open " + simulation_name + " \n .select " + node + " \n " + mo_key + " \n"
        mo_attributes = run_netsim_cmd(netsim_cmd, False)
        mo_attributes = mo_attributes.split("\n")
        if any("MO not defined:" in row for row in mo_attributes):
            writer_map_data_correction(simulation_name, node)
            print ('INFO: Mo not defined for node : ' + node + '. Hence skipping fetching operation for this node.')
            return
        for sim_prop_value in sim_prop_list:
            mo_attribute = sim_prop_value.split(SIM_PROP_NAME_SEPARATOR)[1] + "="
            for atribute in mo_attributes:
                if mo_attribute in atribute:
                    attribute = atribute.replace(mo_attribute, '').strip()
                    if any(attr in mo_attribute for attr in mandate_param_list):
                        if attribute and attribute not in '""':
                            if "destinationHost" in mo_attribute and attribute in "0.0.0.0":
                                invalid_value_check = True
                            elif "adminState" in mo_attribute and attribute in "1":
                                invalid_value_check = True
                            else:
                                writer_map[simulation_name][node].append('_' + mo_attribute + attribute)
                        else:
                            invalid_value_check = True
                        if invalid_value_check:
                            writer_map_data_correction(simulation_name, node)
                            return
                    else:
                        writer_map[simulation_name][node].append('_' + sim_prop_value.split(SIM_PROP_NAME_SEPARATOR)[0] + "=" + attribute)


def writer_map_data_correction(simulation_name, node_name):
    if simulation_name in writer_map.keys():
        if node_name in writer_map[simulation_name].keys():
            del writer_map[simulation_name][node_name]


def write_transport_file():
    transport_sim = ""
    node_list = ""

    file_writer = open(SIM_DATA_TRANSPORT_FILE, 'w')
    file_writer.write("#!/bin/sh" + "\n")

    for simulation_name in writer_map.keys():
        for sftp_key in sftp_order_map.keys():
            if sftp_key in simulation_name:
                transport_sim = transport_sim + " " + simulation_name
                file_writer.write("\n" + "sim_name=" + simulation_name + "\n")
                file_writer.write(simulation_name.replace('-', '_') + '_sftp_order=' + sftp_order_map[sftp_key] + "\n")
                for node in writer_map[simulation_name].keys():
                    node_list = node_list + node + ' '
                file_writer.write(simulation_name.replace('-', '_') + '_node_list="' + node_list[:-1] + '"' + "\n")
                node_list = ""
                for node_name in writer_map[simulation_name].keys():
                    for attr_value in writer_map[simulation_name][node_name]:
                        file_writer.write(node_name + attr_value + "\n")
                    file_writer.write("\n")

    file_writer.close()

    # assign permission to file
    os.chmod(SIM_DATA_TRANSPORT_FILE, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    # check for availability of netsim_cfg
    if os.path.isfile(NETSIM_CFG):
        update_netsim_cfg_file(transport_sim.strip())
    else:
        print ('ERROR: ' + NETSIM_CFG + ' file not present. Cannot update ' + NETSIM_CFG)


# create back up of sim_details.properties file
def create_temp_file(source_file, destination_file):
    shell_command = "cat " + source_file + " | tr -d ' \t\r\f' | sed '/^\s*$/d' > " + destination_file
    run_shell_command(shell_command)


# Generic method to execute shell commands
def run_shell_command(command):
    command_output = Popen(command, stdout=PIPE, shell=True).communicate()[0]
    return command_output


# update transport list in netsim_cfg file
def update_netsim_cfg_file(sim_name):
    shell_command = "tail -c 1 " + NETSIM_CFG
    result = run_shell_command(shell_command)

    if result.strip():
        shell_command = "echo >> " + NETSIM_CFG
        run_shell_command(shell_command)

    shell_command = "echo TRANSPORT_SIM_LIST=" + "'\"" + sim_name + "\"'" + " >> " + NETSIM_CFG
    run_shell_command(shell_command)


def main():
    if os.path.isfile(SIM_MO_PROP_FILE):
        if os.path.isfile(NETSIM_CFG):
            if "TRANSPORT_SIM_LIST" in open(NETSIM_CFG).read():
                shell_command = "sed -i '/TRANSPORT_SIM_LIST/d' " + NETSIM_CFG
                run_shell_command(shell_command)
        else:
            print ('ERROR: ' + NETSIM_CFG + ' file not present. Cannot update ' + NETSIM_CFG)
        create_temp_file(SIM_MO_PROP_FILE, SIM_MO_PROP_FILE_TMP)
        if os.path.isfile(SIM_DATA_TRANSPORT_FILE) and os.path.isfile(NETSIM_CFG):
            os.remove(SIM_DATA_TRANSPORT_FILE)
        if os.path.isfile(SIM_MO_PROP_FILE_TMP):
            read_mo_cfg_file()
            if SCRIPT_EXECUTION_FLAG:
                if sim_prop_map:
                    get_started_node_info_from_netsim()
                    if SCRIPT_EXECUTION_FLAG:
                        map_simulation_with_sim_name()
                        if writer_map:
                            write_transport_file()
                        else:
                            print ('INFO: No information available to write. Check started nodes and Mo attributes.\nExiting process.')
                else:
                    print ('WARNING: No required information present in file : ' + SIM_MO_PROP_FILE + '\n' + 'Exiting process.')
        else:
            print ('WARNING: Unable to create : ' + SIM_MO_PROP_FILE_TMP + ' file.' + '\n' + 'Exiting process.')
    else:
        print ('ERROR: Configuration file ' + SIM_MO_PROP_FILE + ' not available.')


if __name__ == '__main__': main()

