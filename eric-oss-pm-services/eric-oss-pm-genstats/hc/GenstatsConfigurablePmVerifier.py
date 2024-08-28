#!/usr/bin/python

#!/usr/local/bin/python2.7
# encoding: utf-8

################################################################################
# COPYRIGHT Ericsson 2018
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 18.16
# Purpose       :  Script verify for the configuarble event file generation
# Jira No       :  NSS-20364
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/4222660/
# Description   :  Added support for FIVEGRADIONODE pm validation support
# Date          :  8/10/2018
# Last Modified :  abhishek.mandlewala@tcs.com
####################################################

import os, logging
from GenstatsSimPmVerifier import GenstatsSimPmVerifier

class GenstatsConfigurablePmVerifier(GenstatsSimPmVerifier):

    def __init__(self, simulation_name, node_type, nrat_ue_list, deployment):
        self.sim_name = simulation_name
        self.ne = ''
        if node_type == '5GRADIONODE':
            self.ne = 'FIVEGRADIONODE'
        else:
            self.ne = node_type
        self.pms_path = super(GenstatsConfigurablePmVerifier, self).util.getPmsPathForSim(self.sim_name, self.ne)
        self.nodeList = super(GenstatsConfigurablePmVerifier, self).util.getherNodeList(self.pms_path, self.sim_name)
        self.startedNodeList = super(GenstatsConfigurablePmVerifier, self).getStartedNodeListForSim(self.sim_name, self.pms_path, self.nodeList)
        self.eventsPathList = super(GenstatsConfigurablePmVerifier, self).getConfiguredPath(self.sim_name, self.ne, self.startedNodeList)
        self.uePathList = [ os.path.join(started_node, 'c', 'pm_data') + '/'  for started_node in self.startedNodeList ]
        self.nrat_ue_list = nrat_ue_list
        self.deployment = deployment
        self.final_ue_path_list = self.uePathList + self.eventsPathList


    def verify(self):
        celltrace_file_pattern = '*_CellTrace_*'
        uetrace_file_pattern = '*_uetrace_*'
        manifest_file_pattern = '*.manifest'
        if self.eventsPathList:
            self.report_error(self.sim_name + ' MISSING CELLTRACE FILE FOR ', super(GenstatsConfigurablePmVerifier, self).checkFilesNotGeneratedForNodes,self.eventsPathList, self.pms_path, celltrace_file_pattern)
            self.report_error(self.sim_name + ' MISSING MANIFEST FILE FOR ', super(GenstatsConfigurablePmVerifier, self).checkFilesNotGeneratedForNodes,self.eventsPathList, self.pms_path, manifest_file_pattern)
        if self.ne == 'GNODEBRADIO' and self.deployment == 'NSS' and self.sim_name.split('-')[-1] in self.nrat_ue_list:
            if not os.path.isfile('/netsim/genstats/tmp/sim_info.txt'):
                logging.error('/netsim/genstats/tmp/sim_info.txt file not found, while checking UETRACE generation.')
                return
            #The below function is to verify uetrace files for NR simulation for the nodes which they support as per netsim_cfg
            if self.eventsPathList:
               eventPath = []
               uePath = []
               if self.sim_name.split('-')[-1] == 'NR01':
                  list_index = range(1,16,1)
               else:
                  list_index = range(1,6,1)
               #eventsPathList contains list of all the uetrace(cucp, cuup,du) pm paths for all nodes
               for node_check in self.eventsPathList:
                   #Node index contains number i.e. if Node name is NR102gNodebRadio001  then index is 01
                   node_index = int(node_check.split('/')[-3][-2:])
                   if node_index in list_index:
                      eventPath.append(node_check)
               #This is specially for multi nrat since uetrace for multinrat is in /c/pm_data also
               for node_check in self.uePathList:
                   node_index = int(node_check.split('/')[-4][-2:])
                   if node_index in list_index:
                      uePath.append(node_check) 
               self.final_ue_path_list = uePath + eventPath
            with open('/netsim/genstats/tmp/sim_info.txt', 'r') as f:
                for line in f:
                    line = line.strip().split(':')
                    if self.sim_name == line[0]:
                        if len(line) == 3 and line[2].upper() == 'MIXEDNRAT':
                            if uePath and eventPath:
                                self.report_error(self.sim_name + ' MISSING UETRACE FILE FOR ', super(GenstatsConfigurablePmVerifier, self).checkFilesNotGeneratedForNodes, self.final_ue_path_list, self.pms_path, uetrace_file_pattern)
                            else:
                                logging.error('LRAT or NRAT or both path not found for ' + self.sim_name + ', while checking UETRACE generation.')
                        else:
                            if eventPath:
                                self.report_error(self.sim_name + ' MISSING UETRACE FILE FOR ', super(GenstatsConfigurablePmVerifier, self).checkFilesNotGeneratedForNodes, eventPath, self.pms_path, uetrace_file_pattern)
                            else:
                                logging.error('NRAT path not found for ' + self.sim_name + ', while chekcing UETRACE generation.')
                        return
                logging.error('Simulation ' + self.sim_name + ' not found in /netsim/genstats/tmp/sim_info.txt.')

