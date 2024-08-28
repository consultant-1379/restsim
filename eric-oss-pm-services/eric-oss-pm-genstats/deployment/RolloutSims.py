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
# Version no    :  NSS 17.15
# Purpose       :  End to end Genstats setup for single simulation
# Jira No       :  NSS-14660
# Gerrit Link   :  https://gerrit.ericsson.se/#/c/2686691/
# Description   :  Removing dirSetup functionality
# Date          :  09/11/2017
# Last Modified :  mathur.priyank@tcs.com
####################################################


import sys
import getopt
import socket
import os
from time import gmtime, strftime
from subprocess import Popen, PIPE
from shutil import copyfile
import getSimulationData as NetsimInfo
import TemplateGenerator as genTemplates
import DataAndStringConstants as Constants
import FetchDeltaSimList as deltaSims

GENSTATS_TMP_DIR_BCKP = "/netsim/genstats/tmp_bckp/"
SIM_DATA_FILE = Constants.SIM_DATA_FILE
SIM_DATA_FILE_BCKP = GENSTATS_TMP_DIR_BCKP + "sim_data.txt"
RADIO_NODE_NE = ["VTFRADIONODE", "5GRADIONODE", "TLS", "VPP", "VRC", "RNNODE", "VRM", "VRSM","VSAPC"]

def run_shell_command(command):
    command_output = Popen(command, stdout=PIPE, shell=True).communicate()[0]
    return command_output


# This method is responsible foe updating netsim_cfg file and also responsible to call pm_setup_stats_recordings.sh once the templates is generated.
def updateCfg(sim_list,stats_dir):
    for sim_name in sim_list:
        print getCurrentDateTime() + " Adding entry in netsim_cfg for sim -> " + sim_name
        hostName = run_shell_command("hostname").strip()
        hostNameUpdated = hostName.replace("-", "_")

		# Process the simulation names if it is LTE or RNC
        if Constants.LTE in sim_name:
            sim_ID = sim_name.split()[-1].split('-')[-1]
            if Constants.LTE in sim_ID:

                sim_name = sim_ID
        elif Constants.RNC in sim_name:
            sim_ID = sim_name.split()[-1].split('-')[-1]
            if Constants.RNC in sim_ID:
                sim_name = sim_ID

        command = "cat " + Constants.NETSIM_CFG_FILE + " | grep -w {0}".format(sim_name)
        output_value = run_shell_command(command).strip()
        if not output_value:
            fin = open(Constants.NETSIM_CFG_FILE)
            fout = open("tmp", "wt")
            mme_list = hostNameUpdated + "_mme_list"
            other_list = hostNameUpdated + "_list"
            for line in fin:
                if Constants.SGSN in sim_name:
                    fout.write( line.replace(mme_list+'=\"', mme_list+'=\"'+sim_name+" ") )
                else:
                    fout.write( line.replace(other_list+'=\"', other_list+'=\"'+sim_name+" ") )
        #if stats_dir:
            #fout.write('\n'+node_name+"_PM_FileLocation="+stats_dir)
            fin.close()
            fout.close()
            os.rename("tmp", Constants.NETSIM_CFG_FILE)  # Rename the new file
def getCurrentDateTime():
    return strftime("%Y-%m-%d %H:%M:%S", gmtime())

#This takes the backup of original sim_data.txt
def backupGenstatsSimData():
    os.system("mkdir -p " + GENSTATS_TMP_DIR_BCKP)
    copyfile(SIM_DATA_FILE,SIM_DATA_FILE_BCKP)

    
def restoreGenstatsSimData(simList):
    sim_string=""
    for sim_name in simList:
        sim_string = sim_string + sim_name + "\\|"
    sim_string = sim_string[:-2]
    os.system("cat " + SIM_DATA_FILE_BCKP + " | grep -v \"" + sim_string + "\" >> " + SIM_DATA_FILE)
    copyfile(SIM_DATA_FILE_BCKP,SIM_DATA_FILE)
    os.remove(SIM_DATA_FILE_BCKP)

    
def check_LTE_sims_existance(simList):
    for sim_name in simList:
        if 'LTE' in sim_name:
            if all(radio_ne not in sim_name.upper() for radio_ne in RADIO_NODE_NE):
                return True
    return False

#This is start point of this script that take two arguments as an parameters one is simulation and another one is
#real path location and process according to that.
def main(argv):

   simList = Constants.EMPTY_STRING
   stats_dir = Constants.EMPTY_STRING
   isCfgUpdate = False
   isGenerate = False
   autoDetect = False
   sim_map = {}

   if (len(argv) < 2):
      print 'USAGE : RolloutSims.py --sim_list <comma separated sim list> --auto_detect <Automatic detect the delta simulations> --path <real file path for stats_dir>[OPTIONAL] --templates <Set True for template generation> --dirSetup <Set it True if Directory creation within /pms_tmpfs is required>[OPTIONAL] --cfgUpdate <Set it True if sim name needs to be added in netsim_cfg>[OPTIONAL]'
      sys.exit(1)
   try:
      opts, args = getopt.getopt(argv,"help:sim_list:path:templates:dirSetup:cfgUpdate:auto_detect",["sim_list=","path=","templates=","dirSetup=","cfgUpdate=","auto_detect="])
   except getopt.GetoptError:
      print 'USAGE : RolloutSims.py --sim_list <comma separated sim list> --auto_detect <Automatic detect the delta simulations> --path <real file path for stats_dir>[OPTIONAL] --templates <Set True for template generation> --dirSetup <Set it True if Directory creation within /pms_tmpfs is required>[OPTIONAL] --cfgUpdate <Set it True if sim name needs to be added in netsim_cfg>[OPTIONAL]'
      sys.exit(1)
   for opt, arg in opts:
      if opt == '-help':
         print 'USAGE : RolloutSims.py --sim_list <comma separated sim list> --auto_detect <Automatic detect the delta simulations> --path <real file path for stats_dir>[OPTIONAL] --templates <Set True for template generation> --dirSetup <Set it True if Directory creation within /pms_tmpfs is required>[OPTIONAL] --cfgUpdate <Set it True if sim name needs to be added in netsim_cfg>[OPTIONAL]'
         sys.exit(1)
      elif opt in ("--sim_list"):
         simList = arg.split(" ")
      elif opt in ("--auto_detect"):
         autoDetect = arg.split(" ")
      elif opt in ("--path"):
         stats_dir = arg
      elif opt in ("--templates"):
         isGenerate = arg
      elif opt in ("--cfgUpdate"):
         isCfgUpdate = arg

   if autoDetect:
      simList = deltaSims.main()
   if not simList:
      print "No Simulations provided / No Delta Simulations found"
      sys.exit(1)

   if isGenerate:
       backupGenstatsSimData()
       sim_map = NetsimInfo.generate_sim_data(simList)
       NetsimInfo.write_sim_data_to_file(simList, sim_map)
       if(check_LTE_sims_existance):
           os.system("python /netsim_users/pms/bin/GetEutranData.py -s")
       os.system("python /netsim_users/auto_deploy/bin/TemplateGenerator.py -d")
       restoreGenstatsSimData(simList)
 
   if isCfgUpdate:
      updateCfg(simList,stats_dir)


if __name__ == "__main__":
   main(sys.argv[1:])
