import utilprocs
import configUtils
import glob
import os
import json
import re
import datetimeUtils
from collections import defaultdict

script_dir = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.join(script_dir, 'config.ini')
config_json_path = '/etc/config/config.json'
output_list = []

class FileValidation:

    def __init__(self, args, netsim_cfg_params):

        self.netsim_cfg_params = netsim_cfg_params
        self.epoch_folder = args.epoch_folder
        self.validate_creation_time = args.validate_creation_time
        self.validate_file_size = args.validate_file_size
        self.enable_modules = self.createEnabledModuleList(netsim_cfg_params)

        utilprocs.title("File Validation Configuration")
        utilprocs.log(self.netsim_cfg_params)
        utilprocs.log('Validating for Epoch folder : {}'.format(self.epoch_folder))

        utilprocs.log('Starting file validation for ' + ','.join(self.enable_modules))

    def initiateHealthCheck(self):

        global config_map

        config_map = configUtils.createConfigMap(config_file)

        if not config_map:
            utilprocs.log("Terminating Health Check", severity="ERROR")
            return False

        self.custom_stats = utilprocs.str2bool(os.getenv('custom_stats'))
        self.custom_ctr = utilprocs.str2bool(os.getenv('custom_ctr'))
        self.start_epoch, self.end_epoch = [int(x) for x in self.epoch_folder.split('_')]
        self.dateTimeDict = datetimeUtils.convert_epoch_range(self.start_epoch, self.end_epoch)
        self.node_mapping = configUtils.getConfigSectionAsDictionary(config_map,'NODE_MAPPING')

        for pm_type in self.enable_modules:

            if os.path.exists("/ericsson/pmic/{}".format(pm_type)):

                files = glob.glob("/ericsson/pmic/{}/*/{}/*".format(pm_type, self.epoch_folder))

                if files:

                    sorted_dict, output = self.validateFiles(pm_type, files)
                    output_list.append(output)

                    if sorted_dict and self.validate_file_size:
                        fs_output = self.fileSizeValidation(pm_type, sorted_dict)
                        output_list.append(fs_output)
                    else:
                        utilprocs.log('Skipping file size validation for {}'.format(pm_type), severity="WARNING")
                else:
                    utilprocs.title("{} File Validation".format(pm_type.capitalize()))
                    utilprocs.log("{} folder doesn't exist for {}".format(self.epoch_folder, pm_type), severity="ERROR")
                    utilprocs.log('Skipping file validation for {}'.format(pm_type), severity="ERROR")
                    output_list.append(False)
                    continue
            else:
                utilprocs.title("{} File Validation".format(pm_type.capitalize()))
                utilprocs.log("{} folder doesn't exist.".format(pm_type), severity="ERROR")
                utilprocs.log("Skipping file validation for {}".format(pm_type), severity="ERROR")
                output_list.append(False)
                continue

        return all(output_list)

    def validateFiles(self, pm_type, pm_type_list):

        utilprocs.title("{} File Validation".format(pm_type.capitalize()))

        sorted_dict = defaultdict(list)
        invalid_nodes = defaultdict(list)

        extension = configUtils.getConfigSectionAsDictionary(config_map, pm_type + '_FILE_EXTENSION')
        expected_format = configUtils.getConfigSectionAsDictionary(config_map, pm_type + '_EXPECTED_FILE_FORMAT')

        if expected_format:
            replace_timestamp = {'<{}>'.format(key): value for key, value in self.dateTimeDict.items()}

            for key, value in replace_timestamp.items():
                for type, file_format in expected_format.items():
                    expected_format[type] = file_format.replace(key, value)

        for items in pm_type_list:
            file_name = os.path.basename(items)
            node_name = os.path.basename(os.path.dirname(os.path.dirname(items)))
            MeContext = self.extractValueFromNodeName(file_name,"MeContext")

            node_type = self.identifyNodeType(node_name)

            if not node_type:
                invalid_nodes['unidentified_nodes'].append(MeContext)
                continue

            try:
                # Validate file extension
                if not file_name.endswith(extension[node_type]):
                    invalid_nodes['invalid_extension_nodes'].append(MeContext)
                    continue

                # File Format validation
                if expected_format:
                    if not self.validateFileFormat(file_name, expected_format[node_type], MeContext):
                        invalid_nodes['invalid_file_format_nodes'].append(MeContext)
                        continue

                #Validate file creation time in epoch range
                if self.validate_creation_time:
                    creation_time = os.lstat(items).st_ctime
                    if not self.validateFileCreationTime(creation_time):
                        invalid_nodes['invalid_creation_time_nodes'].append(MeContext)
                        continue

            except Exception:
                utilprocs.printException()
                raise

            sorted_dict[node_type].append(items)

        output = self.validateFileCount(pm_type, sorted_dict, dict(invalid_nodes))

        return dict(sorted_dict), output

    def validateFileFormat(self, file_name, file_format, me_context):

        network_options = ['CUCP', 'CUUP', 'DU']
        replace = {
            '<any_value>' : '.*',
            '<me_context>' : me_context
        }

        for key, value in replace.items():
            file_format = file_format.replace(key, value)

        if '<network_options>' in file_format:
            output = self.check_in_list('<network_options>' ,file_format.split('_',1)[1], file_name.split('_',1)[1], network_options) and file_name.startswith(file_format.split('_',1)[0])
        else:
            output = self.matchRegex(file_format.split('_',1)[1], file_name.split('_',1)[1]) and file_name.startswith(file_format.split('_',1)[0])
        return output

    def fileSizeValidation(self, pm_type, sorted_dict):

        try:
            utilprocs.title("{} File Size Validation".format(pm_type.capitalize()))
            expected_file_size_dict = configUtils.getConfigSectionAsDictionary(config_map, pm_type + '_EXPECTED_FILE_SIZE')

            # Skkipping file validation if section doesn't exist in INI file
            if not expected_file_size_dict:
                utilprocs.log("Skipping File Size Validation for {}".format(pm_type), severity="WARNING")
                return True

            avg_file_size_dict = self.calculateAverage(sorted_dict)
            utilprocs.log("{} average file size: ".format(pm_type.capitalize()) + str(avg_file_size_dict))

            file_size_output = self.checkFileSize(avg_file_size_dict, expected_file_size_dict)
            if file_size_output:
                utilprocs.log("{} file size validation passed!!".format(pm_type.capitalize()))
            else:
                utilprocs.log("{} file size validation failed!!".format(pm_type.capitalize()), severity="ERROR")
                utilprocs.log("{} expected file size: {}".format(pm_type.capitalize(), str(expected_file_size_dict)))

            return file_size_output

        except Exception:
            utilprocs.printException()
            raise

    def identifyNodeType(self, node_name):

        for node_type, data_type in self.node_mapping.items():
            if data_type in node_name:
                return node_type

        # utilprocs.log("Can't find matching node for '{}'".format(node_name), severity="ERROR")
        return None

    def generate_expected_output_dict(self, key_dict):

        try:
            with open(config_json_path) as json_file:
                data = json.load(json_file)

            for key, items in key_dict.items():
                key_dict[key] = int(data.get(items))

        except Exception as e:
            utilprocs.printException()
            raise

        return key_dict

    def file_count_list_length(self, input_dict):
        """
        Generate a new dictionary from the input dictionary where:

        Parameters:
        - input_dict (dict): A dictionary where values are lists.

        Returns:
        - output_dict (dict): A new dictionary with the same keys as the input,
        but with values replaced by the lengths of their corresponding lists.
        """

        output_dict = {}

        for key, value in input_dict.items():
            output_dict[key] = len(value)

        return output_dict

    def validateFileCreationTime(self, file_creation_time):
        """
        Validates if file creation time is in epoch range.

        Parameters:
        - file_creation_time (float): File creation time.

        Returns:
        - bool: True/False
        """

        if self.start_epoch <= file_creation_time <= self.end_epoch:
            return True
        return False

    def averageFileSize(self, file_path_list):
        """
        Calculates the average file size from a list of file paths.

        Parameters:
        - file_path_list (list): List of file paths.

        Returns:
        - float: Average file size in kilo bytes. Return 0 if no valid files found.
        """

        sum = 0

        for file_path in file_path_list:
            if os.path.isfile(file_path) and os.path.exists(file_path):
                sum += os.path.getsize(file_path)
            else:
                utilprocs.log("{} is not a file or it doesn't exist.".format(file_path), severity="ERROR")

        return sum/len(file_path_list)

    def calculateAverage(self, input_dict):
        """
        Calculates the average file size for provided dictionary of keys as node_tpe and value as list of file paths.

        Parameters:
        - input_dict (dict): Dictionary with keys as node_types and values as list of file paths.

        Returns:
        - output_dict (dict): Dictionary containing keys from input dictionary and values as average file sizes.
        """

        output_dict = {}
        for key, value in input_dict.items():
            output_dict[key] = self.averageFileSize(value)

        return output_dict

    def check_in_list(self, key, file_format, file_name, replace_list):
        """
        Replace from list and match regex, Returns true or false.

        Parameters:
        - key (str): Key to replace in file format.
        - file_format (str): Expected file format.
        - file_name (str): Actual file name.
        - replace_list (list): List of values which will be replaced in file_format

        Returns:
        - bool: True or False
        """

        if key in file_format:
            for options in replace_list:
                replace_string = file_format
                replace_string = replace_string.replace(key, options)
                output = self.matchRegex(replace_string, file_name)
                if output: return True
        return False

    def extractValueFromNodeName(self, string, key_to_fetch):

        split_str = string.split(',')
        value = None

        for arg in reversed(split_str):
            if key_to_fetch in arg:
                value = arg.split('=')[1]
                if '_' in value:
                    value = value.split('_')[0]
                break
        return value

    def createEnabledModuleList(self, map):

        list = []
        for key, value in map.items():
            if '_ENABLED' in key:
                if not value:
                    continue
                modified_key = key.replace('_ENABLED', '')
                list.append(modified_key)
        return list

    def checkFileSize(self, actual_size_dict, expected_size_dict):

        for key, expected_size_tuple in expected_size_dict.items():
            lower_bound, upper_bound = [float(x) for x in expected_size_tuple.split(',')]
            if key in actual_size_dict:
                actual_size = actual_size_dict[key]
                if lower_bound <= actual_size <= upper_bound:
                    return True
        return False

    def validateFileCount(self, pm_type, sorted_dict, invalid_nodes):

        passed = False
        total_started = configUtils.getConfigSectionAsDictionary(config_map, pm_type + '_TOTAL_STARTED')

        if pm_type == 'STATS' and self.custom_stats:
            custom_ne = (configUtils.getConfigValue(config_map, 'CUSTOM_STATS','NE')).split(',')
            custom_started = configUtils.getConfigSectionAsDictionary(config_map, pm_type + '_CUSTOM_STARTED')
            output_dict_keys = self.create_custom_output_dict(total_started,custom_started,custom_ne)
        elif pm_type == 'CELLTRACE' and self.custom_ctr:
            custom_ne = configUtils.getConfigValue(config_map, 'CUSTOM_CELLTRACE','NE').split(',')
            custom_started = configUtils.getConfigSectionAsDictionary(config_map, pm_type + '_CUSTOM_STARTED')
            output_dict_keys = self.create_custom_output_dict(total_started,custom_started,custom_ne)
        else:
            output_dict_keys = total_started

        actual_file_count = self.file_count_list_length(sorted_dict)

        if not output_dict_keys:
            utilprocs.log("{} actual file count: ".format(pm_type.capitalize()) + str(actual_file_count))
            if invalid_nodes:
                self.printInvalidNodes(pm_type, invalid_nodes)
                return False
            else:
                return True

        expected_output = self.generate_expected_output_dict(output_dict_keys)

        if pm_type == 'CELLTRACE' and self.custom_ctr==False:
            file_per_node = configUtils.getConfigSectionAsDictionary(config_map, pm_type + '_FILES_PER_NODE')
            if file_per_node:
                expected_output = {key: expected_output[key] * int(file_per_node[key]) for key in expected_output if key in file_per_node}

        output = self.compare(actual_file_count,expected_output)
        if output and not invalid_nodes:
            utilprocs.log("{} File Format Validation passed!!".format(pm_type.capitalize()))
            passed = True
        else:
            utilprocs.log("{} file format validation failed!!".format(pm_type.capitalize()), severity="ERROR")
            self.printInvalidNodes(pm_type, invalid_nodes)
            utilprocs.log("{} expected file count: {}".format(pm_type.capitalize(), str(expected_output)))

        utilprocs.log("{} actual file count: ".format(pm_type.capitalize()) + str(actual_file_count))

        return passed

    def create_custom_output_dict(self, total_started, custom_started, ne_list):

        output = {}

        for key in total_started.keys():
            if key in ne_list:
                output[key] = custom_started[key]
            else:
                output[key] = total_started[key]

        return output

    def printInvalidNodes(self, pm_type ,invalid_nodes):

        invalid_node_filename = os.path.join(utilprocs.log_dir, 'invalid_nodes.json')
        existing_data = {}

        if invalid_nodes:
            invalid_nodes_count = self.file_count_list_length(invalid_nodes)

            for key,count in invalid_nodes_count.items():
                utilprocs.log("{} {} : {}".format(pm_type.capitalize(), key.replace('_',' ').lower(), str(count)), severity="ERROR")

            if os.path.exists(invalid_node_filename):
                with open(invalid_node_filename, 'r') as file:
                    existing_data = json.load(file)

            invalid_nodes = {pm_type: invalid_nodes}
            existing_data.update(invalid_nodes)

            with open(invalid_node_filename, 'w') as file:
                json.dump(existing_data, file, indent=4)
            utilprocs.log("Invalid nodes are stored in {} file.".format(invalid_node_filename))
        else:
            utilprocs.log("There are no invalid nodes for {}".format(pm_type.capitalize()))

    def compare(self, val1, val2):

        if val1 == val2:
            return True
        return False

    def matchRegex(self, pattern, string):
        if re.match(pattern, string):
            return True
        return False