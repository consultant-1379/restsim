#!/usr/bin/python

class Nrat(object):
    # NR information
    NRAT_MAP = {'DEFAULT': {'SHORT_FDN_NAME': 'NR<SIM_INDEX>gNodeBRadio<NODE_INDEX>',
                            'FULL_FDN_NAME': 'NR<SIM_INDEX>gNodeBRadio<NODE_INDEX>',
                            'SIM_NAME': 'NR<MIM_VER>x<NE_PER_SIM>-gNodeBRadio-NRAT-NR<SIM_INDEX>',
                            'NODE_TYPE': 'GNODEBRADIO',
                            'SIM_DATA_FORMAT': 'sim_name: <SIM_NAME>   node_name: <NODE_NAME>         node_type: GNODEBRADIO  sim_mim_ver: <MIM_VER>   stats_dir: /c/pm_data/  trace: /c/pm_data/      mim: Netsim_MSRBS-V2_NODE_MODEL_<MIM_VER>.xml     mib: MSRBS_V2_<MIB_VER>Mib.xml'
                            }
                }
