#!/usr/bin/python

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
# Purpose       :  To store the netsim dump mo tree commands
# Jira No       :  NSS-20364
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/4222660/
# Description   :  Dump mo tree command for 5GRADIONODE
# Date          :  8/10/2018
# Last Modified :  abhishek.mandlewala@tcs.com
####################################################

class DumpMoTreeCommand:

    getEventProducer = 'dumpmotree:moid="ComTop:ManagedElement=REPLACE_NODE_NAME,ComTop:SystemFunctions=1,RcsPMEventM:PmEventM=1",scope=1;'
    getCelltraceOutputDir = 'dumpmotree:moid="ComTop:ManagedElement=REPLACE_NODE_NAME,ComTop:SystemFunctions=1,RcsPMEventM:PmEventM=1,RcsPMEventM:EventProducer=EVENT_PRODUCER_ID,RcsPMEventM:FilePullCapabilities=REPLACE_PM_FILE_PULL_CAP_ID",printattrs;'
    
    gNodeBRadioNode_nrat_set_command_map = {'setOne' : ['dumpmotree:moid="ComTop:ManagedElement=REPLACE_NODE_NAME,GNBDU:GNBDUFunction=1",printattrs;', 'GNBDUFunctionId'] ,
                                     'setTwo' : ['dumpmotree:moid="ComTop:ManagedElement=REPLACE_NODE_NAME,NratGNodeBRpFunction:GNodeBRpFunction=1",printattrs;', 'GNodeBRpFunctionId']}


