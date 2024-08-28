#!/usr/bin/python

class Cnf_vdu(object):
    # NR information
    VDU_MAP = {'DEFAULT': {'SHORT_FDN_NAME': '5G<SIM_INDEX>vDU<NODE_INDEX>',
                           'FULL_FDN_NAME': '5G<SIM_INDEX>vDU<NODE_INDEX>',
                           'SIM_NAME': '5G-FT-vDU-<MIM_VER>x<NE_PER_SIM>-5G<SIM_INDEX>',
                           'NODE_TYPE': 'vDU',
                           'SIM_DATA_FORMAT': 'sim_name: <SIM_NAME>   node_name: <NODE_NAME>         node_type: vDU  sim_mim_ver: <MIM_VER>   stats_dir: /eric-pmbr-rop-file-store/  trace: /c/pm_data/      mim: Netsim_vDU_NODE_MODEL_<MIM_VER>.xml     mib: R6675_<MIB_VER>Mib.xml'
                          }
              }
