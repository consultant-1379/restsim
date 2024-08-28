#!/usr/bin/python

################################################################################
# COPYRIGHT Ericsson 2017
#
# The copyright to the computer program(s) herein is the property of
# Ericsson Inc. The programs may be used and/or copied only with written
# permission from Ericsson Inc. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
################################################################################

###################################################
# Version no    :  NSS 17.12
# Purpose       :  This script is used to fetch PM file location for the SIMS which are not part of sim_data.txt
# Jira No       :  NSS-13455
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/2390323/2
# Description   :  /mnt/sd/ecim/enm_performance path is not accessible on netsim node using ISOv1.43.18
# Date          :  06/07/2017
# Last Modified :  tejas.lutade@tcs.com
####################################################

import sys
import os
import getopt
import socket
sys.path.append('/netsim_users/auto_deploy/bin/')
from getSimulationData import *
server_name = socket.gethostname()
STARTED_NODES_FILE = "/tmp/showstartednodes.txt"

def main(argv):

   data_dir = ''
   sim_name = ''
   node_name = ''
   node_type = ''
   mim_ver = ''

   try:
      opts, args = getopt.getopt(argv,"data_dir:sim_name:node_type",["data_dir=","sim_name=","node_type="])
   except getopt.GetoptError:
      sys.exit(1)

   for opt, arg in opts:
      if opt in ("--data_dir"):
         data_dir = arg
      elif opt in ("--sim_name"):
         sim_name = arg
      elif opt in ("--node_type"):
         node_type = arg

   netsim_cmd = ".open " + sim_name + " \n .select network \n .show simnes \n"
   netsim_output = run_netsim_cmd(netsim_cmd, False)
   sim_nodes = netsim_output.split("\n")
   node_name = ''
   for node_info in sim_nodes:
       if server_name in node_info:
           node_name = node_info.split()[0]
           if node_name in open(STARTED_NODES_FILE).read():
               break

   print (get_pmdata_mo_attribute_value(data_dir, sim_name, node_name, node_type, ""))

if __name__ == "__main__":
   main(sys.argv[1:])

