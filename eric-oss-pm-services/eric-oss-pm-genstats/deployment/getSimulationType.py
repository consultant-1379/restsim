#!/usr/bin/python
################################################################################
# COPYRIGHT Ericsson 2019
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 21.15
# Purpose       :  This script is used to create mapping file which includes mapping of <SIM_NAME>:<SIM_TYPE> as one time activity to remove sim name dependency at run time
# Jira No       :  NSS-36041
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/10499199
# Description   :  Adding support for Shared-CNF node type
# Date          :  04/08/2021
# Last Modified :  vadim.malakhovski@tcs.com
####################################################

import os
import sys
import re
from _collections import defaultdict
from DataAndStringConstants import SIM_DATA_FILE
from confGenerator import run_shell_command

simInfo = '/netsim/genstats/tmp/sim_info.txt'
four_g_lte_type = ['ERBS', 'MSRBS-V2', 'PRBS']
rnc_child_type = ['PRBS', 'RBS', 'MSRBS-V2']
radio_node_ne = ["VTFRADIONODE", "5GRADIONODE", "TLS", "VRM", "VRSM", "VSAPC", "VTIF", "PCC", "PCG", "SHARED-CNF", "CCSM", "CCDM", "CCRC", "CCPC", "SC", "CCES"]
router_node_type = ['R6274', 'R6672', 'Router6672', 'R6673', 'Router6675', 'R6675', 'Router6371', 'R6371', 'R6471-1', 'Router6471-1', 'Router6471-2', 'R6471-2', 'R6273']
simDataMap = defaultdict(list)
simToSimType = {}
netsim_script = '/netsim/inst/netsim_shell'

def get_mo_attribute_value(mo_fdn):
    output = run_shell_command(mo_fdn).strip()
    if output.isdigit() and int(output) > 1:
        return True
    return False

def writeSimInfo():
    with open(simInfo, 'w') as file:
        for sim_name, sim_type in simToSimType.iteritems():
            file.write(sim_name + ':' + sim_type + '\n')

def identifySimulation():
    global simToSimType
    node_name = None
    ne_type = None
    for sim_name, sim_info in simDataMap.iteritems():
        ne_type = sim_info[0]
        node_name = sim_info[1]
        if 'LTE' in sim_name.upper():
            val_acquired = False
            for node_type in four_g_lte_type:
                if ne_type.upper() == node_type:
                    val_acquired = True
                    # key of simToSimType for LTE 4G sim is small name like LTE100.
                    if node_type == 'MSRBS-V2':
                        mo_fdn = 'echo "dumpmotree:moid=\\"ComTop:ManagedElement=' + node_name + ',ReqEquipment:Equipment=1\\";" | ' + netsim_script +  ' -sim ' + sim_name + ' -ne ' + node_name + ' | grep "DiLink" | wc -l'
                        dualBbCheck = run_shell_command(mo_fdn).strip()
                        if dualBbCheck == "1":
                            simToSimType[node_name.upper().split('DG2ERBS')[0]] = 'LTE:DualBB'
                        else:
                            simToSimType[node_name.upper().split('DG2ERBS')[0]] = 'LTE'
                    elif node_type == 'PRBS':
                        simToSimType[node_name.upper().split('PERBS')[0]] = 'LTE'
                    else:
                        simToSimType[node_name.upper().split(node_type)[0]] = 'LTE'
            if not val_acquired:
                if any(node_type in sim_name.upper() for node_type in radio_node_ne):
                    simToSimType[sim_name] = ne_type.upper()
                else:
                    simToSimType[node_name.upper().split(ne_type.upper())[0]] = ne_type.upper()
        elif 'GNODEBRADIO' in sim_name.upper():
            moCmd = 'echo "dumpmotree:moid=\\"ComTop:ManagedElement=' + node_name + '\\",scope=1;" | ' + netsim_script +  ' -sim ' + sim_name + ' -ne ' + node_name + ' | egrep "Lrat:" | wc -l'
            multiRatCheck = run_shell_command(moCmd).strip()
            if multiRatCheck == "1" :
                simToSimType[sim_name] = 'GNODEBRADIO:MixedNRAT'
            else :
                simToSimType[sim_name] = 'GNODEBRADIO'
        elif 'RBS' in sim_name.upper() and 'RNC' not in sim_name.upper() and 'RBS' == ne_type.upper():
            simToSimType[sim_name] = 'RBS'
        elif 'RNC' in sim_name.upper():
            if ne_type.upper() == 'RNC':
                if 'UPGIND' not in sim_name.upper():
                    simToSimType[node_name.upper()] = 'WRAN'
                else:
                    sim_content = sim_name.upper().replace('-', '_').split('_')
                    for content in sim_content[::-1]:
                        if 'RNC' in content and content.replace('RNC', '').isdigit():
                            simToSimType[content] = 'WRAN'
            else:
                if 'MULTIRAT' in sim_name.upper() and ne_type.upper() == 'MSRBS-V2':
                    mo_fdn = 'echo "dumpmotree:moid=\\"ComTop:ManagedElement=' + node_name + ',ReqEquipment:Equipment=1\\";" | ' + netsim_script +  ' -sim ' + sim_name + ' -ne ' + node_name + ' | grep "ReqFieldReplaceableUnit:FieldReplaceableUnit" | wc -l'
                    if get_mo_attribute_value(mo_fdn):
                        simToSimType[node_name.upper().split(ne_type)[0]] = 'WRAN:DualMultiRAT'
                    else:
                        simToSimType[node_name.upper().split(ne_type)[0]] = 'WRAN:SingleMultiRAT'
                else:
                    for node_type in rnc_child_type:
                        if node_type == ne_type.upper():
                            simToSimType[node_name.upper().split(node_type)[0]] = 'WRAN'
        elif 'MGW' in ne_type.upper():
            simToSimType[sim_name] = 'MGW'
        elif any(type.upper() == ne_type.upper() for type in router_node_type):
            simToSimType[sim_name] = ne_type.upper().replace('OUTER', '')
        elif 'HSS' in sim_name.upper() and 'HSS' in ne_type.upper():
            simToSimType[sim_name] = 'HSS'
        elif 'MRSV' == ne_type.upper():
            simToSimType[sim_name] = 'VBGF'
        elif ne_type.upper() == 'TCU04' and 'C608' in sim_name.upper():
            simToSimType[sim_name] = 'C608'
        elif 'MRFV' == ne_type.upper() or 'MRF' == ne_type.upper():
            simToSimType[sim_name] = 'MRF'
        elif 'WMG' == ne_type.upper() or 'VWMG' == ne_type.upper():
            simToSimType[sim_name] = 'WMG'
        elif 'DOG' in sim_name.upper():
            simToSimType[sim_name] = 'GSM_DG2'
        else:
            simToSimType[sim_name] = ne_type.upper()
                
def createSimDataMap():
    global simDataMap
    with open(SIM_DATA_FILE, 'r') as f:
        for lineData in f:
            lineData = re.sub(' +', ' ', lineData)
            lineElements = lineData.split()
            # lineElements[1] = simulation name , lineElements[3] = node name and lineElements[5] = node type.
            simDataMap[lineElements[1]] = [lineElements[5], lineElements[3]]

def main():
    if os.path.isfile(SIM_DATA_FILE):
        if os.path.isfile(simInfo):
            os.remove(simInfo)
        createSimDataMap()
        identifySimulation()
        if simToSimType:
            writeSimInfo()
    else:
        print 'ERROR: ' + SIM_DATA_FILE + ' does not exists.'
    
if __name__ == '__main__':
    main()

