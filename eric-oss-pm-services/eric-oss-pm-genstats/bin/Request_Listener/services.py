#!/usr/bin/python -u

import os
import shutil
from urllib.parse import urlparse, parse_qs
import ast
import sys
sys.path.append('/netsim_users/pms/bin')
import logger_utility

logger = logger_utility.LoggerUtilities()

class DoGetService:
        # Handler for the GET requests
    def touch_req_file(self, req_file, response,config_map):
        touch_file =  config_map.get('FILE_PATH','REQUEST_LOOKUP_PATH') + req_file
        if not os.path.exists(config_map.get('FILE_PATH','REQUEST_LOOKUP_PATH')) or not os.path.isdir(config_map.get('FILE_PATH','REQUEST_LOOKUP_PATH')):
            logger.print_error('Either {} is not available or not a directory.'.format(config_map.get('FILE_PATH','REQUEST_LOOKUP_PATH')))
            return response.sendResponse(
                self, 'ERROR : Either {} is not available or not a directory.'.format(config_map.get('FILE_PATH','REQUEST_LOOKUP_PATH')), 400, 'text/plain')
        if not os.path.exists(touch_file):
            logger.print_info('Creating touch file {}.'.format(touch_file))
            os.system('touch "' + touch_file + '"')
            logger.print_info('Touch file {} created.'.format(touch_file))

    def check_mode_status(self, mode,config_map):
        return self.check_netsim_cfg_field(mode,config_map)

    def support_on_demand_for_default_use_case(self, epoch,response,config_map,ROP_IN_SECONDS):
        start_epoch, end_epoch = epoch, epoch + ROP_IN_SECONDS
        mode = ''
        for potential_mode in ast.literal_eval(config_map.get('MODES','SUPPORTED_MODES_LIST')):
            if self.check_netsim_cfg_field(potential_mode + '_ENABLED',config_map):
                mode += '|' + potential_mode
        mode = mode.lstrip('|')
        req_file = str(start_epoch) + '|' + str(end_epoch) + ',' + mode
        self.touch_req_file(req_file,response,config_map)
        logger.print_info('Generating files with Job ID : {}'.format(req_file))
        return response.sendResponse(self, 'INFO : Generating files with Job ID : {}'.format(req_file), 200, 'text/plain')

    def support_on_demand_for_future_rop_use_case(self, epoch,response,config_map,ROP_IN_SECONDS):
        start_epoch = epoch
        for rop_id in range(0, 7):
            end_epoch = start_epoch + ROP_IN_SECONDS
            req_file = str(start_epoch) + '|' + str(end_epoch) + ',FUTURE'
            self.touch_req_file(req_file,response,config_map)
            if rop_id >= 3 and (end_epoch % 3600) == 0:
                logger.print_info('End of Hour ROP acknowledged. Requesting to generate {} future ROP(s).'.format(rop_id + 1))
                try:
                    os.system(config_map.get('FILE_PATH','GENERATE_FUTURE_ROP') + ' -e ' + str(epoch) + ' -f ' + str(rop_id) + ' &')
                    logger.print_info("Future ROP will be available in few seconds.")
                    return response.sendResponse(self ,'INFO : Future ROP will be available in few seconds.', 200, 'text/plain')
                except Exception as e:
                    logger.print_error('An error occurred: {}'.format(e))
                    print(e)
            start_epoch = end_epoch

    def check_netsim_cfg_field(self, param,config_map):
        with open(config_map.get('FILE_PATH','netsim_cfg'), 'r') as cfg:
            for line in cfg:
                if line.startswith(param):
                    if 'true' in line:
                        return True
                    else:
                        return False
            return False

    def check_rop_complete(self, job_id,config_map):
        json_file_path = config_map.get('FILE_PATH','JSON_LOOKUP_PATH') + job_id + '.json_done'
        if os.path.isfile(json_file_path) and os.path.exists(json_file_path):
            return "True"
        else:
            return "False"
        

    def check_status(self,path,response,config_map):
        try:
            query = urlparse(path).query
            job_id = parse_qs(query)['job'][0]
            logger.print_info('Result for Job ID : {} status is: {}'.format(job_id, self.check_rop_complete(job_id,config_map)))
            return response.sendResponse(
                self, 'INFO : Result for Job ID : {} status is: {}'.format(job_id, self.check_rop_complete(job_id,config_map)), 200, 'text/plain')

        except Exception as e:
            logger.print_error('An error occurred: {}'.format(e))
            print(e)




    def verify_input(self, modes,config_map):
        unsupported_modes = [x for x in modes if x not in ast.literal_eval(config_map.get('MODES','SUPPORTED_MODES_LIST'))]
        return [x for x in modes if x in ast.literal_eval(config_map.get('MODES','SUPPORTED_MODES_LIST'))], unsupported_modes
    
    def change_modes(self,path,response,config_map, enable_flag=True):
        changed_list = []
        unchanged_list = []
        return_string = ''
        if enable_flag:
            prefix = "en"
        else:
            prefix = "dis"

        #Parse query and fetch mode list (e.g. STATS|CELLTRACE|REPLAY)
        query = urlparse(path).query
        query_components = parse_qs(query)
        modes_to_change_string = str(query_components['list'][0])
        modes_to_change = modes_to_change_string.split('|')

        #Filter modes not supported and throw warning.
        modes_to_change, unsupported_modes = self.verify_input(modes_to_change,config_map)
        if unsupported_modes:
            logger.print_warn('Found the following unsupported modes : {}. Please only use the following supported modes: {}'.format(unsupported_modes, ast.literal_eval(config_map.get('MODES','SUPPORTED_MODES_LIST'))))
            return response.sendResponse(self ,'WARNING : Found the following unsupported modes : {}. Please only use the following supported modes: {}'.format(unsupported_modes, ast.literal_eval(config_map.get('MODES','SUPPORTED_MODES_LIST'))), 400, 'text/plain')

        #Enable / Disable the mode in the netsim_cfg
        for mode in modes_to_change:
            mode_format = mode.lower().title()
            mode = mode + '_ENABLED'
            if enable_flag != self.check_mode_status(mode,config_map):
                #self.edit_env_variables(mode, enable_flag)
                self.edit_netsim_cfg(mode, config_map, enable_flag)
                changed_list.append(mode_format)
            else:
                unchanged_list.append(mode_format)

        if changed_list:
            return_string += 'INFO : {}abled the file generation for {} mode(s).\n'.format(prefix.title(), changed_list)
        if unchanged_list:
            return_string += 'INFO : {} mode(s) already {}abled.'.format(unchanged_list, prefix)
        logger.print_info(return_string)
        return response.sendResponse(self ,return_string, 200, 'text/plain')

    def edit_netsim_cfg(self, mode, config_map, flag=False):
        output_file = "/netsim/_netsim_cfg"
        with open(config_map.get('FILE_PATH','netsim_cfg'), 'a+') as netsim_cfg_file, open(output_file, "w") as output:
            for line in netsim_cfg_file.readlines():
                if "ENABLED_STATIC_REPLAY=" in line:
                    if flag:
                        line = line.lstrip("#")
                    else:
                        line = "#" + line
                if line.startswith(mode):
                    if flag:
                        line = line.split('=')[0] + "=true\n"
                    else:
                        line = line.split('=')[0] + "=false\n"
                output.write(line)
            os.system("mv " + output_file + " " + config_map.get('FILE_PATH','netsim_cfg'))

    def edit_env_variables(self, mode, flag=False):
        for k, v in os.environ.items():
            if 'ENABLED' in k:
                print(k, v)

        if flag:
            print(mode)
            os.environ[mode] = 'true'
        else:
            os.environ[mode] = 'false'


class DoPutService:

    def file_upload(self,content_length,file_name,read_request_data,response,config_map):
        logger.print_info('Information to transfer : {} bytes.'.format(content_length))
        final_upload_path, intermediate_upload_location, touch_file_name = '', '', ''
        self.create_dir_if_not_exists(config_map.get('FILE_PATH','COMMON_TOUCH_FILE_FOLDER'))
        self.create_dir_if_not_exists(config_map.get('FILE_PATH','TEMPLATE_UPLOAD_LOCATION'))
        if file_name.endswith('.tar.gz'):
            if 'PCC' in file_name.upper() or 'PCG' in file_name.upper():
                if 'TEMPLATE' in file_name.upper():
                    logger.print_info('PCC/PCG Templates upload request processing...')
                    final_upload_path = config_map.get('FILE_PATH','TEMPLATE_UPLOAD_LOCATION') + 'PCC_PCG_TEMPLATE/'
                    intermediate_upload_location = config_map.get('FILE_PATH','TEMPLATE_UPLOAD_LOCATION') + 'PCC_PCG_TEMPLATE_RUNNING/'
                    touch_file_name = 'pcc_pcg_template_upload'
                elif 'CONFIG' in file_name.upper():
                    logger.print_info('PCC/PCG Time Sync Config upload request processing...')
                    final_upload_path = config_map.get('FILE_PATH','TEMPLATE_UPLOAD_LOCATION') + 'PCC_PCG_TIME_SYNC_CONFIG/'
                    intermediate_upload_location = config_map.get('FILE_PATH','TEMPLATE_UPLOAD_LOCATION') + 'PCC_PCG_TIME_SYNC_CONFIG_RUNNING/'
                    touch_file_name = 'pcc_pcg_time_sync_config_upload'
                else:
                    logger.print_error('Invalid file {} upload request. Skipping file upload.'.format(file_name))
                    return response.sendResponse(
                        self,'ERROR : Invalid file {} upload request. Skipping file upload.'.format(file_name), 400,
                        'text/plain')
            else:
                logger.print_info('EBSN Templates upload request processing...')
                final_upload_path = config_map.get('FILE_PATH','TEMPLATE_UPLOAD_LOCATION') + 'EBSN_TEMPLATE/'
                intermediate_upload_location = config_map.get('FILE_PATH','TEMPLATE_UPLOAD_LOCATION') + 'EBSN_TEMPLATE_RUNNING/'
                touch_file_name = 'ebsn_template_upload'

        elif file_name.endswith('.csv'):
            logger.print_info('EBSN Counter information upload request processing...')
            final_upload_path = config_map.get('FILE_PATH','TEMPLATE_UPLOAD_LOCATION') + 'EBSN_COUNTER_UPDATE/'
            intermediate_upload_location = config_map.get('FILE_PATH','TEMPLATE_UPLOAD_LOCATION') + 'EBSN_COUNTER_UPDATE_RUNNING/'
            touch_file_name = 'ebsn_csv_upload'
            file_name = 'ebsn_replay_counter_info.csv'
        else:
            logger.print_error("Filename should consist of '.tar.gz' or '.csv' extension.")
            return response.sendResponse(self,"ERROR : Filename should consist of '.tar.gz' or '.csv' extension.", 400,
                                     'text/plain')
        self.remove_specific_files_from_dir(config_map.get('FILE_PATH','COMMON_TOUCH_FILE_FOLDER'), touch_file_name)
        self.delete_dir_if_exists(final_upload_path)
        self.delete_dir_if_exists(intermediate_upload_location)
        self.create_dir_if_not_exists(intermediate_upload_location)
        file_path = intermediate_upload_location + file_name
        try:
            logger.print_info('Transferring {} file...'.format(file_name))
            with open(file_path, 'wb') as file:
                file.write(read_request_data)
                file.flush()
            logger.print_info('File {} upload completed.'.format(file_name))
            os.rename(intermediate_upload_location, final_upload_path)
            logger.print_info('Directory renamed/moved from {} to {}'.format(intermediate_upload_location, final_upload_path))
            os.system('touch ' + config_map.get('FILE_PATH','COMMON_TOUCH_FILE_FOLDER') + touch_file_name)
            logger.print_info('Touch file {} created successfully.'.format(touch_file_name))
            return response.sendResponse(self,'INFO : File uploaded successfully', 200, 'text/plain')
        except Exception as e:
            print(e)
            logger.print_error('Issue while uploading {} file.'.format(file_name))
            return response.sendResponse(self,'ERROR : Issue while uploading file.', 400, 'text/plain')

    def remove_specific_files_from_dir(self, dir_name, file_name):
        for f in filter(None, os.listdir(dir_name)):
            if f == file_name:
                os.remove(dir_name + f)

    def delete_dir_if_exists(self, dir_name):
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

    def create_dir_if_not_exists(self, dir_name):
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

    



