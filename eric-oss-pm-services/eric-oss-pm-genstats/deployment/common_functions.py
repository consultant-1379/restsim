#!/usr/bin/python
import json
import os.path

from constants import Constants
from nrat import Nrat
from pcc import Pcc
from pcg import Pcg

c = Constants()
nr, pcc, pcg = Nrat(), Pcc(), Pcg()


class CommonFunctions(object):
    netsim_cfg = c.NETSIM_CFG

    def is_file_exists(self, filepath):
        if os.path.isfile(filepath):
            return True
        return False

    def is_dir_exists(self, filepath):
        if os.path.isdir(filepath):
            return True
        return False

    def find_param_value_from_netsim_cfg(self, param):
        value = None
        if not param.endswith('='):
            param = param + '='
        with open(self.netsim_cfg, 'r') as cfg:
            for line in cfg:
                if line.startswith(param):
                    value = line.strip().replace(' ', '').replace('"','').split('=')[1]
                    if value == '':
                        value = None
                    break
        return value

    def get_json_object(self, filepath):
        try:
            with open(filepath, 'r') as cfg:
                return json.load(cfg)
        except Exception as e:
            return None

    def get_str_list_object_from_json(self, json_obj, param, is_filter=False):
        if param in json_obj.keys() and json_obj[param] is not None:
            if is_filter:
                return [str(x) for x in json_obj[param] if x is not None and x.replace(' ', '') != '']
            return [str(x) for x in json_obj[param]]
        return None

    def get_int_value_from_json(self, json_obj, param):
        if param in json_obj.keys() and json_obj[param] is not None:
            if json_obj[param].replace(' ', '') == '':
                return None
            return int(json_obj[param])
        return None

    def get_str_value_from_json(self, json_obj, param):
        if param in json_obj.keys() and json_obj[param] is not None:
            if json_obj[param].replace(' ', '') == '':
                return None
            return str(json_obj[param])
        return None

    def correct_dir_path(self, value):
        if value.endswith('/'):
            return value
        else:
            return value + '/'

    def remove_file_only(self, path):
        os.remove(path)

    def get_mib_version(self, mim_version):
        mib_version = mim_version
        mim_elements = mim_version.split('-')
        if len(mim_elements) == 3:
            mib_version = '-'.join(mim_elements[0:2]) + '_' + mim_elements[-1]
        return mib_version

    def get_ne_configuration(self, ne, dmi_ver):
        _map = None
        if ne == 'GNODEBRADIO':
            _map = nr.NRAT_MAP.get('DEFAULT')
        elif ne == 'PCC':
            _map = pcc.PCC_MAP.get('DEFAULT')
        elif ne == 'PCG':
            _map = pcg.PCG_MAP.get('DEFAULT')
        return _map

    def generate_schema_for_ne(self, ne_config, start_sim_id, total_sim_count, ne_per_sim, mim, padding):
        sim_dir_list, sim_list = [], []
        mib_version = self.get_mib_version(mim)
        for _ in range(total_sim_count):
            str_sim_id = str(start_sim_id).zfill(2)
            sim_name = ne_config['SIM_NAME'].replace('<MIM_VER>', mim).replace('<NE_PER_SIM>', str(ne_per_sim)).replace(
                '<SIM_INDEX>', str_sim_id)
            is_first = True
            for ne_index in range(1, ne_per_sim + 1):
                ne_name_dir = ne_config['SHORT_FDN_NAME'].replace('<SIM_INDEX>', str_sim_id).replace('<NODE_INDEX>',
                                                                                                     str(ne_index).zfill(
                                                                                                         padding))
                if is_first:
                    sim_list.append(ne_config['SIM_DATA_FORMAT'].replace('<SIM_NAME>', sim_name).replace('<NODE_NAME>',
                                                                                                         ne_name_dir).replace(
                        '<MIM_VER>', mim).replace('<MIB_VER>', mib_version) + '\n')
                    is_first = False
                sim_dir_list.append(sim_name + '|' + ne_name_dir)
            start_sim_id = start_sim_id + 1
        return sim_dir_list, sim_list
