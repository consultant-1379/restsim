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
# Version no    :  NSS 21.18
# Purpose       :  Script generates stats templates for ECIM nodes
# Jira No       :  NSS-37568
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/10417947/
# Description   :  DO : PM Support for SBG Nodes
# Date          :  21/10/2021
# Last Modified :  tom.mcgreal@tcs.com
####################################################

"""
Generates GenStats templates for both CPP and COM/ECIM nodes. MIM/MIB files are
extracted from NETSim installation on VM.

edits EutranCellFDD MO within the template configuration files with the predefined
Cell size for both CPP and COM/ECIM nodes

edits the NE configuration files MO content based on NE type for MSRBS-V2 nodes
"""
from DataAndStringConstants import \
    EUTRANCELL_DATA_FILE as GEN_EUTRANCELL_DATA_FILE, PMS_ETC_DIR
from GenericMethods import exit_logs
from _collections import defaultdict
from confGenerator import getCurrentDateTime, run_shell_command
import logging
import math
import os
import re
import sys
import getopt
import json
from shutil import move

LOG_FILE = "/netsim/genstats/logs/genstats_templateGen.log"
format = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(filename=LOG_FILE, format=format, level=logging.INFO)

GSM = "GSM"
LTE = "LTE"
WCDMA = "WCDMA"
MIM_FILE_DIR = "/netsim/inst/zzzuserinstallation/mim_files/"
ECIM_FILE_DIR = "/netsim/inst/zzzuserinstallation/ecim_pm_mibs/"
CFG_FILE_DIR = "/netsim/genstats/xml_cfg/"
TEMPLATES_FILES_1MIN_DIR = "/netsim_users/pms/xml_templates/1/"
TEMPLATES_FILES_5MIN_DIR = "/netsim_users/pms/xml_templates/5/"
TEMPLATE_FILES_15MIN_DIR = "/netsim_users/pms/xml_templates/15/"
TEMPLATE_FILES_30MIN_DIR = "/netsim_users/pms/xml_templates/30/"
TEMPLATE_FILES_60MIN_DIR = "/netsim_users/pms/xml_templates/60/"
TEMPLATE_FILES_720MIN_DIR = "/netsim_users/pms/xml_templates/720/"
TEMPLATE_FILES_1440MIN_DIR = "/netsim_users/pms/xml_templates/1440/"
PM_COUNTERS_SCRIPT = "/netsim_users/pms/bin/getPmCounters"
#PM_COUNTERS_SCRIPT = "/netsim_users/autoo_deploy/bin/cppXmlCfgGenerator.py"
CPPXMLGEN_SCRIPT = "/netsim_users/pms/bin/cppXmlgen"
ECIMXMLGEN_SCRIPT = "/netsim_users/pms/bin/ecimXmlgen"
SIM_DATA_FILE = "/netsim/genstats/tmp/sim_data.txt"
SIM_INFO_FILE = "/netsim/genstats/tmp/sim_info.txt"
XML_FILE_DIR = "/netsim/genstats/xml_templates/1/"
ROUTER_NODES_TYPES = ["R6274", "R6672", "R6673", "R6675", "R6371", "R6471_1", "R6471_2", "R6273"]
ECIM_NODES_TYPES = ["CSCF", "MTAS", "SBG", "VSBG", "SGSN", "SPITFIRE", "MSRBS_V1", "MSRBS_V2", "ESAPC", "PRBS", "TCU03", "TCU04", "MRSV", "HSS_FE", "IPWORKS", "MRFV", "UPG", "WCG", "DSC", "VPP", "VRC", "RNNODE", "EME", "VTFRADIONODE", "5GRADIONODE","VRM", "VRSM","VSAPC", "VTIF", "GNODEBRADIO", "VNSDS", "CONTROLLER6610"] + ROUTER_NODES_TYPES
CPP_NODE_TYPES = ["ERBS", "RNC", "RBS", "RXI", "M_MGW", "MRS"]
MSRBS_NE_TYPES = ["GSM", "LTE", "WCDMA"]
LTE_CELLS_PER_NODE = ["1", "3", "6", "12"]
EPG_FILE_TYPES = ['node', 'pgw', 'sgw']
EPG_RELEASE = ['16A', '16B']
WMG_RELEASE = ['16B']
RNC_CONFIGURATION = {0 : [1, 2, 3, 5, 7], 1 : [4, 6, 8, 9, 10], 2 : [11, 12, 13, 14, 15], 3: [16, 17, 18, 19, 20]}
node_cell_relation_file = "/netsim_users/pms/etc/.node_cell_relation_file"
TOPOLOGY_DATA_FILE = "/netsim_users/pms/etc/topology_info.txt"
relation_file = "/netsim_users/pms/etc/.cell_relation_file"
NODE_CELL_MAPPING = defaultdict(list)
sim_node_map = defaultdict(list)
sim_data_list = []
MO_CSV_FILE = ''
mo_csv_map = defaultdict(lambda : defaultdict(list))
nrm_type = ''
counter_vol = ''
core_nodes_mapping = False
latestCSVFile='/netsim_users/reference_files/NRM4/mo_cfg_320M.csv'
topology_rel_map = defaultdict(lambda : defaultdict(list))
nr_topology_map = defaultdict(lambda : defaultdict(lambda :defaultdict(list)))
sim_info_file_map = defaultdict(lambda : defaultdict(list))
NR_CELL_TYPE = ["NRCellCU", "NRCellDU"]
NR_NODE_TYPE = ["GNODEBRADIO", "5GRADIONODE"]
topology_data_list = []
uniq_node_list = []
cellMap = {}
nodeCellCntMap = {}
ENIQ_STATS_CFG = '/netsim_users/pms/bin/eniq_stats_cfg'
filter_format_tag = ''
filter_ranges_tag = ''
distinct_cell_type = ['EUtranCellFDD', 'EUtranCellTDD', 'NbIotCell']
RNC_CELL_MAPPING_SCRIPT = '/netsim_users/auto_deploy/bin/rncCellMapper.py'
GNODEBRADIO_MIX_SIM_LIST = []
nrat_default_cell_count = 3
DO_SUPPORTED_NODE_LIST = ["SGSN" , "VSAPC", "DSC","GNODEBRADIO", "VSBG", "UPG", "CSCF" , "HSS_FE"]
node_template_file = "/netsim_users/pms/etc/node_template_map/node_template_map.txt"
isDoNrm = False
node_template_map = defaultdict(lambda : defaultdict(list))
TOPOLOGY_SUPPORTED_DO_NETYPE = ['SGSN']
rnc_msrbs_topomap = {}

def clear_existing_log_file(LOG_FILE):
    """ removes existing log entries

        Args:
           param1 (string): log file path
    """
    with open(LOG_FILE, 'w'):
        logging.info("starting template generation process")

def readFilterOSS():
    """It will read ENIQ_STATS_CFG & find the flex filter. """
    global filter_format_tag,filter_ranges_tag
    with open(ENIQ_STATS_CFG) as filter:
        for line in filter:
            if '=' in line and len(line.split('=')) == 2:
                line = line.strip()
            if line.startswith('wranLteFlexFilerFormatTag'):
                filter_format_tag = line.split('=')[1]
            elif line.startswith('wranLteFlexFilterRangesTag'):
                filter_ranges_tag = line.split('=')[1]
            elif filter_format_tag and filter_ranges_tag:
                break


def remove_directories(directories):
    """ deletes directories containing genstats config and template files

       Args:
          param1 (list): list of directories
    """
    for delete_dir in directories:
        logging.info("deleting " + delete_dir)
        os.system("rm -rf " + delete_dir)

def copy_files(source_file, destination_path, destination_file):
    if os.path.isdir(destination_path):
        print getCurrentDateTime() + ' INFO: Copying ' + source_file + ' >> ' + destination_path + destination_file
        logging.info('Copying ' + source_file + ' >> ' + destination_path + destination_file)
        os.system("cp -r " + source_file + " " + destination_path + destination_file)
    else:
        print getCurrentDateTime() + ' WARN: ' + destination_path + ' does not exist. Unable to copy ' + source_file + ' file.'
        logging.warning(destination_path + ' does not exist. Unable to copy ' + source_file + ' file.')


def create_directories(directories):
    """ creates directories required for genstats config and template files

        Args:
           param1 (list): list of directories
    """
    for create_dir in directories:
        logging.info("creating " + create_dir)
        os.system("mkdir -p " + create_dir)


def copy_template_files(source_dir, destination_dir):
    """ copies files from the specified source directory to the specified
            destination directory

        Args:
           param1 (string): source file path
           param2 (string): destination file path

    """
    os.system("cp -rp " + source_dir + ".  " + destination_dir)


def get_sim_data():
    """ retrieves simulation data from /netsim/genstats/tmp/sim_data.txt file

        Returns:
           list: sim data
    """
    try:
       sim_data_file = open(SIM_DATA_FILE, "r")
    except:
       logging.error("cannot find " + SIM_DATA_FILE)
    sim_data_list = sim_data_file.readlines()
    return sim_data_list


def get_eutran_nbiot_relation_for_node(sim_name):
    if NODE_CELL_MAPPING.has_key(sim_name):
        return NODE_CELL_MAPPING.get(sim_name)
    else:
        return LTE_CELLS_PER_NODE


def create_node_template_map():

    '''This method creates a map from the node_template_file
        example - CORE-ST-4.5K-SGSN-1.18-V1x2': defaultdict(<type 'list'>, {'1': 'CORE10SGSN001', '2': 'CORE10SGSN002'}'''

    global node_template_map
    if os.path.isfile(node_template_file) and os.path.getsize(node_template_file) > 0 :
        with open(node_template_file,'r') as fin:
            for line in fin:
                lineElement = line.strip().split('|')
                sim = lineElement[0]
                cfg_id = lineElement[-1]
                node_list = lineElement[1]
                node_template_map[sim][cfg_id] = node_list
    else:
        for sim in sim_data_list:
            sim_data = sim.split();
            node_type = sim_data[5].upper().replace("-", "_")
            if node_type in TOPOLOGY_SUPPORTED_DO_NETYPE:
                logging.error(node_template_file + ' file not found where' + node_type + 'is applicable for topology mapping')
                sys.exit()
        logging.info('No simulation found which required topology mapping')

def generate_ecim_cfg_map():
    """ maps ECIM cfg file names to associated MIM & MIB file names

        Args:
            param1 (list): simulation information

        Returns:
            dictionary : <cfg_file name, [MIM file name, MIB file name]>
    """
    ecim_cfg_map = {}
    cfg_file = ""
    #this set of nodes have mim version  without splitting it with '-'
    ne_list_for_mim_special_handling = ["SGSN", "MSRBS_V2", "GNODEBRADIO", "PRBS", "MRSV", "VNSDS","VSAPC", "CONTROLLER6610", "DSC", "UPG","CSCF","HSS_FE"] +  ROUTER_NODES_TYPES
    for sim in sim_data_list:
         LTE_CELLS_CONF = []
         sim_data = sim.split();
         node_name = sim_data[3]
         sim_name = create_sim_name(sim_data, node_name)
         node_type = sim_data[5].upper()
         node_type = node_type.replace("-", "_")
         if node_type in ECIM_NODES_TYPES:
             mim_file = sim_data[13]
             mib_file = sim_data[15]
             mim_ver = sim_data[7].split("-")[0]

             if any( special_ne in node_type for special_ne in ne_list_for_mim_special_handling):
                 mim_ver = sim_data[7]

             if isDoNrm:
                if node_type in DO_SUPPORTED_NODE_LIST:
                   if node_type not in TOPOLOGY_SUPPORTED_DO_NETYPE:
                      if node_type.lower() == 'gnodebradio':
                           cfg_file = node_type.lower() + "_counters_" + mim_ver + "_" + sim_name.split('-')[-1] + ".cfg"
                      else:
                           cfg_file =node_type.lower() + "_counters_" + mim_ver + ".cfg"
                      ecim_cfg_map[cfg_file] = [mim_file, mib_file, sim_name, node_type]
                   elif sim_name in node_template_map:
                       do_cfg_id_list = node_template_map[sim_name].keys()
                       for id in do_cfg_id_list:
                           cfg_file = node_type.lower() + "_counters_" + mim_ver + ":" + sim_name + ":" + id + ".cfg"
                           ecim_cfg_map[cfg_file] = [mim_file, mib_file,sim_name,node_type]
                   else:
                        logging.error("Cannot generate cfg file for " + sim_name  + " for " + nrm_type)

                else:
                        logging.warning (node_type + " not supported in DO NRM")
                continue
             if "SAPC" == node_type:
                 cfg_file = "sapc_counters_" + mim_ver + ".cfg"
                 ecim_cfg_map[cfg_file] = [mim_file, mib_file, sim_name, node_type]

             if  "VSAPC" == node_type.upper():
                 cfg_file = "vsapc_counters_" + mim_ver + ".cfg"
                 ecim_cfg_map[cfg_file] = [mim_file, mib_file, sim_name, node_type]

             elif "PRBS" in node_type:
                 LTE_CELLS_CONF = get_eutran_nbiot_relation_for_node(sim_name)
                 for cell_size in LTE_CELLS_CONF:
                      cfg_file = "msrbs_v1_counters_" + mim_ver + "_" + cell_size.split('=')[-1] + "CELLS.cfg"
                      if len(cell_size.split('=')) > 1:
                          ecim_cfg_map[cfg_file] = [mim_file, mib_file, cell_size.split('=')[0], node_type]
                      else:
                          ecim_cfg_map[cfg_file] = [mim_file, mib_file, sim_name, node_type]
                 cfg_file = "msrbs_v1_counters_" + mim_ver + ".cfg"
                 ecim_cfg_map[cfg_file] = [mim_file, mib_file, sim_name, node_type]

             elif "MSRBS_V2" in node_type:
                 for msrbs_type in MSRBS_NE_TYPES:
                     if "LTE" in msrbs_type:
                         LTE_CELLS_CONF = get_eutran_nbiot_relation_for_node(sim_name)
                         for cell_size in LTE_CELLS_CONF:
                             cfg_file = msrbs_type.lower() + "_" + node_type.lower() + "_counters_" + mim_ver + "_" + cell_size.split('=')[-1] + "CELLS.cfg"
                             if len(cell_size.split('=')) > 1:
                                 ecim_cfg_map[cfg_file] = [mim_file, mib_file, cell_size.split('=')[0], node_type]
                             else:
                                 ecim_cfg_map[cfg_file] = [mim_file, mib_file, sim_name, node_type]
                     cfg_file = msrbs_type.lower() + "_" + node_type.lower() + "_counters_" + mim_ver + ".cfg"
                     ecim_cfg_map[cfg_file] = [mim_file, mib_file, sim_name, node_type]
             else:
                 if node_type.lower() == 'gnodebradio':
                     if nrm_type != 'MD_1':
                        cfg_file = node_type.lower() + "_counters_" + mim_ver + "_" + sim_name + '_' + str(cellMap[sim_name]) + "CELLS.cfg"
                     else:
                        cfg_file = node_type.lower() + "_counters_" + mim_ver + "_" + sim_name.split('-')[-1] + ".cfg"
                 else:
                     cfg_file = node_type.lower() + "_counters_" + mim_ver + ".cfg"
                 if not cfg_file:
                     continue
                 ecim_cfg_map[cfg_file] = [mim_file, mib_file, sim_name, node_type]
    return ecim_cfg_map


def create_sim_name(sim_data, node_name):
    sim_check = sim_data[1].split('-')[-1]
    if 'LTE' in sim_check and 'ERBS' in node_name:
        return sim_check
    elif 'RNC' in sim_check:
        return sim_check
    else:
        return sim_data[1]


def generate_cpp_cfg_map():
    """ maps CPP cfg file names to associated MIM file names

        Args:
            param1 (list): simulation information

        Returns:
            dictionary : <cfg_file name, MIM file name>
    """
    cpp_cfg_map = {}
    cfg_file = ""
    for sim in sim_data_list:
         LTE_CELLS_CONF = []
         sim_data = sim.split();
         node_name = sim_data[3]
         sim_name = create_sim_name(sim_data, node_name)
         node_type = sim_data[5].upper()
         node_type = node_type.replace("-", "_")

         if node_type in CPP_NODE_TYPES:
             mim_file = sim_data[13]
             mim_pattern = re.compile("([^_]\S?)_(\d+)_(\d+)")
             mim_ver_old = mim_pattern.search(mim_file).group()
             mim_ver = mim_ver_old.replace("_", ".")

             if "RNC" in node_type:
                 node_type = "TYPE_C_RNC"
             if "MGW" in node_type:
                 node_type = "MGW"
                 mim_ver = sim_data[7].split("-")[0]
             if "MRS" in node_type:
                 mim_ver = sim_data[7].split("-")[0]
             if "ERBS" in node_type:
                 LTE_CELLS_CONF = get_eutran_nbiot_relation_for_node(sim_name)
                 for cell_size in LTE_CELLS_CONF:
                     cfg_file = node_type.lower() + "_counters_" + mim_ver + "_" + cell_size.split('=')[-1] + "CELLS.cfg"
                     if len(cell_size.split('=')) > 1:
                         cpp_cfg_map[cfg_file] = [mim_file, cell_size.split('=')[0]]
                     else:
                         cpp_cfg_map[cfg_file] = [mim_file, sim_name ]
             cfg_file = node_type.lower() + "_counters_" + mim_ver + ".cfg"
             if not cfg_file:
                 continue
             cpp_cfg_map[cfg_file] = [mim_file, sim_name]
    return cpp_cfg_map


def edit_EUtranCellFDD_cell_size(cfg_file, node_name, topo_check, ne_type):
    """ Edits the EUtranCellFDD MO within the specified cfg_file with the associated
            cell size as defined in cfg_file name

        Args:
           param1 (string): cfg file name

    """
    EUTRAN_FILE = ''
    LTE_NODE_TYPE_LIST = ['ERBS', 'dg2ERBS', 'pERBS']
    LTE_RELATION_LIST = ['Cdma20001xRttCellRelation', 'EUtranCellRelation', 'GeranCellRelation', 'UtranCellRelation']

    cfg_file_path = CFG_FILE_DIR + cfg_file
    try:
        read_cfg_file = open(cfg_file_path, "r")
    except:
        logging.error("cannot find " + cfg_file_path)

    managed_objects = read_cfg_file.readlines()
    write_cfg_file = open(cfg_file_path, "w")

    if os.path.isfile(GEN_EUTRANCELL_DATA_FILE):
        EUTRAN_FILE = GEN_EUTRANCELL_DATA_FILE

    total_cell_count = 0
    if topo_check:
        if ':' in cfg_file:
            total_cell_count = sum([int(x) for x in cfg_file.split('_')[-1].replace('CELLS.cfg', '').split(':')])
        else:
            total_cell_count = int(cfg_file.split('_')[-1].replace('CELLS.cfg', ''))


    for managed_object in managed_objects:
        cell_type = managed_object.split(',')[0]
        new_cell_value = '1'

        # NbIot conf, then node name value comes in node_name variable else sim name value will come in variable
        if any(cell_type == _cell for _cell in distinct_cell_type):
            if ':' in cfg_file:
                new_cell_value = str(cfg_file.split('_')[-1].replace('CELLS.cfg','').split(':')[distinct_cell_type.index(cell_type)])
            else:
                if cell_type == 'EUtranCellFDD':
                    new_cell_value = str(cfg_file.split('_')[-1].replace('CELLS.cfg',''))
                else:
                    new_cell_value = '0'

        # This block only work when we need to map topology.
        elif topo_check:
            if any(cell_type == rel for rel in LTE_RELATION_LIST):
                if ':' in cfg_file:
                    new_cell_value = str(find_relation_count_for_cfg(relation_file, node_name, cell_type))
                else:
                    for nodeKey in nodeCellCntMap.iterkeys():
                        for ne in LTE_NODE_TYPE_LIST:
                            if node_name + ne in nodeKey and total_cell_count == nodeCellCntMap[nodeKey]:
                                new_cell_value = str(find_relation_count_for_cfg(relation_file, nodeKey, cell_type))
                                break

                if ne_type == 'CPP':
                    new_cell_value = str(math.ceil(int(new_cell_value) / (total_cell_count * 1.0))).split('.')[0]

            else:
                if NODE_CELL_MAPPING:
                    new_cell_value = str(find_mo_info_from_csv_map(retrieve_lte_sim_name(node_name), cell_type, str(total_cell_count)))
                else:
                    new_cell_value = str(find_mo_info_from_csv_map(node_name, cell_type, str(total_cell_count)))

        if new_cell_value != '1':
            if ne_type == 'CPP':
                new_cell_value = ',' + new_cell_value + ','
                managed_object = managed_object.replace(',1,', new_cell_value)
            else:
                new_cell_value = ',' + new_cell_value
                managed_object = managed_object.replace(',1', new_cell_value)

        write_cfg_file.write(managed_object)

    write_cfg_file.close()


def find_mo_info_from_csv_map(sim_name, cell_type, cfg_cell_count):
    mim_ver = ''
    node_type = ''
    index = 0
    key = ''
    other_mo_key = ''
    check = False

    for sim_info in sim_data_list:
        sim_data = sim_info.split()
        if 'LTE' in sim_name:
            if '-' not in sim_name:
                if sim_name == sim_data[1].split('-')[-1]:
                    index = retrieve_csv_index('LTE', cfg_cell_count)
                    check = True
            elif sim_name == sim_data[1]:
                index = retrieve_csv_index('5G', cfg_cell_count)
                check = True
        elif 'RNC' in sim_name:
            if sim_name == sim_data[1].split('-')[-1]:
                if sim_data[5] == 'RNC':
                    index = retrieve_csv_index('RNC', sim_name)
                    check = True
        elif 'GNODEBRADIO' in sim_name.upper():
             if sim_name == sim_data[1]:
                if nrm_type == "NRM6.3":
                   index = retrieve_csv_index('GNODEBRADIO', cfg_cell_count)
                check = True
        else:
            if sim_name == sim_data[1]:
                check = True

        if check:
            node_type = sim_data[5]
            mim_ver = sim_data[7]
            if 'RNC' in sim_name:
                if 'RBS' in node_type:
                    node_type += '(RNC)'
            elif 'GNODEBRADIO' == node_type:
                if sim_name in GNODEBRADIO_MIX_SIM_LIST:
                    node_type += '(MixedNRAT)'
            break

    other_mo_key = node_type + ':Other_MO'

    if mo_csv_map.has_key(node_type + ':' + mim_ver):
        key = node_type + ':' + mim_ver
        return (return_value_from_csv_for_mo(key, other_mo_key, cell_type, index))
    elif mo_csv_map.has_key(node_type + ':default'):
        key = node_type + ':default'
        return (return_value_from_csv_for_mo(key, other_mo_key, cell_type, index))
    elif mo_csv_map.has_key(other_mo_key):
        if mo_csv_map.get(other_mo_key).has_key(cell_type):
            return int(mo_csv_map.get(other_mo_key).get(cell_type)[0])
        else:
            return 1
    else:
        return 1


def return_value_from_csv_for_mo(key, other_mo_key, cell_type, index):
    if mo_csv_map.get(key).has_key(cell_type):
        return int(mo_csv_map.get(key).get(cell_type)[index])
    elif mo_csv_map.has_key(other_mo_key):
        if mo_csv_map.get(other_mo_key).has_key(cell_type):
            return int(mo_csv_map.get(other_mo_key).get(cell_type)[0])
        else:
            return 1
    else:
        return 1


def retrieve_csv_index(sim_type, param):
    if sim_type in ['LTE', 'GNODEBRADIO']:
        if param == '12':
            return 3
        elif param == '3':
            return 1
        elif param == '6':
            return 2
        else:
            return 0
    elif sim_type == '5G':
        return 0
    elif sim_type == 'RNC':
        number = int("{0:0=1d}".format(int(param.replace('RNC', ''))))
        for key_index, values in RNC_CONFIGURATION.iteritems():
            for value in values:
                if number == value:
                    return key_index
        return 4


def retrieve_lte_sim_name(node_name):
    for key, values in sim_node_map.iteritems():
        for value in values:
            if value == node_name:
                return key


def get_uniq_node_list(EUTRANCELL_DATA_FILE):
    """ This method will fetch unique LTE nodes from eutrancellfdd_list.txt.
        Arg : < text file >
        create : uniq_node_list = ['node_1','node_2',..]
    """
    global uniq_node_list
    with open(EUTRANCELL_DATA_FILE, 'r') as inEutran:
        for line_data in inEutran:
            if any(cell in line_data for cell in distinct_cell_type):
                uniq_node_list.append(line_data.split(',')[-1].split('=')[1].split('-')[0].strip())
            else:
                print getCurrentDateTime() + ' ERROR: Cell info not defined properly in ' + EUTRANCELL_DATA_FILE + '. Exiting process.'
                sys.exit(1)
    uniq_node_list = list(set(uniq_node_list))


def find_relation_count_for_cfg(relation_file, node_name, cell_type):
    total_count = 0
    node_name, cell_type = node_name + '-', '=' + cell_type + '='
    with open(relation_file, 'r') as inFile:
        for line in inFile:
            if node_name in line and cell_type in line:
                total_count = total_count + int(line.split('=')[-2])
    return total_count

def edit_cfg_for_do_nodes(cfg_file, topology_data ,sim_name):
    '''Update xml_cfg files for do supported nodes'''

    cfg_id = cfg_file.split(":")[2].replace(".cfg","")
    cfg_file_path = CFG_FILE_DIR + cfg_file
    node = ''
    for id in node_template_map[sim_name].keys() :
       if id == cfg_id:
          node = node_template_map[sim_name][id].split(' ')[0]
          break

    temp_cfg_file =  cfg_file +  "_tmp"
    with open (temp_cfg_file , 'w') as write_cfg:
       with open(cfg_file_path , 'r') as read_cfg:
          for line in read_cfg:
             line_element = line.strip().split(',')
             mo = line_element[0]
             try:
                if mo in topology_data[node]:
                   new_mo_count = topology_data[node][mo]['mo_count']
                   line = mo + ',' + str(new_mo_count) +'\n'
                write_cfg.write(line)
             except KeyError:
                logging.error("Topology data for node key :" + node + "does not exists !!")
             finally:
                write_cfg.flush()
    os.remove(cfg_file_path)
    move(temp_cfg_file,cfg_file_path)


def generate_cpp_cfg_file(cfg_file, mim_file, node_name, topo_check):
    """ maps CPP cfg file names to associated MIM file names

        Args:
            param1 (string): MIM file name

        Returns:
            dictionary : <cfg_file name, MIM file name>
    """
    mim_file_path = MIM_FILE_DIR + mim_file
    cfg_file_path = CFG_FILE_DIR + cfg_file
    os.system(PM_COUNTERS_SCRIPT + " --xml " + mim_file_path + " --outputCfg " + cfg_file_path)
    #os.system(PM_COUNTERS_SCRIPT + ' ' + mim_file_path + ' ' + cfg_file_path)

    if "LTE" in node_name:
        if "CELLS" in cfg_file:
            edit_EUtranCellFDD_cell_size(cfg_file, node_name, topo_check, 'CPP')
        else:
            edit_cfg_file_for_core_nodes(cfg_file, node_name, topo_check, 'CPP')
    elif 'RBS' != cfg_file.split('_')[0].upper() and core_nodes_mapping:
        edit_cfg_file_for_core_nodes(cfg_file, node_name, topo_check, 'CPP')

    try:
        os.path.isfile(cfg_file_path)
        logging.info(cfg_file + " created successfully")
    except:
        logging.error("Failed to create config file for: " + mim_file)


def isSimPureTDD(fileName):
    if 'CELLS' in fileName:
        cells = fileName.split('_')[-1].replace('CELLS.cfg', '').split(':')
        if int(cells[0]) == 0 and int(cells[2]) == 0:
            return 'true'
        else:
            return 'false'
    else:
        return 'false'


def generate_cpp_template_files(cfg_file, mim_file):
    """ generates CPP template files

        Args:
           param1 (string): cfg file name
           param2 (string): MIM file name

    """
    counter_file = cfg_file.replace(".cfg", ".xml")
    isTddOnly = isSimPureTDD(cfg_file)
    if os.path.isfile(TEMPLATE_FILES_15MIN_DIR + counter_file):
        logging.info(counter_file + " already exists")
        print counter_file + " already exists"
    else:
        cntrprop_file = cfg_file.replace(".cfg", ".cntrprop")
        mim_file_path = MIM_FILE_DIR + mim_file
        cfg_file_path = CFG_FILE_DIR + cfg_file
        counter_file_path = TEMPLATE_FILES_15MIN_DIR + counter_file
        cntrprop_file_path = TEMPLATE_FILES_15MIN_DIR + cntrprop_file
        if not filter_format_tag or not filter_ranges_tag:
            os.system(CPPXMLGEN_SCRIPT + " -cfg " + cfg_file_path + " -mom " + mim_file_path + " -out " + counter_file_path + " -prop " + cntrprop_file_path + " -isPureTDD " + isTddOnly)
        else:
            os.system(CPPXMLGEN_SCRIPT + " -cfg " + cfg_file_path + " -mom " + mim_file_path + " -out " + counter_file_path + " -prop " + cntrprop_file_path + " -filter_flex " + filter_format_tag + " -range_filter_flex " + filter_ranges_tag)
    try:
        os.path.isfile(counter_file_path)
    except:
        logging.error("Failed to create config file for: " + mim_file)
    if counter_file.startswith('type_c_rnc') and core_nodes_mapping:
        cmd_result = run_shell_command('python ' + RNC_CELL_MAPPING_SCRIPT + ' ' + mim_file + ' ' + counter_file_path + ' ' + ':'.join(mo_csv_map['RNC:default']['UtranCell']))
        if cmd_result.strip():
            print cmd_result


def get_MSRBS_NE_MO_list(mib_file, node_type):
    """ get MO associated with a specfic node_type within  a given MIB file

        Args:
           param1 (string): mib_file name
           param2 (string): node_type

        Returns:
               list : MO list associated with the specified node_type
    """
    mib_file_path = ECIM_FILE_DIR + mib_file
    MSRBS_V2_MO_file_path = "/tmp/MSRBS_V2_MO.txt"

    os.system(ECIMXMLGEN_SCRIPT + " -mode m -mom " + mib_file_path + " -outCfg " + MSRBS_V2_MO_file_path)

    if node_type == GSM:
        mo_type = ",1,Grat"
    if node_type == LTE:
        mo_type = ",1,Lrat"
    if node_type == WCDMA:
        mo_type = ",1,Wrat"

    parse_file_command = "grep \"" + mo_type + "\" " + MSRBS_V2_MO_file_path
    managed_objects = os.popen(parse_file_command).read()
    managed_objects = managed_objects.replace(mo_type, "")
    node_type_MO_list = managed_objects.strip().split()
    return node_type_MO_list


def remove_multi_standard_MO_in_cfg_file(cfg_file, mib_file):
    """ removes the unnecessary MO's based on the NE type as specified in cfg_file
            i.e. if LTE NE type removes all WCDMA & GSM MO's defined in cfg_file

        Args:
           param1 (string): cfg file name

    """
    WCDMA_MO_list = get_MSRBS_NE_MO_list(mib_file, WCDMA)
    LTE_MO_list = get_MSRBS_NE_MO_list(mib_file, LTE)
    GSM_MO_list = get_MSRBS_NE_MO_list(mib_file, GSM)

    if LTE in cfg_file:
        excluded_MO_list = WCDMA_MO_list + GSM_MO_list
    if WCDMA in cfg_file:
        excluded_MO_list = LTE_MO_list + GSM_MO_list
    if GSM in cfg_file:
        excluded_MO_list = LTE_MO_list + WCDMA_MO_list

    cfg_file_path = CFG_FILE_DIR + cfg_file

    try:
        ecim_cfg_file = open(cfg_file_path, "r")
    except:
        logging.error("cannot find " + cfg_file_path)

    managed_objects = ecim_cfg_file.readlines()
    ecim_cfg_file.close()
    ecim_cfg_file = open(cfg_file_path, "w")

    for managed_object in managed_objects:
        if any(x in managed_object for x in excluded_MO_list):
            continue
        ecim_cfg_file.write(managed_object)
    ecim_cfg_file.close()

    try:
        os.path.isfile(cfg_file_path)
    except:
        logging.error("Failed to create config file: " + cfg_file)


def edit_cfg_file_for_core_nodes(cfg_file, sim_name, topo_check, ne_type):
    cfg_file_path = CFG_FILE_DIR + cfg_file
    try:
        read_cfg_file = open(cfg_file_path, "r")
    except:
        logging.error("cannot find " + cfg_file_path)

    managed_objects = read_cfg_file.readlines()
    write_cfg_file = open(cfg_file_path, "w")
    for managed_object in managed_objects:

        attr_name = managed_object.split(',')[0]
        new_attr_value = '1'

        new_attr_value = str(find_mo_info_from_csv_map(sim_name, attr_name, '0'))
        if 'wcdma_msrbs_v2' in cfg_file and sim_name in rnc_msrbs_topomap  and attr_name == 'EUtranCellFDD' :
          new_attr_value=rnc_msrbs_topomap[sim_name]
        if new_attr_value != '1':
            if ne_type == 'CPP':
                new_attr_value = ',' + new_attr_value + ','
                managed_object = managed_object.replace(',1,', new_attr_value)
            else:
                new_attr_value = ',' + new_attr_value
                managed_object = managed_object.replace(',1', new_attr_value)

        write_cfg_file.write(managed_object)

    write_cfg_file.close()


def edit_cfg_for_gnodebradio(cfg_file, sim):
    cfg_file_path = CFG_FILE_DIR + cfg_file
    try:
        read_cfg_file = open(cfg_file_path, "r")
    except:
        logging.error("cannot find " + cfg_file_path)

    nrm_id = None

    if nrm_type.startswith('NRM'):
        nrm_id = float(nrm_type.replace('NRM', ''))
    else:
        # 0 id is for NSS/DO deployment
        nrm_id = 0

    managed_objects = read_cfg_file.readlines()

    sim_with_gutran = False
    for m_o in managed_objects:
        if 'gutrancell' == m_o.split(',')[0].lower():
            sim_with_gutran = True
            break

    write_cfg_file = open(cfg_file_path, "w")
    value = '0'

    for managed_object in managed_objects:
        attr_name = managed_object.split(',')[0]

        if nrm_id > 5:
            if nrm_id == 6.3:
               value = cfg_file.split('_')[-1].replace('CELLS.cfg', '')
            attr_val = str(find_mo_info_from_csv_map(sim, attr_name, value))
            managed_object = managed_object.replace(',1', ',' + attr_val)
        else:
            if sim_with_gutran:
                if sim in GNODEBRADIO_MIX_SIM_LIST:
                    if attr_name.lower() == 'gutrancell':
                        managed_object = managed_object.replace(',1', ',1080')
                else:
                    if attr_name.lower() == 'gutrancell':
                        managed_object = managed_object.replace(',1', ',230')
        if attr_name in NR_CELL_TYPE:
            managed_object = managed_object.replace(',1', ',' + str(get_unique_cell_count(sim, attr_name)))
        write_cfg_file.write(managed_object)

    write_cfg_file.close()


def get_gnodeb_mixed_sim_list():
    global GNODEBRADIO_MIX_SIM_LIST
    if(os.path.isfile(SIM_INFO_FILE)):
        with open(SIM_INFO_FILE, "r") as sim_info_file:
             for info in sim_info_file:
                filter_info = info.split(":")
                if filter_info[1] == "GNODEBRADIO" and filter_info[2].strip() == "MixedNRAT"  :
                    GNODEBRADIO_MIX_SIM_LIST.append(filter_info[0])

def generate_ecim_cfg_file(cfg_file, mib_file, node_name, topo_check, netype):
    """ generates ECIM template file

        Args:
           param1 (string): cfg file name
           param2 (string): MIB file name

    """
    mib_file_path = ECIM_FILE_DIR + mib_file
    cfg_file_path = CFG_FILE_DIR + cfg_file

    if node_name.strip() in GNODEBRADIO_MIX_SIM_LIST:
        os.system(ECIMXMLGEN_SCRIPT + " -mode c -mom " + mib_file_path + " -outCfg " + cfg_file_path + " -node_type GNODEBRADIO_MIXED")
    else:
        os.system(ECIMXMLGEN_SCRIPT + " -mode c -mom " + mib_file_path + " -outCfg " + cfg_file_path + " -node_type " + netype)
    if "MSRBS_V2" in cfg_file:
        remove_multi_standard_MO_in_cfg_file(cfg_file, mib_file)

    if  "LTE" in node_name:
        if "CELLS" in cfg_file:
            edit_EUtranCellFDD_cell_size(cfg_file, node_name, topo_check, 'ECIM')
        else:
            edit_cfg_file_for_core_nodes(cfg_file, node_name, topo_check, 'ECIM')
    elif 'RNC' not in node_name and core_nodes_mapping and 'gnodebradio' != netype.lower():
        edit_cfg_file_for_core_nodes(cfg_file, node_name, topo_check, 'ECIM')

    elif cfg_file.startswith('wcdma_msrbs_v2') and node_name in rnc_msrbs_topomap :
         edit_cfg_file_for_core_nodes(cfg_file, node_name, topo_check, 'ECIM')

    if node_name in nr_topology_map:
        edit_cfg_for_gnodebradio(cfg_file, node_name)
    if isDoNrm:
        if netype in DO_SUPPORTED_NODE_LIST and netype in TOPOLOGY_SUPPORTED_DO_NETYPE:
            topology_parsed_file = "/netsim_users/pms/etc/topology_info/" + node_name + ".json"
            parsed_file_input = open(topology_parsed_file)
            data = json.load(parsed_file_input)
            parsed_file_input.close()
            edit_cfg_for_do_nodes(cfg_file, data ,node_name)
    try:
        os.path.isfile(cfg_file_path)
        logging.info(cfg_file + " created successfully")
    except:
        logging.error("Failed to create config file for: " + mib_file)


def generate_ecim_template_file(cfg_file, mim_file, mib_file, netype, sim):
    """ maps ECIM cfg file names to associated MIM file names

        Args:
           param1 (string): cfg_file name
           param2 (string): MIM file name
           param3 (string): MIB file name

    """
    counter_file = cfg_file.replace(".cfg", ".xml")
    isTddOnly = isSimPureTDD(cfg_file)
    if os.path.isfile(TEMPLATE_FILES_15MIN_DIR + counter_file):
        logging.info(counter_file + " already exists")
        print counter_file + " already exists"
    else:
        cntrprop_file = cfg_file.replace(".cfg", ".cntrprop")
        mim_file_path = MIM_FILE_DIR + mim_file
        mib_file_path = ECIM_FILE_DIR + mib_file
        cfg_file_path = CFG_FILE_DIR + cfg_file
        counter_file_path = TEMPLATE_FILES_15MIN_DIR + counter_file
        cntrprop_file_path = TEMPLATE_FILES_15MIN_DIR + cntrprop_file
        if sim.strip() in GNODEBRADIO_MIX_SIM_LIST:
            if not filter_format_tag or not filter_ranges_tag:
                os.system(ECIMXMLGEN_SCRIPT + " -mode t -mom " + mib_file_path + " -inCfg " + cfg_file_path + " -inRelFile " + mim_file_path + " -outFile " + counter_file_path + " -prop " + cntrprop_file_path + " -node_type GNODEBRADIO_MIX" + " -isPureTDD " + isTddOnly)
            else:
                os.system(ECIMXMLGEN_SCRIPT + " -mode t -mom " + mib_file_path + " -inCfg " + cfg_file_path + " -inRelFile " + mim_file_path + " -outFile " + counter_file_path + " -prop " + cntrprop_file_path + " -node_type GNODEBRADIO_MIX" + " -filter_flex " + filter_format_tag + " -range_filter_flex " + filter_ranges_tag)
        else:
            if not filter_format_tag or not filter_ranges_tag:
                os.system(ECIMXMLGEN_SCRIPT + " -mode t -mom " + mib_file_path + " -inCfg " + cfg_file_path + " -inRelFile " + mim_file_path + " -outFile " + counter_file_path + " -prop " + cntrprop_file_path + " -node_type " + netype + " -isPureTDD " + isTddOnly)
            else:
                os.system(ECIMXMLGEN_SCRIPT + " -mode t -mom " + mib_file_path + " -inCfg " + cfg_file_path + " -inRelFile " + mim_file_path + " -outFile " + counter_file_path + " -prop " + cntrprop_file_path + " -node_type " + netype + " -filter_flex " + filter_format_tag + " -range_filter_flex " + filter_ranges_tag)
    try:
        os.path.isfile(counter_file_path)
    except:
        logging.error("Failed to create config file for: " + mib_file)

def copy_nexus_templates_file():
    for sim in sim_data_list:
        node_type = sim.split()[5].upper().strip()

        if 'EPG-SSR' in node_type or 'EPG-EVR' in node_type:
            print getCurrentDateTime() + ' INFO: Copying EPG templates.'
            logging.info('Copying EPG templates.')
            for release in EPG_RELEASE:
                for type in EPG_FILE_TYPES:
                    SOURCE_FILE = XML_FILE_DIR + "EPG_" + release + "_" + type + ".template"
                    TARGET_FILE = "epg_counters_" + type + "_" + release + ".xml"
                    if os.path.isfile(SOURCE_FILE):
                        copy_files(SOURCE_FILE, TEMPLATES_FILES_1MIN_DIR, TARGET_FILE)
                        copy_files(SOURCE_FILE, TEMPLATE_FILES_15MIN_DIR, TARGET_FILE)
                        copy_files(SOURCE_FILE, TEMPLATE_FILES_1440MIN_DIR, TARGET_FILE)
                        copy_files(SOURCE_FILE, TEMPLATES_FILES_5MIN_DIR, TARGET_FILE)
                        copy_files(SOURCE_FILE, TEMPLATE_FILES_60MIN_DIR, TARGET_FILE)
                    else:
                        print getCurrentDateTime() + ' ERROR: ' + SOURCE_FILE + ' does not exist.'
                        logging.error(SOURCE_FILE + ' does not exist.')
        elif 'WMG' in node_type:
            print getCurrentDateTime() + ' INFO: Copying WMG templates.'
            logging.info('Copying WMG templates.')
            for wmg_release in WMG_RELEASE:
                SOURCE_FILE = XML_FILE_DIR + "WMG_" + wmg_release + ".template"
                TARGET_FILE = "wmg_counters_" + wmg_release + ".xml"
                if os.path.isfile(SOURCE_FILE):
                        copy_files(SOURCE_FILE, TEMPLATES_FILES_1MIN_DIR, TARGET_FILE)
                        copy_files(SOURCE_FILE, TEMPLATE_FILES_15MIN_DIR, TARGET_FILE)
                        copy_files(SOURCE_FILE, TEMPLATE_FILES_1440MIN_DIR, TARGET_FILE)
                        copy_files(SOURCE_FILE, TEMPLATES_FILES_5MIN_DIR, TARGET_FILE)
                        copy_files(SOURCE_FILE, TEMPLATE_FILES_60MIN_DIR, TARGET_FILE)
                else:
                    print getCurrentDateTime() + ' ERROR: ' + SOURCE_FILE + ' does not exist.'
                    logging.error(SOURCE_FILE + ' does not exist.')

def get_nodes_for_sim(sim_data_list):
    """ This method will map node names with it's simulation.
        Args : <list, list>

        return : sim_node_map = { 'sim_name' : ['node_1', 'node_2', ...] }
    """
    for sim in sim_data_list:
        sim_name = sim.split()[1].split('-')[-1]
        if 'LTE' in sim_name:
            node_pattern = sim.split()[3].replace(sim_name, '')[:-5]
            if 'ERBS' in node_pattern:
                node_pattern = sim_name + node_pattern
                for node in uniq_node_list:
                    if node_pattern in node:
                        sim_node_map[sim_name].append(node)


def findSpecificWord(filename, wordList):
    with open(filename, 'r') as f:
        for line in f:
            if any(_str in line for _str in wordList):
                return True
    return False


def findNodeCell(filename):
    returnMap = {}
    with open(filename, 'r') as f:
        for line in f:
            node = line.split('=')[-1].split('-')[0]
            if returnMap.has_key(node):
                returnMap[node] += 1
            else:
                returnMap[node] = 1
    return returnMap


def get_eutran_nbiot_cell_data(EUTRANCELL_DATA_FILE):
    """ This method will check for single instance of nbiot cell in eutrancellfdd_list.txt, if exists than templates will be created wityh new configuration.
        or else it will create template with old filename format.
        Args : <list, file>
        create : NODE_CELL_MAPPING = { 'sim_name' : ['node=1:2', 'node=2:1'] }
    """
    global nodeCellCntMap
    global NODE_CELL_MAPPING
    print getCurrentDateTime() + ' INFO: Reading ' + EUTRANCELL_DATA_FILE + ' file.'
    get_uniq_node_list(EUTRANCELL_DATA_FILE)
    get_nodes_for_sim(sim_data_list)
    if not findSpecificWord(EUTRANCELL_DATA_FILE, ['EUtranCellTDD', 'NbIotCell']):
        print getCurrentDateTime() + ' INFO: No NbIoTCell/EUtranCellTDD available in ' + EUTRANCELL_DATA_FILE + ' file.'
        nodeCellCntMap = findNodeCell(EUTRANCELL_DATA_FILE)
        return

    print getCurrentDateTime() + ' INFO: NbIoTCell/EUtranCellTDD available in ' + EUTRANCELL_DATA_FILE + ' file.'

    # temp_map = {'node_name' : 0:0:0} , 0thb In
    temp_map = {}
    with open(EUTRANCELL_DATA_FILE, 'r') as the_eutran_file:
        for line in the_eutran_file:
            line = line.strip()
            temp_val_fdd = temp_val_tdd = temp_val_nbiot = ''
            last_index_elements = line.split(',')[-1].split('=')
            node_cell_type = last_index_elements[0]
            node_name = last_index_elements[1].split('-')[0]
            if not temp_map.has_key(node_name):
                temp_map[node_name] = returnValueForCellType(node_cell_type, [0, 0, 0])
            else:
                temp_map[node_name] = returnValueForCellType(node_cell_type, temp_map[node_name])
    for sim_name, node_list in sim_node_map.iteritems():
        for node_name in node_list:
            if temp_map.has_key(node_name):
                NODE_CELL_MAPPING[sim_name].append(node_name + '=' + ':'.join([str(i) for i in temp_map[node_name]]))
            else:
                print getCurrentDateTime() + ' ERROR: Mismatch found in ' + EUTRANCELL_DATA_FILE + 'file for node ' + node_name
                sys.exit(1)
    temp_map.clear()
    write_temp_mapping_file()


def returnValueForCellType(cellType, list_):
    for index, _type in enumerate(distinct_cell_type):
        if _type == cellType:
            list_[index] += 1
            break
    return list_


def write_temp_mapping_file():
    print getCurrentDateTime() + ' INFO: Writing ' + node_cell_relation_file + ' file.'
    write_node_cfg_file = open(node_cell_relation_file, "a+")
    for sim, node_details in NODE_CELL_MAPPING.iteritems():
        for detail in node_details:
            write_node_cfg_file.write(sim + '=' + detail + '\n')
    write_node_cfg_file.close()


def evaluate_topology_data_for_sim(sim_name, other_cell_bool):
    global topology_rel_map
    global topology_data_list
    for line_data in topology_data_list:
        element_list = line_data.split(',')
        node_cell = element_list[-3].split('=')[1]
        rel_data = element_list[-1].split('=')
        rel_name = rel_data[0]
        rel_val = str(rel_data[1]).strip()
        if rel_val:
            topology_rel_map[node_cell][rel_name].append(rel_val)
    if topology_rel_map:
        with open(relation_file, 'a+') as the_file:
            for first_key, first_value in topology_rel_map.iteritems():
                for second_key, second_value in first_value.iteritems():
                    len_of_list = len(second_value)
                    if len_of_list > 0:
                        comma_sep_val = ''
                        node_name = first_key.split('-')[0]
                        total_cell_count = 0
                        if other_cell_bool:
                            for sim_node_data in NODE_CELL_MAPPING.get(sim_name):
                                splitted_data = sim_node_data.split('=')
                                if splitted_data[0] == node_name:
                                    total_cell_count = sum([int(x) for x in splitted_data[1].split(':')])
                                    break
                        else:
                            total_cell_count = nodeCellCntMap[node_name]
                        if total_cell_count == 0:
                            print getCurrentDateTime() + ' ERROR: Cells are not available for ' + node_name
                            sys.exit(1)

                        mo_inst_value = str(math.ceil(find_mo_info_from_csv_map(retrieve_lte_sim_name(node_name), second_key, str(total_cell_count)) / (total_cell_count * 1.0))).split('.')[0]

                        if int(mo_inst_value) > 0:
                            rotation_cnt = 0
                            if len_of_list < int(mo_inst_value):
                                rotation_cnt = len_of_list
                            else:
                                rotation_cnt = int(mo_inst_value)

                            for ele_num in range(0, rotation_cnt):
                                comma_sep_val = comma_sep_val + ',' + second_value[ele_num]

                            the_file.write(sim_name + '=' + first_key + '=' + second_key + '=' + mo_inst_value + '=' + comma_sep_val[1:] + '\n')
                        else:
                            the_file.write(sim_name + '=' + first_key + '=' + second_key + '=' + mo_inst_value + '\n')
                    else:
                        the_file.write(sim_name + '=' + first_key + '=' + second_key + '=' + str(len_of_list) + '\n')
    else:
        print getCurrentDateTime() + ' WARN: Topology data is not matching with either cell or cell relation for sim ' + sim_name
    topology_rel_map.clear()
    del topology_data_list[:]


def appendTopologyFiles(inFile, writeMode):
    global topology_data_list
    patternList = [',Cdma20001xRttCellRelation=',',EUtranCellRelation=',',UtranCellRelation=',',GeranCellRelation=']
    with open(TOPOLOGY_DATA_FILE, writeMode) as fout:
        with open(inFile, 'r') as fin:
            for line in fin:
                if 'EUtranCellFDD=' in line or 'EUtranCellTDD=' in line:
                    if any(_str in line for _str in patternList):
                        line = line.replace('"','')
                        fout.write(line)
                        topology_data_list.append(line)


def create_topology_data():
    """ This method will map the topology and cell relation with node's cell and write it in text file.
        It will only work for DG2 and ERBS nodes.
        Args : list
    """
    print getCurrentDateTime() + ' INFO: Mapping cell relation for sims.'
    topology_data = ''
    writerMode = 'w'
    for sim_info in sim_data_list:
         sim_data = sim_info.split()
         sim_name = sim_data[1]
         node_name = sim_data[3]
         if 'LTE' in sim_name and 'ERBS' in node_name:
             topology_data = "/netsim/netsimdir/" + sim_name + "/SimNetRevision/TopologyData.txt"
             if os.path.isfile(topology_data):
                 appendTopologyFiles(topology_data, writerMode)
                 writerMode = 'a'
                 # Making LTE sim name like netsim_cfg, e.g : LTE01
                 sim_name = sim_name.split('-')[-1]
                 if topology_data_list:
                     if NODE_CELL_MAPPING:
                         evaluate_topology_data_for_sim(sim_name, True)
                     else:
                         evaluate_topology_data_for_sim(sim_name, False)
                 else:
                     print getCurrentDateTime() + ' WARN : Topology data is not available for ' + sim_name
             else:
                 print getCurrentDateTime() + " WARN: cannot find " + topology_data


def create_csv_file_map():
    global mo_csv_map
    ne_type_with_mim_ver = ""
    with open(MO_CSV_FILE, 'r') as fin:
        next(fin)
        for data in fin:
            attrs = ''.join(data.split()).split(',')
            if attrs[0]:
                ne_type_with_mim_ver = attrs[0] + ':' + attrs[1]
            if len(attrs) > 3:
                for index in range(3, len(attrs)):
                    mo_csv_map[ne_type_with_mim_ver][attrs[2]].append(attrs[index])


def topology_creation_check():
    # fetch eutran and nbiot cell info if eutrancellfdd.txt file exists.
    if os.path.isfile(GEN_EUTRANCELL_DATA_FILE) and os.path.getsize(GEN_EUTRANCELL_DATA_FILE) > 0:
        get_eutran_nbiot_cell_data(GEN_EUTRANCELL_DATA_FILE)
        if MO_CSV_FILE:
            return True
        else:
            return False
    else:
        if nrm_type == 'NRM1.2':
            print getCurrentDateTime() + ' WARN: ' + GEN_EUTRANCELL_DATA_FILE + ' file is empty or not found.'
            return False
        else:
            print getCurrentDateTime() + ' ERROR: ' + GEN_EUTRANCELL_DATA_FILE + ' file is empty or not found for deployment type ' + nrm_type
            exit_logs(1)


def get_required_attribute_value(attribute):
    input_file = '/tmp/' + get_hostname()
    if os.path.isfile(input_file):
        with open(input_file, 'r') as provided_file:
            for line in provided_file:
                if line.startswith(attribute) and line.replace(attribute, '').replace('"', '').strip():
                    return line.replace(attribute, '').replace('"', '').strip()
        print getCurrentDateTime() + ' ERROR : Attribute ' + attribute.replace('=', '') + ' is not defined in ' + input_file + ' file.'
        exit_logs(1)
    else:
        print getCurrentDateTime() + ' ERROR: ' + input_file + ' not found.'
        exit_logs(1)


def check_LTE_sims_existance():
    for sim_data in sim_data_list:
        sim_name = sim_data.split()[1]
        node_name = sim_data.split()[3]
        if 'LTE' in sim_name and 'ERBS' in node_name:
            return True
    return False


def get_hostname():
    command = "hostname"
    hostName = run_shell_command(command).strip()
    if isDocker:
        hostName = "netsim"
    return hostName

def get_unique_cell_count(sim_name,network_function):
    cell_list = list(set([ len(cell_elements) for cell_elements in nr_topology_map[sim_name][network_function].values()]))
    if len(cell_list) != 1:
            print 'WARN: Inconsistent cell count (Cell count should be constant for all nodes) for MO : ', network_function,' and simulation ',sim_name
            sys.exit(1)
    else:
            if nrm_type == 'NRM6.3':
               if cell_list[0] not in [1, 3, 6, 12]:
                  print 'WARN: Cell count is not an expected value. It should be a value in [1 3 6 12] for NRM6.3 deployment'
               return cell_list[0]
            else:
               if cell_list[0] != nrat_default_cell_count:
                  print 'WARN: Inconsistent cell count (not equal to expected cell count ) for MO ', network_function, ' and simulation ',sim_name
               return cell_list[0]

def read_sim_info():
    '''This method will read sim_info file and create global map '''
    nr_sim_check = False
    if(os.path.isfile(SIM_INFO_FILE)):
        with open(SIM_INFO_FILE, "r") as sim_info_file:
            for info in sim_info_file:
                filter_info = info.split(":")
                sim_info_file_map[filter_info[0].strip()] = filter_info[1:]
                if filter_info[1].strip().upper() in NR_NODE_TYPE and not nr_sim_check:
                    nr_sim_check = True
    return nr_sim_check


def collect_nr_sims_data():
    '''This Method will check is GNODEBRADIO node and 5GRADIONODE node present inside simulation. '''
    '''Nested map NR_CELL_COUNT contain SIM_NAME:MO_NAME as a key and MO count as value'''
    default_nr_cell_list = ['1','2','3']
    global cellMap
    nr_cell_file = '/netsim_users/pms/etc/nr_cell_data.txt'
    with open(nr_cell_file, 'w') as f_out:
        for sim_name in sim_info_file_map:
            node_type = sim_info_file_map[sim_name][0].strip()
            if node_type in NR_NODE_TYPE:
                topology_data = "/netsim/netsimdir/" + sim_name + "/SimNetRevision/TopologyData.txt"
                if os.path.isfile(topology_data) and os.path.getsize(topology_data) > 0:
                    with open(topology_data) as topology:
                        for line in topology:
                            if line.startswith('ManagedElement='):
                                cell_info = line.split(',')[-1].split('=')
                                cell_mo, node_cell_info  = cell_info[0],cell_info[1].split('-')
                                if cell_mo in NR_CELL_TYPE:
                                    if not nrm_type in ['MD_1','DO']:
                                       f_out.write(line)
                                    nr_topology_map[sim_name][cell_mo][node_cell_info[0]].append(node_cell_info[1])
                                else:
                                    break
                    if not nrm_type in ['MD_1','DO']:
                       nrcellcu_count = get_unique_cell_count(sim_name,'NRCellCU')
                       nrcelldu_count = get_unique_cell_count(sim_name,'NRCellDU')
                       if nrcellcu_count == nrcelldu_count:
                          cellMap[sim_name] = nrcellcu_count
                       else:
                          print 'ERROR: No consistency in cellcount of NRCellCU and NRCellDU'
                          sys.exit(1)
                    ''' If topology file contains only one cell info then add default value 3 for another cells'''
                    for cell in NR_CELL_TYPE:
                        if cell not in nr_topology_map[sim_name]:
                            nr_topology_map[sim_name][cell]['default'] = default_nr_cell_list
                            print ' WARN:', cell, ' MO is missing inside topology file for simulation: ', sim_name, '. Adding default cell count 3.'
                else:
                    nr_topology_map[sim_name]['NRCellCU']['default'],nr_topology_map[sim_name]['NRCellDU']['default'] = default_nr_cell_list,default_nr_cell_list
                    print getCurrentDateTime() + ' WARN : Topology data is not available apply default cell count 3 for simulation ' + sim_name

def core_node_mapping_check():
    global core_nodes_mapping
    if MO_CSV_FILE:
        core_nodes_mapping = True
        if not mo_csv_map:
            create_csv_file_map()


def create_mo_cfg_file_path():
    global MO_CSV_FILE
    if nrm_type != 'NSS' or OSS_enabled == 'True':
        if nrm_type == 'NSS':
            nrm_type_OSS = 'OSS'
            file_name = 'mo_cfg_' + counter_vol + '.csv'
            MO_CSV_FILE = '/netsim_users/reference_files/' + nrm_type_OSS + '/' + file_name
        elif nrm_type == 'DO':
            file_name = 'do_mo_cfg.csv'
            MO_CSV_FILE = '/netsim_users/reference_files/' + nrm_type + '/' + file_name
        else:
            file_name = 'mo_cfg_' + counter_vol + '.csv'
            MO_CSV_FILE = '/netsim_users/reference_files/' + nrm_type + '/' + file_name
        if not os.path.isfile(MO_CSV_FILE):
            print getCurrentDateTime() + ' WARNING: ' + MO_CSV_FILE + ' file not found. Searching default csv file.'
            MO_CSV_FILE = latestCSVFile
            if not os.path.isfile(MO_CSV_FILE):
                print getCurrentDateTime() + ' ERROR: Default csv file ' + MO_CSV_FILE + ' not exists for ' + nrm_type +'. Terminating process.'
                sys.exit(1)

def doCustomConfiguration(inputAttributes):
    for inputAttribute in inputAttributes:
        if inputAttribute == 1:
            global RNC_CONFIGURATION
            if nrm_type == 'NRM5':
                RNC_CONFIGURATION = {0 : [5, 7], 1 : [1, 2, 6, 8, 9, 10], 2 : [3, 11, 12, 13, 14, 15], 3: [16, 17, 18, 19, 20]}
            elif nrm_type == 'NRM5.1':
                RNC_CONFIGURATION = {0 : [5, 7], 1 : [1, 2, 4, 6, 8, 9, 10], 2 : [11, 12, 13, 14, 15], 3: [16, 17, 18, 19, 20], 5:[3]}

def get_rnc_topo_info():
    global rnc_msrbs_topomap
    topo_ref_data="/netsim/netsimdir/sim_name/SimNetRevision/EUtranCellData.txt"
    for sim in sim_data_list:
        sim_name=sim.split()[1].strip()
        if 'RNC' in sim_name.upper() and 'MSRBS' in sim_name.upper():
            ne_type=sim.split()[5].strip()
            if ne_type !="MSRBS-V2":
                continue
            rnc_key=sim_name.split('-')[-1]
            first_ne_name=None
            counter=0
            if rnc_key not in rnc_msrbs_topomap:
                topo_data=topo_ref_data.replace("sim_name",sim_name)
                if os.path.isfile(topo_data) and os.path.getsize(topo_data) > 0:
                    with open(topo_data) as topo_file_object:
                        for line in topo_file_object:
                            line=line.replace(" ","")
                            if line.startswith('SubNetwork=') and line.split(",")[-1].startswith("EUtranCellFDD="):
                                if first_ne_name is None:
                                    first_ne_name="-".join(line.split(",")[-1].split('=')[-1].split("-")[:-1])
                                if "-".join(line.split(",")[-1].split("=")[-1].split("-")[:-1])== first_ne_name:
                                    counter+=1
                    if counter == 0:
                        counter=1
                        print " WARN : cell Information for node " + first_ne_name + " is empty. Hence setting default cellvalue as 1"
                    rnc_msrbs_topomap[rnc_key] = str(counter)
                else:
                    print "WARN : Topology information File for the sim  " + sim_name + " is either empty or not present "

def main(argv):

    isDeletion = True
    isTopology = False
    isLTEpresent = False
    global isDocker
    isDocker = False

    try:
        opts, args = getopt.getopt(argv, "d:e", ["d=", "docker="])
    except getopt.GetoptError:
        print "Cleanup of " + TEMPLATE_FILES_15MIN_DIR + " required"
    for opt, arg in opts:
        if opt == '-h':
            print "TemplateGenerator.py -d <If cleanup of older templates is required> -e <If for docker> "
            sys.exit()
        elif opt in ("-e", "--docker"):
            print "INFO : TemplateGenerator.py running for Docker Environment."
            isDocker = True
        elif opt in ("-d", "--d"):
            print "Cleanup of " + TEMPLATE_FILES_15MIN_DIR + " not required"
            isDeletion = False

    # clear any existing log file entries
    clear_existing_log_file(LOG_FILE)

    # remove existing template files
    directories = [TEMPLATES_FILES_1MIN_DIR, TEMPLATES_FILES_5MIN_DIR, TEMPLATE_FILES_15MIN_DIR, TEMPLATE_FILES_30MIN_DIR, TEMPLATE_FILES_60MIN_DIR, TEMPLATE_FILES_720MIN_DIR, TEMPLATE_FILES_1440MIN_DIR, CFG_FILE_DIR]
    if isDeletion:
        remove_directories(directories)
        create_directories(directories)

    # generate ecim cfg and template files
    global sim_data_list
    sim_data_list = get_sim_data()
    get_rnc_topo_info()

    isLTEpresent = check_LTE_sims_existance()

    if not os.path.isdir(PMS_ETC_DIR):
        os.system("mkdir -p " + PMS_ETC_DIR)

    # remove old files.
    if isDeletion:
        os.system("rm -rf " + node_cell_relation_file)
        os.system("rm -rf " + TOPOLOGY_DATA_FILE)
        os.system("rm -rf " + relation_file)


    global nrm_type, counter_vol, OSS_enabled,nrat_default_cell_count
    nrm_type = get_required_attribute_value('TYPE=')
    counter_vol = get_required_attribute_value('REQUIRED_COUNTER_VOLUME=')
    OSS_enabled = get_required_attribute_value('OSS_enabled=')
    nrat_default_cell_count = int(get_required_attribute_value('DEFAULT_NRAT_CELL_COUNT='))

    ''' 1 is for changing RNC_CONFIGURATION for NRM5 and NRM5.1'''
    doCustomConfiguration([1])

    if OSS_enabled == 'True':
        readFilterOSS()
    create_mo_cfg_file_path()

    if nrm_type == "DO":
        global isDoNrm
        isDoNrm = True

    if isDoNrm:
        os.system('python /netsim_users/auto_deploy/bin/topology_parser.py')
        create_node_template_map()

    if isLTEpresent:
        isTopology = topology_creation_check()
        # map topology based on check
        if isTopology:
            print getCurrentDateTime() + ' INFO: Reading ' + MO_CSV_FILE + ' file.'
            create_csv_file_map()
            create_topology_data()

    core_node_mapping_check()

    get_gnodeb_mixed_sim_list()
    # This will use to check 5G simulation are present or not
    if read_sim_info():
        collect_nr_sims_data()

    print getCurrentDateTime() + ' INFO: Generating templates.'

    # generate ecim cfg and template files
    ecim_cfg_map = generate_ecim_cfg_map()
    for cfg_file in ecim_cfg_map:
        mim_file = ecim_cfg_map[cfg_file][0]
        mib_file = ecim_cfg_map[cfg_file][1]
        generate_ecim_cfg_file(cfg_file, mib_file, ecim_cfg_map[cfg_file][2], isTopology, ecim_cfg_map.get(cfg_file)[3])
        generate_ecim_template_file(cfg_file, mim_file, mib_file, ecim_cfg_map.get(cfg_file)[3], ecim_cfg_map[cfg_file][2])

    # generate cpp cfg and template files
    cpp_cfg_map = generate_cpp_cfg_map()
    for cfg_file in cpp_cfg_map:
        mim_file = cpp_cfg_map[cfg_file][0]
        generate_cpp_cfg_file(cfg_file, mim_file, cpp_cfg_map[cfg_file][1], isTopology)
        generate_cpp_template_files(cfg_file, mim_file)

    # manipulate EPG/WMG templates
    if not os.path.isdir(XML_FILE_DIR):
        print getCurrentDateTime() + ' ERROR: ' + XML_FILE_DIR + ' does not exist. Unable to copy  EPG-SSR/EPG-EVR/WMG templates.'
        logging.error(XML_FILE_DIR + ' does not exist. Unable to copy  EPG-SSR/EPG-EVR/WMG templates.')
        return
    else:
        copy_nexus_templates_file()

    # copy templates
    copy_template_files(TEMPLATE_FILES_15MIN_DIR, TEMPLATES_FILES_1MIN_DIR)
    copy_template_files(TEMPLATE_FILES_15MIN_DIR, TEMPLATE_FILES_1440MIN_DIR)
    copy_template_files(TEMPLATE_FILES_15MIN_DIR, TEMPLATES_FILES_5MIN_DIR)
    copy_template_files(TEMPLATE_FILES_15MIN_DIR, TEMPLATE_FILES_60MIN_DIR)
    copy_template_files(TEMPLATE_FILES_15MIN_DIR, TEMPLATE_FILES_30MIN_DIR)
    copy_template_files(TEMPLATE_FILES_15MIN_DIR, TEMPLATE_FILES_720MIN_DIR)

if __name__ == "__main__":
    main(sys.argv[1:])
