#!/usr/bin/python

class Cnf_vcucp(object):
    # NR information
    VCUCP_MAP = {'DEFAULT': {'SHORT_FDN_NAME': '5G<SIM_INDEX>vCU-CP<NODE_INDEX>',
                           'FULL_FDN_NAME': '5G<SIM_INDEX>vCU-CP<NODE_INDEX>',
                           'SIM_NAME': '5G-FT-vCU-CP-<MIM_VER>x<NE_PER_SIM>-5G<SIM_INDEX>',
                           'NODE_TYPE': 'vCUCP',
                           'SIM_DATA_FORMAT': 'sim_name: <SIM_NAME>   node_name: <NODE_NAME>         node_type: vCU-CP  sim_mim_ver: <MIM_VER>   stats_dir: /eric-pmbr-rop-file-store/  trace: /c/pm_data/      mim: Netsim_vCUCP_NODE_MODEL_<MIM_VER>.xml     mib: R6675_<MIB_VER>Mib.xml'
                          }
              }
