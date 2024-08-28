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
# Version no    :  NSS 19.06
# Purpose       :  Script to verify if the setup for file generation is working fine for GSM simulations
# Jira No       :  NSS-23812
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/4940257/
# Description   :  Stop PM file generation for LANSWITCH and BSP nodes
# Date          :  13/03/2019
# Last Modified :  kumar.dhiraj7@tcs.com
####################################################

'''
Created on 05 Sep 2018

@author: zdhikum
'''
from GenstatsSimPmVerifier import GenstatsSimPmVerifier, logging
import os, glob
GSM_SIM_INFO_FILE = "/netsim/genstats/tmp/bsc_msc_sim_info.txt"

class GenstatsGsmSimPmVerifier(GenstatsSimPmVerifier):
    '''
    classdocs
    '''

    def __init__(self, tmpfs_dir, simname, pm_data_dir):
        '''
        Constructor
        '''
        self.tmpfs_dir = tmpfs_dir
        self.simname = simname
        self.nodename_list = os.listdir(self.tmpfs_dir + self.simname)
        self.pm_data_dir = pm_data_dir

    def verify(self):

        self.nodename_list = super(GenstatsGsmSimPmVerifier, self).getStartedNodeListForSim(self.simname, self.tmpfs_dir, self.nodename_list)
        bsc_node_list = []
        unsupported_list = []
        msc_blade_type_list = ["BP", "CP", "SPX", "IPLB", "TSC"]
        unsupported_netype = ["BSP", "LANSWITCH", "ECM"]
        if os.path.isfile(GSM_SIM_INFO_FILE):
            with open(GSM_SIM_INFO_FILE) as bsc_msc_sim_info:
                for sim_info in bsc_msc_sim_info:
                    filter_sim_info = sim_info.split("|")
                    if self.simname in sim_info:
                        if 'BSC' in filter_sim_info[2]:
                            bsc_node_list.append(filter_sim_info[1])
                        for blade_type in msc_blade_type_list:
                            if blade_type in filter_sim_info[2]:
                                unsupported_list.append(filter_sim_info[1])
                        for une in unsupported_netype: 
                            if une == filter_sim_info[2].strip():
                                unsupported_list.append(filter_sim_info[1])    
        if unsupported_list:
            self.nodename_list = [node for node in self.nodename_list if node not in unsupported_list]             
        self.report_error(self.simname + " misses stats files.",
                          super(
                              GenstatsGsmSimPmVerifier, self).get_nodes_file_not_generated,
                          self.nodename_list, self.pm_data_dir)

        # Suppressing HC for BSC MTR/Recording files temporarily as it is pushed based and Genstats HC failing randomly due to this 
        '''info_dict = {"MTR":["mgbridata.txt","MTRFIL"], "MRR":["MRR.txt","MRRFIL"],
                     "CER":["CER.txt","CERFIL"], "CTR":["CTR.txt","CTRFILE"],
                     "BAR":["BAR.txt","BARFIL"], "RIR":["RIR.txt","RIRFIL"]}

        if bsc_node_list:
            for rec_type, details in info_dict.iteritems():
                recs_required_bsc_list = []
                for node_name in bsc_node_list:
                    check_file = self.tmpfs_dir + "/" + self.simname + "/" + node_name + "/fs/"
                    if rec_type == "MTR":
                        if os.path.isfile(check_file + details[0]):
                            rr_list = []
                            with open(check_file + details[0]) as datafile:
                                for line_count,line in enumerate(datafile):
                                    if line_count > 2:
                                        if line.strip() and len(line.strip().split()) == 4:
                                            rr_list.append(line.split()[2])

                            if rr_list:
                                recs_required_bsc_list.append(node_name)
                    else:
                        if os.path.isfile(check_file + details[0]):
                            recs_required_bsc_list.append(node_name)

                rec_out_dir = "/apfs/data_transfer/destinations/OSS" + rec_type + "/Ready/"
                if recs_required_bsc_list:
                    self.report_error(self.simname + " misses " + rec_type + " files.",
                            super(GenstatsGsmSimPmVerifier, self).get_nodes_file_not_generated,
                                 recs_required_bsc_list, rec_out_dir, details[1] + '*')'''
