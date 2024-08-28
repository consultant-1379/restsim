################################################################################
# COPYRIGHT Ericsson 2022
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 23.01
# Purpose       :  Script to verify if the setup for file generation is working fine for WRAN simulations
# Jira No       :  NSS-41094
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/13746073/
# Description   :  Adding support to check RNC parent and child nodes through respective PM dir
# Date          :  03/11/2022
# Last Modified :  surendra.mattaparthi@tcs.com
####################################################
'''
Created on 20 Jun 2016

@author: eaefhiq
'''
from GenstatsSimPmVerifier import GenstatsSimPmVerifier, logging
import os
import fnmatch
from subprocess import Popen, PIPE
import subprocess

class GenstatsWranSimPmVerifier(GenstatsSimPmVerifier):
    '''
    classdocs
    '''
    @staticmethod
    def run_shell_command(input):
        """ This is the generic method, Which spawn a new shell process to get the job done
        """
        output = Popen(input, stdout=PIPE, shell=True).communicate()[0]
        return output

    def __init__(self, tmpfs_dir, simname, pm_data_dir, rnc_parent_dir=''):
        '''
        Constructor
        '''
        super(GenstatsWranSimPmVerifier, self).__init__(
            tmpfs_dir, simname, pm_data_dir)
        self.nodename_list = os.listdir(self.tmpfs_dir + self.simname)
        self.rnc_parent_dir = rnc_parent_dir
        if 'RNC' in self.simname.upper():
            self.nodename_list = [x for x in self.nodename_list if 'BSC' not in x.upper()]
        self.simnames_full_names = fnmatch.filter(
            os.listdir(self.NETSIM_DBDIR), '*RNC*')
        self.mixed_mode_nodename_list = fnmatch.filter(os.listdir(self.tmpfs_dir + self.simname),'*MSRBS*V2*')
        self.mixed_mode_prbs_nodename_list = fnmatch.filter(os.listdir(self.tmpfs_dir + self.simname),'*PRBS*')
        self.scanner_info = self.get_scanner_info(self.simname, self.simnames_full_names)

    def verify(self):
        '''verify stats files'''
        logging.debug("verify WRAN")
        self.report_error(self.simname + " MISSING STATS FILES ",
                          super(
                              GenstatsWranSimPmVerifier, self).get_nodes_file_not_generated,
                          self.nodename_list, self.pm_data_dir, '*xml*', self.rnc_parent_dir)
        if not any( 'PRBS' in node and 'RNC' in self.simname for node in self.nodename_list):
            logging.debug("verify cell trace")
            self.report_error(self.simname + " MISSING CELLTRACE FILES ",
                          self.get_nodes_file_not_generated_wran,
                          self.nodename_list, self.pm_data_dir, '*_CTR_*', self.rnc_parent_dir)

            logging.debug("verify UE trace")
            self.report_error(self.simname + " MISSING UETRACE FILES ",
                          self.get_nodes_file_not_generated_wran,
                          self.nodename_list, self.pm_data_dir, '*_UETR_*', self.rnc_parent_dir)

            if int(self.simname.replace('RNC','')) < 21:
                logging.debug("verify GPEH")
                self.report_error(self.simname + " MISSING GPEH MP FILES ",
                          self.get_nodes_file_not_generated_wran,
                          self.nodename_list, self.pm_data_dir, '*_gpehfile*', self.rnc_parent_dir)

        result = GenstatsWranSimPmVerifier.verify_scanners_exist_on_sim(self)

        if result:
            logging.warning("NO PREDEFINED SCANNERS ON " + result)

        result = GenstatsWranSimPmVerifier.__extract_nonsuspended_scanners(self, self.scanner_info)

        if len(result) > 0:
            logging.warning("PM SCANNERS ARE ACTIVE/MISSING ON THE FOLLOWING NODES " + str(result))

        self.report_error(self.simname + " TMPFS IS NOT SET ",
                          self.check_tmpfs_setup,
                          self.findKey(self.simname, self.simnames_full_names))

        if self.mixed_mode_nodename_list:
            RNC_SIM_FULL_NAME = fnmatch.filter(os.listdir(self.NETSIM_DBDIR), '*-' + self.simname)[0]
            if 'MULTIRAT' in RNC_SIM_FULL_NAME.upper():
                if 'MSRBS-V2' in self.mixed_mode_nodename_list[0]:
                    if self.isMultiRATSimExists():
                        logging.debug("verify MIXED MODE CELLTRACE")
                        self.report_error(self.simname + " MISSING MULTIRAT CELLTRACE FILES ",super(GenstatsWranSimPmVerifier, self).get_nodes_file_not_generated,
                        self.mixed_mode_nodename_list, self.pm_data_dir, '*_CellTrace_*', self.rnc_parent_dir)
            else:
                MIXED_MODE_DUMPMOTREE_CMD='dumpmotree:moid=1,scope=1,includeattrs=\"Lrat,Wrat\",printattrs;'
                MIXED_MODE_CMD_OUTPUT = self.run_shell_command("printf '.open " + RNC_SIM_FULL_NAME +"\n.select " + self.mixed_mode_nodename_list[0] + "\n" + MIXED_MODE_DUMPMOTREE_CMD + "' | /netsim/inst/netsim_shell")
                if 'Lrat:' in MIXED_MODE_CMD_OUTPUT and 'Wrat:' in MIXED_MODE_CMD_OUTPUT:
                    logging.debug("verify MIXED MODE CELLTRACE")
                    self.report_error(self.simname + " MISSING MIXED MODE CELLTRACE FILES ",super(GenstatsWranSimPmVerifier, self).get_nodes_file_not_generated,
                    self.mixed_mode_nodename_list, self.pm_data_dir, '*_CellTrace_*', self.rnc_parent_dir)

        if self.mixed_mode_prbs_nodename_list:
            RNC_SIM_FULL_NAME = self.run_shell_command("ls " + self.NETSIM_DBDIR + " | grep -w " + self.simname)
            MIXED_MODE_DUMPMOTREE_CMD='dumpmotree:moid=1,scope=1,includeattrs=\"Lrat,Wrat\",printattrs;'
            MIXED_MODE_CMD_OUTPUT = self.run_shell_command("printf '.open " + RNC_SIM_FULL_NAME +"\n.select " + self.mixed_mode_prbs_nodename_list[0] + "\n" + MIXED_MODE_DUMPMOTREE_CMD + "' | /netsim/inst/netsim_shell")
            if 'NodeBFunction' in MIXED_MODE_CMD_OUTPUT and 'ENodeBFunction' in MIXED_MODE_CMD_OUTPUT:
                logging.debug("verify MIXED MODE CELLTRACE")
                self.report_error(self.simname + " MISSING MIXED MODE CELLTRACE FILES for WCDMA PRBS ",
                          super(GenstatsWranSimPmVerifier, self).get_nodes_file_not_generated,
                          self.mixed_mode_prbs_nodename_list, self.pm_data_dir, '*Lrat*', self.rnc_parent_dir)

    def get_nodes_file_not_generated_wran(self, nodename_list, data_dir, reg='*', rnc_parent_dir=''):
        result = super(GenstatsWranSimPmVerifier, self).get_nodes_file_not_generated(
            nodename_list, data_dir, reg, rnc_parent_dir)
        logging.debug(result)
        return [x for x in result if "rbs" not in x.lower()]

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


    def verify_scanners_by_pm_staus(self):
        return self.__extract_nonsuspended_scanners(self.scanner_info)


    def __extract_nonsuspended_scanners(self, scanners_status):
        result = []
        tmp = []
        flag = False
        for line in scanners_status.splitlines():
            if line.startswith('RNC') and not 'not started' in line.lower():
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

    def isMultiRATSimExists(self):
        if os.path.isfile(self.SIM_INFO_FILE):
            with open(self.SIM_INFO_FILE, 'r') as sim_info_file:
                for line in sim_info_file:
                    ele = line.split(":")
                    if ele[0] == self.simname:
                        if len(ele[2]) == 3:
                            return True
                        else:
                            return False
                return False
        else:
            logging.error("File " + self.SIM_INFO_FILE + "is not present. Skipping " + sim + " for verification.")
            return False

    @staticmethod
    def netsim_show_scanners_status(simulation):
        return '''.open %s\n.select network \nshowscanners2;\n''' % (simulation)
