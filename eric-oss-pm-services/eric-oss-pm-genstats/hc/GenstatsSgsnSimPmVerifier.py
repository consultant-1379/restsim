'''
Created on 13 Apr 2016

@author: eaefhiq
'''
from GenstatsSimPmVerifier import GenstatsSimPmVerifier, logging
import os


class GenstatsSgsnSimPmVerifier(GenstatsSimPmVerifier):
    '''
    classdocs
    '''

    def __init__(self, tmpfs_dir, simname, pm_data_dir):
        '''
        Constructor
        '''
        super(GenstatsSgsnSimPmVerifier, self).__init__(
            tmpfs_dir, simname, pm_data_dir)
        self.nodename_list = os.listdir(self.tmpfs_dir + self.simname)
        self.ebs_dir = '/fs/tmp/OMS_LOGS/ebs/ready/'
        self.uetrace_dir = '/fs/tmp/OMS_LOGS/ue_trace/ready/'
        self.ctum_dir = '/fs/tmp/OMS_LOGS/ctum/ready/'

    def verify(self):
        self.nodename_list = super(GenstatsSgsnSimPmVerifier, self).getStartedNodeListForSim(self.simname, self.tmpfs_dir, self.nodename_list)
        self.report_error(self.simname + " misses stats files.",
                          super(
                              GenstatsSgsnSimPmVerifier, self).get_nodes_file_not_generated,
                          self.nodename_list, self.pm_data_dir, '*xml*')

        self.report_error(self.simname + " misses EBS files.",
                          super(
                              GenstatsSgsnSimPmVerifier, self).get_nodes_file_not_generated,
                          self.nodename_list, self.ebs_dir, '*ebs*')

        self.report_error(self.simname + " misses uetrace files.",
                          super(
                              GenstatsSgsnSimPmVerifier, self).get_nodes_file_not_generated,
                          self.nodename_list, self.uetrace_dir, '*ue_trace*')

        self.report_error(self.simname + " misses ctum files.",
                          super(
                              GenstatsSgsnSimPmVerifier, self).get_nodes_file_not_generated,
                          self.nodename_list, self.ctum_dir, '*ctum*')
