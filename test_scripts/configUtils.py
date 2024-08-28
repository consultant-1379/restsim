import configparser
import utilprocs
import os

def getConfigSectionAsDictionary(config_map, section_name):
    """
    Reads a specified section from the INI file and creates a dictionary.

    Parameters:
    - config_map (ConfigParser): ConfigParser object
    - section_name (str) : Name of section in INI file.

    Returns:
    - section_dict (dict) : Dictionary containing key value pair from the specified section.
    """

    section_dict = dict(config_map.items(section_name)) if config_map.has_section(section_name) else {}
    return section_dict

def getConfigValue(config_map, section_name, key):
    """
    Retrieves a value from the INI fil using the provided section name and key.

    Parameters:
    - config_map (ConfigParser): ConfigParser object
    - section_name (str) : Name of section in INI file.
    - key (str) : The key within the specified section to retrieve the value.

    Returns:
    - val (str or None) : Value corresponding to given section name and key. None, if key/section doesn't exist.
    """

    return config_map.get(section_name, key)

def createConfigMap(file_path):
    """
    Returns ConfigParser object for provided file.

    Parameters:
    - file_path (str) : Path of INI file.

    Returns:
    - config_map (ConfigParser): ConfigParser object
    """

    try:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            config_map = configparser.ConfigParser()
            config_map.optionxform = str
            config_map.read(file_path)
        else:
            utilprocs.log("'{}' is not a file or it doesn't exist.".format(file_path), severity="ERROR")
            return None
    except Exception as e:
        raise Exception ('ERROR : Issue while loading configuration.')

    return config_map