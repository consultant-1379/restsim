'''
Created on 15 Apr 2016

@author: eaefhiq
'''
from GenstatsSimPmVerifier import GenstatsSimPmVerifier, logging
import os


class GenstatsSpitfireSimPmVerifier(GenstatsSimPmVerifier):
    '''
    classdocs
    '''

    def __init__(self, tmpfs_dir, simname, pm_data_dir):
        '''
        Constructor
        '''
        super(GenstatsSpitfireSimPmVerifier, self).__init__(
            tmpfs_dir, simname, pm_data_dir)
        self.nodename_list = os.listdir(self.tmpfs_dir + self.simname)

    def verify(self):
        self.report_error(self.simname + " misses stats files.",
                          super(
                              GenstatsSpitfireSimPmVerifier, self).get_nodes_file_not_generated,
                          self.nodename_list, self.pm_data_dir)
