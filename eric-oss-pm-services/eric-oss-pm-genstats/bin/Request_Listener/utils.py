import configparser
import os
import math
from time import time
import sys
sys.path.append('/netsim_users/pms/bin')
import logger_utility

logger = logger_utility.LoggerUtilities()


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
            logger.print_error("{} is not a file or it doesn't exist.".format(file_path))
            sys.exit(1)

    except Exception as e:
        logger.print_error('Issue while loading configuration.')
        raise Exception('ERROR : Issue while loading configuration.')

    return config_map

def get_epoch_token(ROP_IN_SECONDS):
    utc_sys_time = math.floor(time())
    rounded_sys_time = int(utc_sys_time / ROP_IN_SECONDS) * ROP_IN_SECONDS
    return rounded_sys_time
