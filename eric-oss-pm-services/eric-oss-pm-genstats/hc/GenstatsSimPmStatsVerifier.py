'''
Created on 2 Nov 2016

Generic PM stats verification class for
NE types that only generate PM stats files

@author: ejamfur
'''
from GenstatsSimPmVerifier import GenstatsSimPmVerifier, logging
import os
GSM_HLR_SIM_INFO_FILE = "/netsim/genstats/tmp/bsc_msc_sim_info.txt"
esc_node_strings = ['ERSN', 'ERS_SN_SCU', 'ERS_SN_ESC']

class GenstatsSimPmStatsVerifier(GenstatsSimPmVerifier):
    '''
    classdocs
    '''

    def __init__(self, tmpfs_dir, simname, pm_data_dir):
        '''
        Constructor
        '''
        super(GenstatsSimPmStatsVerifier, self).__init__(
            tmpfs_dir, simname, pm_data_dir)
        self.nodename_list = os.listdir(self.tmpfs_dir + self.simname)


    def verify(self):
        self.nodename_list = super(GenstatsSimPmStatsVerifier, self).getStartedNodeListForSim(self.simname, self.tmpfs_dir, self.nodename_list)
        if "SCEF" in self.simname.upper():
           for path_info in self.pm_data_dir.split("|"):
                file_type = path_info.split(":")[0]
                file_path = path_info.split(":")[1]
                file_regex = path_info.split(":")[2]
                self.report_error(self.simname + " misses " + file_type + " files.",
                     super(GenstatsSimPmStatsVerifier, self).get_nodes_file_not_generated,
                         self.nodename_list, file_path, '*' + file_regex)
        elif any(name in self.simname.upper().replace('-','_') for name in esc_node_strings):
            self.report_error(self.simname + " misses stats files. ",
                 super(GenstatsSimPmStatsVerifier, self).get_nodes_file_not_generated,
                     self.nodename_list, self.pm_data_dir, '*xml')
            self.report_error(self.simname + " misses semaphore files. ",
                 super(GenstatsSimPmStatsVerifier, self).get_nodes_file_not_generated,
                     self.nodename_list, self.pm_data_dir, 'semaphore')
        elif "VAFG" in self.simname.upper():
            self.report_error(self.simname + " misses .tar.gz files. ",
                              super(GenstatsSimPmStatsVerifier, self).get_nodes_file_not_generated,
                              self.nodename_list, self.pm_data_dir, '*tar.gz')
        else:
            if "HLR" in self.simname.upper():
                blade_list = []
                hlr_blade_type_list = ["BP", "CP", "SPX", "IPLB", "TSC"]
                if os.path.isfile(GSM_HLR_SIM_INFO_FILE):
                    with open(GSM_HLR_SIM_INFO_FILE) as bsc_msc_sim_info:
                        for sim_info in bsc_msc_sim_info:
                            filter_sim_info = sim_info.split("|")
                            if self.simname in sim_info:
                                for blade_type in hlr_blade_type_list:
                                    if blade_type in filter_sim_info[2]:
                                       blade_list.append(filter_sim_info[1])
                if blade_list:
                    self.nodename_list = [node for node in self.nodename_list if node not in blade_list]

            self.report_error(self.simname + " misses stats files.",
                          super(
                              GenstatsSimPmStatsVerifier, self).get_nodes_file_not_generated,
                          self.nodename_list, self.pm_data_dir)
