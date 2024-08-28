#!/usr/bin/python

import os


class Constants(object):
    # ENM Config
    ENM_ID = 'ENM_ID'  # in netsim_cfg
    ENM_ID_LIST = 'ENM_ID_LIST'  # in config_map
    RELEASE = 'TYPE'
    # Unknown PMIC location structure
    PMIC_LOC = '/ericsson/pmic/'

    # Config file Config
    CONFIG_MAP_PATH = 'CONFIG_MAP_PATH'
    CONFIG_JSON = 'config.json'

    # Lock files
    DEPLOYING = '.DEPLOYING'
    SCALE_READY = '.SCALE_READY'
    SCALING = '.SCALING'

    # clean up
    FULL_CLEANUP = [DEPLOYING, SCALE_READY, SCALING]

    # network information json file, expected enm_id format i,e ENM_1, ENM_2,...
    ENM_NETWORK_JSON = '.simulated_network_<ENM_ID>.json'

    # events paths template
    NR_TEMPLATE = "<SIM>|GNODEBRADIO"

    # locations
    NETSIM_CFG = '/netsim/netsim_cfg'
    PMS_LOG_LOC = '/netsim_users/pms/logs/'
    STARTED_NE_FILE = '/tmp/showstartednodes.txt'
    SIM_DATA_FILE = '/netsim/genstats/tmp/sim_data.txt'

    identity_map = {'NR': 'GNODEBRADIO', 'NR_EBSN': 'GNODEBRADIO_EBSN', 'LTE_DG2': 'LTE', 'PCC': 'PCC',
                    'PCC_AMF': 'PCC_AMF', 'PCG': 'PCG', 'VDU': 'VDU', 'VCUCP': 'VCUCP', 'VCUUP': 'VCUUP'}

    # Ne Support config
    SUPPORTED_NE_MAP = {'NRM6.3': [{'GNODEBRADIO': ['STATS', 'CELLTRACE', 'FUTURE']},
                                   {'PCC': ['STATS']},
                                   {'PCG': ['STATS']},
                                   {'PCC_AMF': ['STATS']},
                                   {'GNODEBRADIO_EBSN': ['REPLAY']},
                                   {'VDU': ['STATS']},
                                   {'VCUCP': ['STATS']},
                                   {'VCUUP': ['STATS']},
                                   {'LTE': ['STATS', 'CELLTRACE', 'FUTURE']}
                                   ]
                        }

    # Per node type, limit for future PM files generation
    FUTURE_NODE_LIMIT = 2

    sims_per_enm_map = {'NR_SIMS_PER_ENM': 0, 'LTE_DG2_SIMS_PER_ENM': 0, 'PCC_SIMS_PER_ENM': 0,
                        'PCC_AMF_SIMS_PER_ENM': 0, 'PCG_SIMS_PER_ENM': 0,
                        'NR_EBSN_SIMS_PER_ENM': 0, 'VDU_SIMS_PER_ENM': 0, 'VCUCP_SIMS_PER_ENM': 0,
                        'VCUUP_SIMS_PER_ENM': 0}
    nes_per_sim_map = {'NR_NES_PER_SIM': 0, 'LTE_DG2_NES_PER_SIM': 0, 'PCC_NES_PER_SIM': 0, 'PCC_AMF_NES_PER_SIM': 0,
                       'PCG_NES_PER_SIM': 0,
                       'NR_EBSN_NES_PER_SIM': 0, 'VDU_NES_PER_SIM': 0, 'VCUCP_NES_PER_SIM': 0, 'VCUUP_NES_PER_SIM': 0}
    total_started_ne_to_cnt_map = {'TOTAL_STARTED_NR_NES': 0, 'TOTAL_STARTED_LTE_DG2_NES': 0,
                                   'TOTAL_STARTED_PCC_NES': 0, 'TOTAL_STARTED_PCC_AMF_NES': 0,
                                   'TOTAL_STARTED_PCG_NES': 0, 'TOTAL_STARTED_NR_EBSN_NES': 0,
                                   'TOTAL_STARTED_VDU_NES': 0, 'TOTAL_STARTED_VCUCP_NES': 0,
                                   'TOTAL_STARTED_VCUUP_NES': 0}
    ne_mim_release_map = {'NR_MIM_RELEASE': None, 'LTE_DG2_MIM_RELEASE': None, 'PCG_MIM_RELEASE': None,
                          'PCC_MIM_RELEASE': None, 'PCC_AMF_MIM_RELEASE': None, 'NR_EBSN_MIM_RELEASE': None,
                          'VDU_MIM_RELEASE': None,
                          'VCUCP_MIM_RELEASE': None, 'VCUUP_MIM_RELEASE': None}

    ne_ctr_files = {'NR_CTR_FILES': 0, 'LTE_DG2_CTR_FILES': 0}

    ne_stats_files = {'NR_STATS_FILES': 0, 'LTE_DG2_STATS_FILES': 0, 'PCC_STATS_FILES': 0, 'PCG_STATS_FILES': 0,
                      'VDU_STATS_FILES': 0, 'VCUCP_STATS_FILES': 0, 'VCUUP_STATS_FILES': 0}

    custom_file_map = {'custom_ctr': "true", 'custom_stats': "true"}

    # Started node entry format
    START_NE_FORMAT = '    <NODE_NAME>         30.5.103.198 161 public v3+v2+v1 .128.0.0.193.1.30.5.103.198 mediation authpass privpass none none  [TLS] /netsim/netsimdir/<SIM_NAME> <STATS> <CTR>\n'

    FULL_FDN_FORMAT = 'SubNetwork=<subnet>,MeContext='

    SUB_NET_MAP = {'PCC': 'ERBS-SUBNW-1', 'PCC_AMF': 'ERBS-SUBNW-1', 'PCG': 'ERBS-SUBNW-1',
                   'DEFAULT': 'Europe,SubNetwork=Ireland'}

    MANAGED_ELEMENT_MAP = {'PCC': ',ManagedElement=', 'PCC_AMF': ',ManagedElement=', 'PCG': ',ManagedElement=',
                           'DEFAULT': ''}

    JAR_PATH = '/netsim_users/pms/lib/fls-updator-service.jar'

    EBSN_REPLAY_PARAMS = ['REPLAY_ENABLED', 'EBSN_PERFORMANCE_ENABLED']

    PCC_PCG_ESOA_PARAMS = ['PCC_PCG_FOR_ESOA', 'PCC_PCG_FOR_ESOA_PERFORMANCE']

    def __init__(self):
        self.modify_class_for_esoa_ebsn()
        self.modify_class_for_esoa_pcc_pcg()

    # Need to test this code logic again
    def modify_class_for_esoa_ebsn(self):
        for param in self.EBSN_REPLAY_PARAMS:
            if os.getenv(param).upper() not in ['NO', 'FALSE']:
                continue
            for nrm_rel in self.SUPPORTED_NE_MAP.keys():
                rel_ne_map_list = self.SUPPORTED_NE_MAP[nrm_rel]
                for index, ne_map in enumerate(rel_ne_map_list):
                    if 'GNODEBRADIO_EBSN' in ne_map.keys():
                        self.SUPPORTED_NE_MAP[nrm_rel].pop(index)

    # Need to test this code logic
    def modify_class_for_esoa_pcc_pcg(self):
        if os.getenv('PCC_PCG_FOR_ESOA').upper() in ['NO', 'FALSE']:
            return
        for param in self.PCC_PCG_ESOA_PARAMS:
            if os.getenv(param).upper() not in ['NO', 'FALSE']:
                continue
            for nrm_rel in self.SUPPORTED_NE_MAP.keys():
                rel_ne_map_list = self.SUPPORTED_NE_MAP[nrm_rel]
                for index, ne_map in enumerate(rel_ne_map_list):
                    for ne_key in ne_map.keys():
                        if ne_key in ['PCC', 'PCG', 'PCC_AMF']:
                            self.SUPPORTED_NE_MAP[nrm_rel].pop(index)
