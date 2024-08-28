import datetime
import traceback
import os
import shutil

log_dir = 'test_logs'
log_file_name = os.path.join(log_dir, 'healthCheck.log')

def create_log_dir():
    """
    Create a new log directory and deletes an existing directory with same name.
    """
    try:
        if os.path.exists(log_dir) and os.path.isdir(log_dir):
            shutil.rmtree(log_dir)
        os.makedirs(log_dir)
    except Exception:
        raise

def create_log_file():
    """
    Create a new log file and deletes an existing file with same name.
    """
    with open(log_file_name, 'w'):
        pass

def log(message, severity="INFO"):
    """
    Adds time and date to the 'message' in a correct format.

    Parameters:
    - message (str) : message to be added in the log.
    """
    now = datetime.datetime.now()
    val = (now.date().isoformat() +
           ' ' + now.time().isoformat() +
           ': ' + str(severity.upper()) +
           ': ' + str(message))
    write_to_logfile(val)
    print(val)

def write_to_logfile(val):
    """
    Writes to the log file.

    Parameters:
    - val (str) : The string to be written to the log file.
    """
#   file_p = open(log_file_name, "a", encoding="utf-8")
    file_p = open(log_file_name, "a")
    file_p.write(val + '\n')
    file_p.close()

def title(message):
    """
    Write to stdout a nice title with the message specified

    Parameters:
    - message (str) : string to print
    """
    log("-"*65)
    log("-"*65)
    log(message)
    log("-"*65)

def str2bool(string):
    """
    Converts a string to a boolean
    Parameters:
        string: string to convert
    Returns:
        boolean
    """
    if not isinstance(string, str):
        return string
    if string.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    if string.lower() in ('no', 'false', 'f', 'n', '0'):
        return False

def printException():
    exc = traceback.format_exc()
    log(exc, severity="ERROR")