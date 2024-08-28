#!/netsim/miniconda/bin/python

from netsim_cfg_gen import *
import os,sys,socket
import mako.template as Template
import getopt
from subprocess import Popen, PIPE

SIMULATION_DIR = "/netsim/netsim_dbdir/simdir/netsim/netsimdir/"
RADIO_NODE_NE = ["VTFRADIONODE", "5GRADIONODE", "TLS", "VRM", "VRSM","VSAPC", "VTIF", "PCC", "PCG", "CCSM", "CCDM", "CCRC", "CCPC", "SC"]
PLAYBACK_CFG = "/netsim_users/pms/bin/playback_cfg"
CFG = "/netsim/etc/netsim_cfg_gen"

def upload_cfg(nssRelease="16.8", sim_data_list=[], edeStatsCheck="False", deplType="NSS", counterVolume="None", oss_enabled="False"):
    sims = []
    mmes = []
    default_LTE_UETRACE_LIST = ["LTE01", "LTE02", "LTE03", "LTE04", "LTE05"]
    LTE_NE_map = {"LTE_UETRACE_LIST": [], "MSRBS_V1_LTE_UETRACE_LIST": [], "MSRBS_V2_LTE_UETRACE_LIST": [] }
    PM_file_paths = {}
    playback_sim_list = ""
    bsc_sim_list = []
    hlr_sim_list = []
    host_name = get_hostname()
    msc_sim_list = []
    ecs_sim_list = []
    for sim_info in sim_data_list:
         sim_data = sim_info.split()
         sim_name = sim_data[1]
         ne_type = sim_data[5]
         stats_dir = sim_data[9]
         trace_dir = sim_data[11]
         if ne_type == 'PRBS' and 'LTE' in sim_name:
             ne_type = 'MSRBS_V1'

         if ne_type not in PM_file_paths:
             if "EPG" in ne_type:
                PM_file_paths["EPG"] = [stats_dir, trace_dir]
             elif "5GRADIONODE" in ne_type:
                PM_file_paths["FIVEGRADIONODE"] = [stats_dir, trace_dir]
             else:
                PM_file_paths[ne_type] = [stats_dir, trace_dir]

         if "LTE" in sim_name:
            sim_ID = sim_name.split()[-1].split('-')[-1]
            if any(radio_ne in sim_name.upper() for radio_ne in RADIO_NODE_NE):
               sims.append(sim_name)
            else:
               sims.append(sim_ID)
            if "PRBS" in ne_type or "MSRBS-V1" in ne_type:
                LTE_NE_map["MSRBS_V1_LTE_UETRACE_LIST"].append(sim_ID)
                if sim_ID in default_LTE_UETRACE_LIST:
                    default_LTE_UETRACE_LIST.remove(sim_ID)
            elif "MSRBS-V2" in ne_type:
                  LTE_NE_map["MSRBS_V2_LTE_UETRACE_LIST"].append(sim_ID)
                  if sim_ID in default_LTE_UETRACE_LIST:
                      default_LTE_UETRACE_LIST.remove(sim_ID)
         elif "RNC" in sim_name:
              sims.append(sim_name.split()[-1].split('-')[-1])
         elif "SGSN" in sim_name:
              mmes.append(sim_name.split()[-1])
         elif "FRONTHAUL" in sim_name.upper():
              if edeStatsCheck:
                 sims.append(sim_name.split()[-1])
         else:
              sims.append(sim_name.split()[-1])

    if get_playback_list():
        for nes in get_playback_list():
            sim_list = []
            sim_list = run_shell_command("ls " + SIMULATION_DIR + " | grep {0}".format(nes)).split('\n')
            for sim_name in sim_list:
                playback_sim_list = playback_sim_list + " " + sim_name.strip()

    bsc_sim_list = get_bsc_list()
    if bsc_sim_list:
        for sim_name in bsc_sim_list:
             sims.append(sim_name.strip())

    msc_sim_list = get_msc_list()
    if msc_sim_list:
        for sim_name in msc_sim_list:
             sims.append(sim_name.strip())

    hlr_sim_list = get_hlr_list()
    if hlr_sim_list:
        for sim_name in hlr_sim_list:
             sims.append(sim_name.strip())
    
    ecs_sim_list = get_ecs_list()
    if ecs_sim_list:
        for sim_name in ecs_sim_list:
            sims.append(sim_name.strip())

    sims = list(set(sims))
    LTE_NE_map["LTE_UETRACE_LIST"] = default_LTE_UETRACE_LIST

    template = "/netsim_users/auto_deploy/etc/netsim_cfg_template_omni"
    if oss_enabled == "True":
        template = "/netsim_users/auto_deploy/etc/netsim_cfg_OSS"

    create_netsim_cfg(
        get_hostname(), nssRelease, ' '.join(sims), ' '.join(mmes), PM_file_paths, playback_sim_list.strip(), template, edeStatsCheck, counterVolume, oss_enabled, deplType)
    os.system("cp -f " + host_name + " /tmp/" + host_name)
    #os.remove(get_hostname())


def get_playback_list():
    bashCommand = "grep NE_TYPE_LIST " + PLAYBACK_CFG
    playback_content = filter(None, run_shell_command(bashCommand).strip())
    PLAYBACK_SIM_LIST = []
    PLAYBACK_SIM_LIST = playback_content.split("=")[-1].replace("\"", "").split()
    return PLAYBACK_SIM_LIST

def get_bsc_list():
    bashCommand = "ls " + SIMULATION_DIR + " | grep BSC"
    result = filter(None, run_shell_command(bashCommand).split("\n"))
    if result:
        return result
    else:
        return None

def get_msc_list():
    bashCommand = "ls " + SIMULATION_DIR + " | grep MSC"
    result = filter(None, run_shell_command(bashCommand).split("\n"))
    if result:
        return result
    else:
        return None

def get_hlr_list():
    bashCommand = "ls " + SIMULATION_DIR + " | grep HLR-FE"
    result = filter(None, run_shell_command(bashCommand).split("\n"))
    if result:
        return result
    else:
        return None

def get_ecs_list():
    ecs_sim_list = filter(None, run_shell_command('ls ' + SIMULATION_DIR + ' | egrep "ERSN|ERS[-_]SN[-_]ESC|ERS[-_]SN[-_]SCU|SCU[-_]"').split("\n"))
    if ecs_sim_list:
        return ecs_sim_list
    else:
        return None

def get_hostname():
    netsim_cfg_file = socket.gethostname().split('.')[0]
    if os.path.isfile("/netsim/genstats/.dockerenv") or "atvts" in netsim_cfg_file:
        netsim_cfg_file = "netsim"
    return netsim_cfg_file

def run_shell_command(input):
    """ This is the generic method, Which spawn a new shell process to get the job done
    """
    output = Popen(input, stdout=PIPE, shell=True).communicate()[0]
    return output


def main(argv):
    edeStatsCheck="False"
    counterVolume="None"
    ossEnabled="False"
    with open('/netsim/genstats/tmp/sim_data.txt', 'r') as sim_data:
        sim_data_list = filter(None, sim_data.read().split('\n'))
    try:
        opts, args = getopt.getopt(argv,"nssRelease:deplType:edeStatsCheck:counterVolume:ossEnabled:",["nssRelease=","deplType=","edeStatsCheck=","counterVolume=","ossEnabled="])
    except getopt.GetoptError:
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("--nssRelease"):
            nssRelease = arg
        elif opt in ("--deplType"):
            deplType = arg
        elif opt in ("--edeStatsCheck"):
            edeStatsCheck = arg
        elif opt in ("--counterVolume"):
            counterVolume = arg
        elif opt in ("--ossEnabled"):
            ossEnabled = arg

    upload_cfg(nssRelease, sim_data_list, edeStatsCheck, deplType, counterVolume, ossEnabled)


if __name__ == "__main__":
   main(sys.argv[1:])
