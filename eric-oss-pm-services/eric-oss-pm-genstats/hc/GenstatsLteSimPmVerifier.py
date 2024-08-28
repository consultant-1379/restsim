'''
Created on 13 Apr 2016

@author: eaefhiq
'''
from GenstatsSimPmVerifier import GenstatsSimPmVerifier, logging
import os
import fnmatch


class GenstatsLteSimPmVerifier(GenstatsSimPmVerifier):
    '''
    classdocs
    '''

    def __init__(self, tmpfs_dir, simname, stats_dir, trace_dir, lte_uetrace='', node_type=''):
        '''
        Constructor
        '''
        self.node_type = node_type
        self.stats_dir = stats_dir
        self.trace_dir = trace_dir
        super(GenstatsLteSimPmVerifier, self).__init__(
            tmpfs_dir, simname, stats_dir)
        self.nodename_list = os.listdir(self.tmpfs_dir + self.simname)
        self.lte_uetrace_range = super(
            GenstatsLteSimPmVerifier, self).get_trace_file_range(lte_uetrace)
        self.simnames_full_names = fnmatch.filter(
            os.listdir(self.NETSIM_DBDIR), '*LTE*')
        if self.node_type == "ERBS" :
            self.scanner_info = self.get_scanner_info(self.simname, self.simnames_full_names)


    def verify(self):
        '''verify stats files'''

        if 'MSRBS-V1' in self.node_type or 'PRBS' in self.node_type:
            cell_trace_pattern = '*.Lrat_*'
        else:
            cell_trace_pattern = '*CellTrace_*'
        self.report_error(self.simname + " MISSING STATS FILES ",
                          super(
                              GenstatsLteSimPmVerifier, self).get_nodes_file_not_generated,
                          self.nodename_list, self.stats_dir, '*xml*')

        self.report_error(self.simname + " MISSING CELLTRACE FILES ",
                          super(
                              GenstatsLteSimPmVerifier, self).get_nodes_file_not_generated,
                          self.nodename_list, self.trace_dir, cell_trace_pattern)

        self.report_error(self.simname + " MISSING UETRACE FILES ",
                          self.verifyUEtrace)

        if self.node_type == "ERBS" :
            result = GenstatsLteSimPmVerifier.verify_scanners_exist_on_sim(self)

            if result:
               logging.warning("NO PREDEFINED SCANNERS ON " + result)

            result = GenstatsLteSimPmVerifier.__extract_nonsuspended_scanners(self, self.scanner_info)

            if len(result) > 0:
               logging.warning("PM SCANNERS ARE ACTIVE/MISSING ON THE FOLLOWING NODES " + str(result))

        self.report_error(self.simname + " TMPFS IS NOT SET ",
                          self.check_tmpfs_setup,
                          self.findKey(self.simname, self.simnames_full_names))

    '''verify UE trace '''

    def get_scanner_info(self, simname, simnames_full_names):
        sim_full_name = self.findKey(simname, simnames_full_names)
        sim_scanner_info = self.pipe_to_netsim(self.netsim_show_scanners_status(sim_full_name))[0]
        return sim_scanner_info


    def verify_scanners_exist_on_sim(self):
        result = ''
        scr_info = self.scanner_info.splitlines()
        scr_info_list_length = len(scr_info)
        if 'There are no scanners' in scr_info[scr_info_list_length - 2]:
            result = self.simname
        return result

    def verifyUEtrace(self):
        result = []
        #Current support of UETRACE in NSS is for : LTE01,02,03,04,05,VTFRADIONODE
        if self.simname in self.lte_uetrace_range.keys() or 'VTFRADIONODE' in self.simname.upper():
            uetrace_missing_nodes_list = super(GenstatsLteSimPmVerifier, self).get_nodes_file_not_generated(self.nodename_list, self.trace_dir, reg='*_uetrace_*')
            for nodename in uetrace_missing_nodes_list:
                '''checking if the node set up for the uetrace'''
                '''to convert nodes number to an integer and checking if the integer is in the range that specified on the config parameter.
                e.g. To convert the node LTE01ERBS00004 to an integer is 4;
                for parameter 154kb_ue_trace.gz:LTE01:1:4:1:64  the range is 1 to 4 so the node LTE01ERBS00004 should have UE trace files generated.'''
                if int(nodename[-5:]) in self.lte_uetrace_range[self.simname]:
                    result.append(nodename)
        return result

    def verify_scanners_by_pm_staus(self):
        return self.__extract_nonsuspended_scanners(self.scanner_info)


    def __extract_nonsuspended_scanners(self, scanners_status):
        result = []
        tmp = []
        flag = False
        for line in scanners_status.splitlines():
            if line.startswith('LTE') and not 'not started' in line.lower():
                tmp = []
                tmp = line.strip()[:-1].split()
            elif line.strip() == '':
                flag = False
            elif "=========================" in line:
                flag = True
            elif flag:
                if not 'SUSPENDED' in line.upper():
                    result = result + tmp
                    flag = False
            elif "There are no scanners" in line:
                flag = False
                result = result + tmp
        return result


    @staticmethod
    def netsim_show_scanners_status(simulation):
        return '''.open %s\n.select network \nshowscanners2;\n''' % (simulation)
