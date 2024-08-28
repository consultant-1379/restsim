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
# Version no    :  NSS 22.12
# Purpose       :  Script fetches details of each simulation configured on Netsim
# Jira No       :  NSS-35445
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/13009303/
# Description   :  Adding code changes to take 1st started node info and default pm paths
# Date          :  28/07/2022
# Last Modified :  surendra.mattaparthi@tcs.com
####################################################


"""
Generates  a file /netsim/genstats/tmp/sim_data.txt containing the following data below on each simulation
under /netsim/netsim_dbdir/simdir/netsim/netsimdir/ supported by GenStats

sim_name: <sim_name>  node_name: <node_name> node_type: <node_type> sim_mim_ver: <MIM_version> stats_dir: <stats_filepath> trace: <trace_filepath> mim: <mim file name> mib: <>mib file name

"""
import os
import re
import socket
import subprocess
import sys, getopt
import ConfigParser, logging
from subprocess import PIPE, Popen
from utilityFunctions import Utility


# Defining class objects
util = Utility()
config = ConfigParser.ConfigParser()

NETSIM_DBDIR = "/netsim/netsim_dbdir/simdir/netsim/netsimdir/"
NETSIM_DIR = "/netsim/netsimdir/"
CPP_NE_TYPES = ["M-MGW", "ERBS", "RBS", "RNC", "MRS"]
EPG_NE_TYPE = "EPG"
WMG_NE_TYPE = [ "WMG", "VWMG" ]
SGSN_NE_TYPE = "SGSN"
COMMON_ECIM_NE_TYPES = ["CSCF", "ESAPC", "MTAS", "MRSV", "IPWORKS", "MRFV", "UPG", "WCG", "DSC", "SBG", "VSBG", "EME", "BSP", "VNSDS", "CONTROLLER6610"]
SPITFIRE_NE_TYPES = ["SPITFIRE", "R6274", "R6672", "R6673", "R6675", "R6371", "R6471-1", "R6471-2", "R6273"]
HSS_NE_TYPE = "HSS-FE"
MSRBS_V2_NE_TYPES = ["TCU03", "TCU04", "MSRBS-V2"]
MSRBS_V1_NE_TYPES = ["PRBS", "MSRBS-V1"]
FIVEG_NE_TYPES = ["VPP", "VRC", "RNNODE", "VTFRADIONODE", "5GRADIONODE", "VRM", "VRSM", "VSAPC", "VTIF", "GNODEBRADIO", "PCC", "PCG", "CCSM", "CCDM", "CCRC", "CCPC", "SC", "CCES", "SMSF", "SHARED-CNF", "CIMS" ]
FIVEG_EVENT_FILE_NE_TYPES = ["VTFRADIONODE"]
TRANSPORT_NE_TYPES = [ "FRONTHAUL" ]
YANG_OTHER_NE_TYPES = [ "CCDM", "CCES", "CCSM", "PCC", "PCG", "SC", "CCRC", "CCPC", "SMSF", "SHARED-CNF", "CIMS" ]
SUPPORTED_NE_TYPES = [ "CSCF", "EPG-EVR", "EPG-SSR", "MGW", "MTAS", "LTE", "MSRBS-V1", "MSRBS-V2", "PRBS", "ESAPC", "SBG", "VSBG", "SGSN", "SPITFIRE", "TCU", "RBS", "RNC", "RXI", "VBGF", "HSS-FE", "IPWORKS", "C608", "MRF", "UPG", "WCG", "VPP", "VRC", "RNNODE", "DSC", "WMG", "SIU", "EME", "VTFRADIONODE", "5GRADIONODE", "R6274", "R6672", "R6673", "R6675", "R6371", "R6471-1", "R6471-2", "R6273", "VRM", "VRSM", "VSAPC", "VTIF", "MRS", "GNODEBRADIO", "PCC", "PCG", "CCSM", "CCDM", "CCRC", "CCPC", "SC", "CCES", "VNSDS", "CONTROLLER6610", "SMSF", "SHARED-CNF", "CIMS" ]
SUPPORTED_NE_TYPES_EXTENDED = SUPPORTED_NE_TYPES + [ "STN", "MRFV", "TCU04", "MRSV", "ERBS", "VWMG", "M-MGW"]
ECIM_NE_TYPES = MSRBS_V1_NE_TYPES + MSRBS_V2_NE_TYPES + COMMON_ECIM_NE_TYPES + FIVEG_NE_TYPES + SPITFIRE_NE_TYPES + TRANSPORT_NE_TYPES
ECIM_NE_TYPES.extend((SGSN_NE_TYPE, EPG_NE_TYPE, HSS_NE_TYPE))
EXCEPTIONAL_NODE_TYPES = ["MTAS", "EME"]
# MIB file names not following the expected naming standard for a given NE must be added here
NONSTANDARD_MIB_FILENAME_MAP = { "SBG_16A": "SBG_16A_CORE_V1Mib.xml", "PRBS_15B": "Fmpmpmeventmib.xml","SGSN_16A": "SgsnMmeFmInstances_mp.xml", "SGSN_15B": "SGSN_MME_MIB.xml", "WMG": "WMG_MIB.xml", "PRBS_16A": "fmmib.xml", "EME_16A": "EME_MIB.xml"}
mim_files = []
mib_files = []
GENSTATS_TMP_DIR = "/netsim/genstats/tmp/"
configFileLocation = "/netsim_users/reference_files/DefaultStatsAndEventsPmPaths/"
LOG_PATH = '/netsim_users/pms/logs/'
SIM_PM_PATH_LOG_FILE = LOG_PATH + 'sim_pm_path.log'
SIM_DATA_FILE = GENSTATS_TMP_DIR + "sim_data.txt"
PLAYBACK_CFG = "/netsim_users/pms/bin/playback_cfg"
edeStatsCheck = 'False'
GET_SIMULATION_TYPE_SCRIPT = "/netsim_users/auto_deploy/bin/getSimulationType.py"
GET_BSC_MSC_SIM_INFO_SCRIPT = "/netsim_users/auto_deploy/bin/get_MSC_BSC_Sim_Info.py"
TRIGGER_SIM_PM_PATH_VALIDATION = '/netsim_users/auto_deploy/bin/validateSimPmPath.py'
depl_type="NSS"


def findHostname(isDocker):
    """ gets hostname of the server

        Args:
            param (boolean):

        Returns:
            string: server hostname
    """
    if isDocker:
        return "netsim"
    return socket.gethostname()


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


def get_mim_file(node_type, mim_ver, exact_mim_ver):
    """ gets the associated MIM file for a given NE type and MIM version

        Args:
            param1 (string): node type
            param2 (string): node MIM version
            param3 (string): original node MIM version

        Returns:
            string : mim_file
    """
    mim_file = ""

    if node_type == 'GNODEBRADIO':
        node_type = 'MSRBS-V2'

    shell_command = "echo '.show netype full " + node_type + " " + mim_ver + "' | /netsim/inst/netsim_shell | grep cs_mim -A 1 | grep xml | cut -d\":\" -f2 | cut -d\"'\" -f2"

    mim_file = run_shell_command(shell_command).strip()

    if mim_file:
        return mim_file
    else:
        if node_type.upper() == "ERBS":
            shell_command = "echo '.show netype full " + node_type + " " + exact_mim_ver + "' | /netsim/inst/netsim_shell | grep cs_mim -A 1 | grep xml | cut -d\":\" -f2 | cut -d\"'\" -f2"
            mim_file = run_shell_command(shell_command).strip()

            if mim_file:
                return mim_file

    if mim_ver[0].isalpha() and node_type in CPP_NE_TYPES:
        mim_ver = get_CPP_mim_ver(mim_ver)

    found_mim_list = []
    temp_mim_ver = mim_ver.replace("_", "").upper()
    for mim in mim_files:
        temp_mim = mim.replace("_", "").upper()
        if node_type in mim.upper() and temp_mim_ver in temp_mim.upper():
            found_mim_list.append(mim)
    if len(found_mim_list) == 0:
        print "NO MIM File Found For " + mim_ver + " MIM Version"
    elif len(found_mim_list) == 1:
        return found_mim_list[0]
    else:
        for mf in found_mim_list:
            temp_mf = mf.replace('_','').upper()
            if temp_mf.replace('.xml','').endswith(temp_mim_ver):
                return mf
        print "NO MIM File Found For " + mim_ver + " MIM Version"

    return mim_file


def get_CPP_mim_ver(mim_ver):
    """ returns the CPP MIM version in the expected format necessary to map to the associated MIM file

        Args:
            param1 (string): node MIM version

        Returns:
            string : NE MIM version
    """
    try:
        cpp_mim_pattern = re.compile("(\S?)(\d+)")
        mim_ver = cpp_mim_pattern.search(mim_ver).group()
        mim_ver = mim_ver[:1] + "_" + mim_ver[1:]
        cpp_mim_ver = mim_ver[:3] + "_" + mim_ver[3:]
        return cpp_mim_ver
    except:
        return mim_ver


def get_nonstandard_mim_ver(mim_ver, mim_ver_pattern):
    """ returns NE release & MIM version for NE types that do not conform to a commom standard

        Args:
            param1 (string): node MIM version
            param2 (string): MIM ver regex pattern

        Returns:
            string : NE MIM version
    """
    formatted_mim_ver = mim_ver.replace("-", "_").upper()
    ne_release_pattern = re.compile(mim_ver_pattern)
    try:
        ne_release = ne_release_pattern.search(formatted_mim_ver).group()
        mim_ver_pattern = re.compile("_([V])(\d+)")
        mim_ver = mim_ver_pattern.search(formatted_mim_ver).group()
        nonstandard_mim_ver = ne_release + mim_ver
    except:
        if "CORE_" in formatted_mim_ver:
            nonstandard_mim_ver = formatted_mim_ver.replace("CORE_","")
        else:
            nonstandard_mim_ver = formatted_mim_ver
    return nonstandard_mim_ver


def get_mib_file(node_type, mim_ver):
    """ gets the associated MIB file for a given ECIM node type and MIM version

        Args:
            param1 (string): node type
            param2 (string): node MIM verison

        Returns:
            string : MIB file name
    """
    if node_type == 'GNODEBRADIO':
        node_type = 'MSRBS-V2'

    mib_file = ""

    shell_command = "echo '.show netype full " + node_type + " " + mim_ver + "' | /netsim/inst/netsim_shell | grep pm_mib | grep .xml | cut -d\":\" -f2"
    mib_file = run_shell_command(shell_command).strip()[1:][:-1]

    if mib_file:
        return mib_file

    node_type = node_type.replace("-", "_").upper()

    if "SGSN" in node_type:
        ssgn_mim_ver_pattern = "(\d+)([A-B])_CP(\d+)"
        mim_ver_sgsn_bck = mim_ver.replace("-", "_").upper()

    if  node_type in COMMON_ECIM_NE_TYPES:
         ecim_mim_ver_pattern = "(\d+)([A-B])"
         mim_ver = get_nonstandard_mim_ver(mim_ver, ecim_mim_ver_pattern)

    formatted_mim_ver = mim_ver.replace("-", "_").upper()

    for mib in mib_files:
        formatted_mib = mib.replace("-", "_").upper()
        if node_type in formatted_mib and formatted_mim_ver in formatted_mib:
            return mib
        #Handling for mim_version name containing String "RUI" in case of SGSN.
        #eg. MIM VER : 16A_CP02_RUI_V4 for MIB NAME : SGSN_16A_CP02_RUI_V4.XML
        elif "SGSN" in node_type:
            if node_type in formatted_mib and mim_ver_sgsn_bck in formatted_mib:
                return mib

        elif "PRBS" in node_type and node_type in formatted_mib:
            prbs_mim_ver = formatted_mim_ver.replace("LTE_","")
            if prbs_mim_ver in formatted_mib:
                return mib

        elif "MRSV" in node_type.upper():
            if "BGF" in formatted_mib and mim_ver in formatted_mib:
                return mib

    if mib_file == "":
        node_ver = node_type + "_" + formatted_mim_ver[0:3]
        for node in NONSTANDARD_MIB_FILENAME_MAP:
             if node_ver in node:
                 mib_file = NONSTANDARD_MIB_FILENAME_MAP[node]
                 return mib_file
    return mib_file


def generate_sim_data(sim_list):
    """ get simulation information (nodename, node type/types, mim version/versions) from NETSim
        adds this information to dictionary

        Args:
            param1 (list): simulation list

        Returns:
            dictionary : { <sim_name> : [<simulation/node_info>]}
    """
    sim_info_map = {}
    all_started_nodes = [node.strip().split()[0] for node in run_netsim_cmd(".show started \n").split("\n") if 'netsimdir' in node]
    for sim in sim_list:
        sim_info_map[sim] = []
        netsim_cmd = ".open " + sim + " \n .select network \n .show simnes \n"
        netsim_output = run_netsim_cmd(netsim_cmd, False)
        sim_nodes = netsim_output.split("\n")
        mim_version = ""
        current_mim_version = ""
        default_node_mim_version = ""

        for node_info in sim_nodes:
           if server_name in node_info:
               node_info_list = node_info.split()
               if 'RNC' in sim.upper() and 'BSC' in node_info_list[0].upper():
                   continue
               mim_version = node_info_list[3]
               node_name = node_info_list[0]
               if mim_version != "" and mim_version != current_mim_version:
                  if mim_version != default_node_mim_version:
                      default_node_mim_version = mim_version
                      sim_info_map[sim].append(node_info)
                  if node_name in all_started_nodes:
                      sim_info_map[sim][-1] = node_info
                      current_mim_version = mim_version
    return sim_info_map


def run_shell_command(command):
    command_output = Popen(command, stdout=PIPE, shell=True).communicate()[0]
    return command_output


def write_sim_data_to_file(sim_list, sim_info_map):
    """ writes the simulation data to /netsim/genstats/tmp/sim_data.txt file

        Args:
            param1 (list): simulations list
            param2 (dictionary): { <sim_name> : [<simulation/node_info>]}

    """
    os.system("rm -rf " + GENSTATS_TMP_DIR)
    os.system("mkdir -p " + GENSTATS_TMP_DIR)
    # default values
    stats_dir = "/c/pm_data/"
    trace_dir = "/c/pm_data/"
    mib_file = ""
    mim_file = ""
    file_writer = open(SIM_DATA_FILE, "w+")
    for sim in sim_info_map:
        node_info = sim_info_map[sim]
        for node in node_info:
            node_info_list = node.split()
            node_name = node_info_list[0]
            node_filter_data = node.upper()
            node_type = ''
            node_type_exact = ''
            if 'M-MGW' in node_filter_data and 'EMRS' in node_filter_data:
                node_type_exact = 'MRS'
                node_type = 'MRS'
            else:
                node_type_exact = node_info_list[2]
                if node_info_list[2].upper() == 'MSRBS-V2' and 'GNODEBRADIO' in node_name.upper():
                    node_type = 'GNODEBRADIO'
                else:
                    node_type = node_type_exact.upper()
            if node_type not in SUPPORTED_NE_TYPES_EXTENDED:
                break

            exact_mim_ver = node_info_list[3]
            sim_mim_ver = exact_mim_ver.upper()
            mim_ver = sim_mim_ver

            if node_type == 'VSAPC':
                mim_file = get_mim_file(node_type_exact, mim_ver, exact_mim_ver)
            else:
                mim_file = get_mim_file(node_type, mim_ver, exact_mim_ver)

            if not mim_file:
                if edeStatsCheck == 'True':
                    if "FRONTHAUL" not in node_type:
                        print "WARN : "+ sim +" do not have required MIM File. Please check"
                        continue
                else:
                    print "WARN : "+ sim +" do not have required MIM File. Please check"
                    continue
            if node_type in ECIM_NE_TYPES and node_type not in YANG_OTHER_NE_TYPES:
                if node_type == 'VSAPC':
                    mib_file = get_mib_file(node_type_exact, mim_ver)
                else:
                    mib_file = get_mib_file(node_type, mim_ver)
                if not mib_file:
                    if edeStatsCheck == 'True':
                        if "FRONTHAUL" not in node_type:
                            print "WARN : "+ sim +" do not have required MIB File. Please check"
                            continue
                    else:
                        print "WARN : "+ sim +" do not have required MIB File. Please check"
                        continue
            if node_type in CPP_NE_TYPES:
                data_dir = "performanceDataPath"
            else:
                data_dir = "fileLocation"

            stats_dir = get_pmdata_mo_attribute_value(data_dir, sim, node_name, node_type, mim_ver)

            if not stats_dir:
                print "WARN : "+ sim +" do not have stats_dir set. Please check"
                continue

            if node_type in MSRBS_V1_NE_TYPES or node_type in MSRBS_V2_NE_TYPES or node_type in FIVEG_EVENT_FILE_NE_TYPES:
                trace_dir = get_pmdata_mo_attribute_value("outputDirectory", sim, node_name, node_type, mim_ver)
            else:
                trace_dir = "/c/pm_data/"

            if not trace_dir:
                print "WARN : "+ sim +" do not have trace_dir set. Please check"
                continue

            if not stats_dir.endswith("/"):
                stats_dir = stats_dir + "/"
            if not trace_dir.endswith("/"):
                trace_dir = trace_dir + "/"

            sim_information = "sim_name: " + sim + "\tnode_name: " + node_name + " \tnode_type: " + node_type + "\tsim_mim_ver: " + mim_ver + "\tstats_dir: " + stats_dir + "\ttrace: " + trace_dir + "\tmim: " + mim_file

            if node_type in ECIM_NE_TYPES:
                file_writer.write(sim_information + "\t mib: " + mib_file + "\n")
            else:
                file_writer.write(sim_information + "\n")

    file_writer.close()


def get_playback_list():
    if os.path.isfile(PLAYBACK_CFG):
       PLAYBACK_SIM_LIST = []
       with open(PLAYBACK_CFG, 'r') as cfg:
          for line in cfg:
              if line.startswith('NE_TYPE_LIST'):
                 PLAYBACK_SIM_LIST = line.split("=")[-1].replace("\"","").split()
          if edeStatsCheck == 'True':
              for sim in PLAYBACK_SIM_LIST:
                 if 'FrontHaul' in sim:
                     PLAYBACK_SIM_LIST.remove(sim)
       return PLAYBACK_SIM_LIST

def  get_pmdata_mo_attribute_value(data_dir, sim_name, node_name, node_type, mim_ver):
    """ gets the value of PmService, PmMeasurementCapabilities and PMEventM:FilePullCapabilities MO attribute from NETSim

        Args:
            param1 (string): MO attribute
            param2 (string): simulation name
            param3 (string): node name
            param4 (string): node type
            param5 (string): node mim version

        Returns:
            string : MO attribute value (file path)
    """
    attribute = "/c/pm_data/"
    mo_fdn = ""

    if node_type in CPP_NE_TYPES:
        if "fileLocation" in data_dir:
              mo_attribute = "performanceDataPath="
              mo_fdn = "dumpmotree:moid=\"ManagedElement=1,SystemFunctions=1,PmService=1\",printattrs;"

    if node_type in MSRBS_V1_NE_TYPES:
        mo_id = "1";
        if "15B" in mim_ver:
            mo_id = "2";
        if "fileLocation" in data_dir:
            mo_attribute = data_dir
            mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + node_name + ",ComTop:SystemFunctions=1,MSRBS_V1_PM:Pm=1,MSRBS_V1_PM:PmMeasurementCapabilities=1\",printattrs;"

        if "outputDirectory" in data_dir:
            mo_attribute = data_dir
            mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + node_name + ",ComTop:SystemFunctions=1,MSRBS_V1_PMEventM:PmEventM=1,MSRBS_V1_PMEventM:EventProducer=Lrat,MSRBS_V1_PMEventM:FilePullCapabilities=" + mo_id + "\",printattrs;"

    if node_type in MSRBS_V2_NE_TYPES:
        if "fileLocation" in data_dir:
            mo_attribute = data_dir
            mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + node_name + ",ComTop:SystemFunctions=1,RcsPm:Pm=1,RcsPm:PmMeasurementCapabilities=1\",printattrs;"

        if "outputDirectory" in data_dir:
            mo_attribute = data_dir
            mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + node_name + ",ComTop:SystemFunctions=1,RcsPMEventM:PmEventM=1,RcsPMEventM:EventProducer=Lrat,RcsPMEventM:FilePullCapabilities=2\",printattrs;"


    if SGSN_NE_TYPE in node_type:
        if "fileLocation" in data_dir:
            mo_attribute = data_dir
            mo_fdn = "dumpmotree:moid=\"SgsnMmeTop:ManagedElement=" + node_name + ",SgsnMmeTop:SystemFunctions=1,SgsnMmePM:Pm=1,SgsnMmePM:PmMeasurementCapabilities=1\",printattrs;"


        if "outputDirectory" in data_dir:
            mo_attribute = data_dir
            mo_fdn = "dumpmotree:moid=\"SgsnMmeTop:ManagedElement=" + node_name + ",SgsnMmeTop:SystemFunctions=1,SgsnMmePMEventM:PmEventM=1,SgsnMmePMEventM:EventProducer=1,SgsnMmePMEventM:FilePullCapabilities=1\",printattrs;"


    if node_type in COMMON_ECIM_NE_TYPES:
        managedElementId = node_name
        if "fileLocation" in data_dir:
            mo_attribute = "fileLocation"
            if node_type == "BSP":
                mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + managedElementId + ",ComTop:SystemFunctions=1,DMXC_PM:Pm=1,DMXC_PM:PmMeasurementCapabilities=1\",printattrs;"
            else:
                mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + managedElementId + ",ComTop:SystemFunctions=1,CmwPm:Pm=1,CmwPm:PmMeasurementCapabilities=1\",printattrs;"

    if node_type in SPITFIRE_NE_TYPES:
        mo_attribute = "fileLocation"
        mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=1,ComTop:SystemFunctions=1,Ipos_Pm:Pm=1,Ipos_Pm:PmMeasurementCapabilities=1\",printattrs;"

    if node_type.replace('_','-') in HSS_NE_TYPE:
        mo_attribute = "fileLocation"
        mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=1,ComTop:SystemFunctions=1,ECIM_PM:Pm=1,ECIM_PM:PmMeasurementCapabilities=1\",printattrs;"

    if EPG_NE_TYPE in node_type and 'epg-oi' not in node_type.lower():
        attribute = "/var/log/services/epg/pm/"

    if node_type in WMG_NE_TYPE:
        attribute = "/md/wmg/pm/"

    if node_type in FIVEG_NE_TYPES:
        if "fileLocation" in data_dir:
            mo_attribute = data_dir
            if node_type in YANG_OTHER_NE_TYPES:
                isYANG = checkYANG(sim_name, node_name)
                if isYANG:
                    if node_type in [ "PCC", "PCG", "SHARED-CNF", "SC",  "CIMS" ]:
                        mo_attribute = "file-location"
                        mo_fdn = "dumpmotree:motypes=\"pme:measurement-jobs\",printattrs;"                      
                    # other yang nodes - keep hardcoded
                    else:
                        attribute =  "/PerformanceManagementReportFiles"                     
                # static nodes that could also be yang
                else:
                    if node_type in [ "PCC", "PCG", "SC" ]:
                       mo_fdn = "dumpmotree:motypes=\"Ipos_Pm:PmMeasurementCapabilities\",printattrs;"                   
                    else:
                        mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + node_name + ",ComTop:SystemFunctions=1,Ipos_Pm:Pm=1,Ipos_Pm:PmMeasurementCapabilities=1\",printattrs;"
            # other nodes not in YANG list
            else:
                mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + node_name + ",ComTop:SystemFunctions=1,RcsPm:Pm=1,RcsPm:PmMeasurementCapabilities=1\",printattrs;"
                
        if node_type in FIVEG_EVENT_FILE_NE_TYPES:
           if "outputDirectory" in data_dir:
               mo_attribute = data_dir
               if "RUI" in sim_name:
                   mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + node_name + ",ComTop:SystemFunctions=1,RcsPMEventM:PmEventM=1,RcsPMEventM:EventProducer=Lrat,RcsPMEventM:FilePullCapabilities=2\",printattrs;"
               else:
                   mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + node_name + ",ComTop:SystemFunctions=1,RcsPMEventM:PmEventM=1,RcsPMEventM:EventProducer=VTFrat,RcsPMEventM:FilePullCapabilities=2\",printattrs;"

    if node_type in TRANSPORT_NE_TYPES or "fronthaul" in node_type.lower():
        if "fileLocation" in data_dir:
            mo_attribute = data_dir
            mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=1,ComTop:SystemFunctions=1,OPTOFH_PM:Pm=1,OPTOFH_PM:PmMeasurementCapabilities=1\",printattrs;"

    if not mo_fdn:
        return attribute

    mo_value = get_mo_attribute_value(sim_name,node_name,mo_fdn,mo_attribute,node_type)

    if mo_value:
       if mo_value.startswith("."):
           attribute = mo_value[1:]
       else:
           attribute = mo_value
    else:
        if node_type in COMMON_ECIM_NE_TYPES:
            if any(y in node_type for y in EXCEPTIONAL_NODE_TYPES):
                managedElementId = "1"
                if "fileLocation" in data_dir:
                    mo_attribute = "fileLocation"
                    mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + managedElementId + ",ComTop:SystemFunctions=1,CmwPm:Pm=1,CmwPm:PmMeasurementCapabilities=1\",printattrs;"
                    mo_value = get_mo_attribute_value(sim_name,node_name,mo_fdn,mo_attribute,node_type)
                    if mo_value:
                        attribute = mo_value
        elif node_type in FIVEG_NE_TYPES:
            if node_type in FIVEG_EVENT_FILE_NE_TYPES:
                if "outputDirectory" in data_dir:
                    mo_attribute = data_dir
                    mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + node_name + ",ComTop:SystemFunctions=1,RcsPMEventM:PmEventM=1,RcsPMEventM:EventProducer=Lrat,RcsPMEventM:FilePullCapabilities=2\",printattrs;"
                    mo_value = get_mo_attribute_value(sim_name,node_name,mo_fdn,mo_attribute,node_type)
                    if not mo_value:
                        mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + node_name + ",ComTop:SystemFunctions=1,RcsPMEventM:PmEventM=1,RcsPMEventM:EventProducer=VTFrat,RcsPMEventM:FilePullCapabilities=2\",printattrs;"
                        mo_value = get_mo_attribute_value(sim_name,node_name,mo_fdn,mo_attribute,node_type)
                        if not mo_value:
                            mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + node_name + ",ComTop:SystemFunctions=1,RcsPMEventM:PmEventM=1,RcsPMEventM:EventProducer=VTFratPA1,RcsPMEventM:FilePullCapabilities=2\",printattrs;"
                            mo_value = get_mo_attribute_value(sim_name,node_name,mo_fdn,mo_attribute,node_type)
                            if mo_value:
                                attribute = mo_value
                            else:
                                attribute = '/c/pm_data/'
                        else:
                            attribute = mo_value
                    else:
                        attribute = mo_value

        if node_type.replace('_','-') in HSS_NE_TYPE:
            mo_attribute = "fileLocation"
            managedElementId = node_name
            mo_fdn = "dumpmotree:moid=\"ComTop:ManagedElement=" + managedElementId + ",ComTop:SystemFunctions=1,CmwPm:Pm=1,CmwPm:PmMeasurementCapabilities=1\",printattrs;"
            mo_value = get_mo_attribute_value(sim_name,node_name,mo_fdn,mo_attribute,node_type)
            if mo_value:
                attribute = mo_value
    return attribute

def get_mo_attribute_value(sim_name, node_name, mo_fdn, mo_attribute, node_type):
    attribute = ""
    fetch_attribute="EVENTS"
    if mo_attribute in ["fileLocation", "performanceDataPath", "file-location"]:
       fetch_attribute="STATS" 
    netsim_cmd = ".open " + sim_name + " \n .select " + node_name + " \n " + mo_fdn + " \n"
    mo_attributes = run_netsim_cmd(netsim_cmd, False)
    mo_attributes = mo_attributes.split("\n")
    mo_attribute = mo_attribute + "="
    for atribute in mo_attributes:
        if mo_attribute in atribute:
            attribute = atribute.replace(mo_attribute, '')
    if node_type == 'PRBS' and 'RNC' not in sim_name:
        node_type = 'MSRBS-V1'
    configFileReaderAndLogCreator(depl_type)
    if not attribute.strip() and config.has_option(fetch_attribute,node_type.upper()):
        attribute = config.get(fetch_attribute,node_type.upper())
        logging.warning("Default "+ fetch_attribute +" Pm Path taken for the sim "+ sim_name +" => ['" + attribute + "']")
    return attribute.strip()

def configFileReaderAndLogCreator(depl_type):
    if not os.path.isdir(LOG_PATH):
        try:
            os.makedirs(LOG_PATH, 0755)
        except Exception as x:
            print 'ERROR : Issue while creating ' + LOG_PATH
            print str(x)
    # log file creation
    logging.basicConfig(filename=SIM_PM_PATH_LOG_FILE, filemode='a', format='%(asctime)s : %(levelname)s : %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    # reading default pm paths configuration file
    configFileName = 'NSS.ini' if depl_type == 'NSS' else 'NRM.ini'
    config.read(os.path.join(os.path.dirname(configFileLocation), configFileName))


def checkYANG(sim_name, node_name):
    attribute = ""
    netsim_cmd_port = ".open " + sim_name + " \n .select " + node_name + "\n .show simne \n"
    ne_attributes = run_netsim_cmd(netsim_cmd_port, False)
    ne_attributes = ne_attributes.split("\n")
    port_attribute = "port"
    for attribute in ne_attributes:
        if port_attribute in attribute:
            attribute = attribute.replace(port_attribute, '')
            if "YANG" in attribute:
                return True
            else:
                return False
    return False

def check_mim_and_mib_file():
    global mim_files, mib_files
    mim_location = '/netsim/inst/zzzuserinstallation/mim_files/'
    mib_location = '/netsim/inst/zzzuserinstallation/ecim_pm_mibs/'


    if os.path.isdir(mim_location):
        mim_files = filter(None, os.listdir(mim_location))
    else:
        print 'WARNING : ' + mim_location + ' not available.'

    if os.path.isdir(mib_location):
        mib_files = filter(None, os.listdir(mib_location))
    else:
        print 'WARNING : ' + mib_location + ' not available.'


def fetchSimListToBeProcessed():
    sim_list = []
    sim_list_delete = []
    sim_list_add = []
    sims = os.listdir(NETSIM_DBDIR)
    netsimdir_sims = os.listdir(NETSIM_DIR)
    check_mim_and_mib_file()
    UNSUPPORTED_SIMS = ['CORE-MGW-15B-16A-UPGIND-V1', 'CORE-SGSN-42A-UPGIND-V1', 'PRBS-99Z-16APICONODE-UPGIND-MSRBSV1-LTE99', 'RNC-15B-16B-UPGIND-V1', 'LTEZ9334-G-UPGIND-V1-LTE95', 'LTEZ8334-G-UPGIND-V1-LTE96', 'LTEZ7301-G-UPGIND-V1-LTE97', 'RNCV6894X1-FT-RBSU4110X1-RNC99', 'LTE17A-V2X2-UPGIND-DG2-LTE98', 'LTE16A-V8X2-UPGIND-PICO-FDD-LTE98', 'RNC-FT-UPGIND-PRBS61AX1-RNC01','GSM-FT-BSC_17-Q4_V4X2', 'GSM-ST-BSC-16B-APG43L-X5', 'RNC-FT-UPGIND-PRBS61AX1-RNC31', 'RNC-FT-UPGIND-PRBS61AX1-RNC32', 'RNCV10305X2-FT-RBSUPGIND', 'CORE-ST-DSC-17B-UPGIND-V1X2', 'CORE-FT-LANSWITCHALPINEX2-CORE55', 'CORE-FT-LANSWITCHSUMMIT5IX2-CORE52', 'CORE-FT-LANSWITCHSUMMIT7IX2-CORE54']

    if edeStatsCheck == 'True':
        SUPPORTED_NE_TYPES.append('FRONTHAUL')

    if get_playback_list():
        UNSUPPORTED_SIMS.extend(get_playback_list())


    for sim in sims:
        if sim in netsimdir_sims:

            if any(y in sim.upper() for y in UNSUPPORTED_SIMS):
                sim_list_delete.append(sim)

            elif any(x in sim.upper() for x in SUPPORTED_NE_TYPES):
                sim_list_add.append(sim)

    sim_list = [simType for simType in sim_list_add if simType not in sim_list_delete]
    return sim_list

def main(argv):

    global edeStatsCheck
    global depl_type
    global isDocker
    isDocker = False
    global server_name

    try:
        opts, args = getopt.getopt(argv, "edeStatsCheck:D:c:", ["edeStatsCheck=", "deployment", "docker"])
    except getopt.GetoptError:
        print "[WARN]: Ede Stats check is " + edeStatsCheck

    for opt, arg in opts:
        if opt == '-h':
            print "getSimulationData.py --edeStatsCheck <If Ede Stats setup is required> -d <If deployment type NRM>"
            sys.exit()
        elif opt in ("-c", "--docker"):
            isDocker = True
        elif opt in ('-D', "--deployment"):
            depl_type = arg
            print "INFO : Deployment type is : " + depl_type
        elif opt in ("-edeStatsCheck", "--edeStatsCheck"):
            edeStatsCheck = arg

    server_name = findHostname(isDocker);

    if os.path.isdir(NETSIM_DIR) and os.path.isdir(NETSIM_DBDIR):
        if os.path.isfile(SIM_PM_PATH_LOG_FILE):
            os.remove(SIM_PM_PATH_LOG_FILE)
        sim_list = fetchSimListToBeProcessed()
        sim_info_map = generate_sim_data(sim_list)
        write_sim_data_to_file(sim_list, sim_info_map)
        os.system('python ' + GET_SIMULATION_TYPE_SCRIPT)
        os.system('python ' + TRIGGER_SIM_PM_PATH_VALIDATION )
        os.system('python ' + GET_BSC_MSC_SIM_INFO_SCRIPT)
    else:
        print "ERROR: Either " + NETSIM_DIR + " or " + NETSIM_DBDIR + " directory is not present. Please check."
        sys.exit(1)

if __name__ == "__main__": main(sys.argv[1:])


