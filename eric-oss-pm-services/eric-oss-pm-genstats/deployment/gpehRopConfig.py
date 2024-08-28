#!/usr/bin/python
import sys
import socket
from tempfile import mkstemp
import subprocess
import os
fileToSearch = "/netsim/netsim_cfg"
text = 'TYPE="NSS"'

os.system ("cp /netsim/netsim_cfg /netsim/netsim_cfg_NRM.bak")
os.chdir("/netsim/")
abs_path = "/netsim/netsim_cfg_temp"
os.system("touch /netsim/netsim_cfg_temp")
new_cfg = open(abs_path,'w')
old_file = open(fileToSearch)
var = sys.argv[1]

#Get hostname of server
def get_hostname():
    netsim_cfg_file = socket.gethostname().split('.')[0]
    if "atvts" in netsim_cfg_file:
        netsim_cfg_file = "netsim"
    return netsim_cfg_file

print "[INFO]: Initiated GPEH setup processing."

#Main
if int(var) == 1:
        print "[INFO]: Processing 1 min GPEH ROP period."
        subst = ["BANDWIDTH_RNC_1=29696", "BANDWIDTH_RNC_2=29696", "BANDWIDTH_RNC_3=29696", "BANDWIDTH_RNC_4=29696", "BANDWIDTH_RBS=1024", 'GPEH_RBS_WORKLOAD="1"', 'GPEH_WORKLOAD_LIST="1:default:10134897:13130000:0-23:01-20"', 'GPEH_MP_CONFIG_LIST="01:05:62,1 06:10:79,1 11:15:91,1 16:20:117,1"']
elif int(var) == 15:
        print "[INFO]: Processing 15 min GPEH ROP period."
        subst = ["BANDWIDTH_RNC_1=16384", "BANDWIDTH_RNC_2=16384", "BANDWIDTH_RNC_3=16384", "BANDWIDTH_RNC_4=16384", "BANDWIDTH_RBS=1024", 'GPEH_RBS_WORKLOAD="15"', 'GPEH_WORKLOAD_LIST="15:max:20269794:40900000:12-18:01-05 15:max:20269794:40900000:12-18:06-15 15:max:20269794:40900000:12-18:16-20 15:default:20269794:24600000:0-11,19-23:01-05 15:default:20269794:24600000:0-11,19-23:06-15 15:default:20269794:24600000:0-11,19-23:16-20"', 'GPEH_MP_CONFIG_LIST="01:05:62,1 06:10:79,1 11:15:91,1 16:20:117,1"']

pattern = ["BANDWIDTH_RNC_1", "BANDWIDTH_RNC_2", "BANDWIDTH_RNC_3", "BANDWIDTH_RNC_4", "BANDWIDTH_RBS", "GPEH_RBS_WORKLOAD", 'GPEH_WORKLOAD_LIST="1', "GPEH_MP_CONFIG_LIST" ]
filedata = old_file.readlines()

if text not in filedata:
        print "[INFO]: Updating netsim_cfg file."
        for line in filedata:
                if pattern[0] in line:
                        print "[INFO]: Replacing " + pattern[0]
                        new_cfg.write(line.replace(line, subst[0] + "\n"))
                elif pattern[1] in line:
                        print "[INFO]: Replacing " + pattern[1]
                        new_cfg.write(line.replace(line, subst[1] + "\n"))
                elif pattern[2] in line:
                        print "[INFO]: Replacing " + pattern[2]
                        new_cfg.write(line.replace(line, subst[2] + "\n"))
                elif pattern[3] in line:
                        print "[INFO]: Replacing " + pattern[3]
                        new_cfg.write(line.replace(line, subst[3] + "\n"))
                elif pattern[4] in line:
                        print "[INFO]: Replacing " + pattern[4]
                        new_cfg.write(line.replace(line, subst[4] + "\n"))
                elif pattern[5] in line:
                        print "[INFO]: Replacing " + pattern[5]
                        new_cfg.write(line.replace(line, subst[5] + "\n"))
                elif pattern[6] in line:
                        print "[INFO]: Replacing " + pattern[6].split('=')[0]
                        new_cfg.write(line.replace(line, subst[6] + "\n"))
                elif pattern[7] in line:
                        print "[INFO]: Replacing " + pattern[7]
                        new_cfg.write(line.replace(line, subst[7] + "\n"))
                else:
                        new_cfg.write(line)

#Closing temp file
new_cfg.close()
#Moving new file to netsim_cfg
os.system("mv /netsim/netsim_cfg_temp /netsim/netsim_cfg")

#Initiated Bandwidth setup
bashCommand = "/netsim_users/pms/bin/setup_GPEH.sh -v 1"

try:
    process = subprocess.Popen(bashCommand.split(), stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    out, err = process.communicate()
    if ("error" or "ERROR") in (err or out):
        print "[ERROR]: Something went wrong while generating GPEH templates.Please contact Genstats team, they will investigate."
        sys.exit(1)
except (ValueError, OSError):
    print "[ERROR]: Please run mannually. \n Hit this --> 'bash /netsim_users/pms/bin/setup_GPEH.sh -v <rop minute>' and you may report to Genstats Team."
    sys.exit(1)

#Applying limit bandwidth for GPEH
#bashCommand2 = "/usr/bin/rsh -l root "+ get_hostname() +" /netsim_users/pms/bin/limitbw -n -c"
bashCommand2 = 'echo shroot | su root -c "/netsim_users/pms/bin/limitbw -n -c"'

try:
    process = subprocess.Popen(bashCommand2.split(), stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    out, err = process.communicate()
    if ("error" or "ERROR") in (err or out):
        print "[ERROR]: Something went wrong while generating GPEH templates.Please contact Genstats team, they will investigate."
        sys.exit(1)
except (ValueError, OSError):
    print "[ERROR]: Please run mannually. \n Hit this --> 'bash /netsim_users/pms/bin/setup_GPEH.sh -v <rop minute>' and you may report to Genstats Team."
    sys.exit(1)

print "[INFO]: Processing Completed."

