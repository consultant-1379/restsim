import argparse
import utilprocs
import os
from fileValidation import FileValidation

def parse_args():

   #Create argument parser
    parser = argparse.ArgumentParser(description='Count files with a specific extension in sub-folders.')

    parser.add_argument('--epoch-folder','-ef',
                        type = str, required = True, dest='epoch_folder',
                        help=  'Epoch folder name')
    parser.add_argument('--validate-creation-time','-ct',
                        type = utilprocs.str2bool, required = False, default = True, dest='validate_creation_time',
                        help = 'Parameter to Enable/Disable file creation time validation.')
    parser.add_argument('--validate-file-size', '-fs',
                        type = utilprocs.str2bool, required = False, default = True, dest='validate_file_size',
                        help = 'Parameter to Enable/Disable file size validation.')

    args = parser.parse_args()

    return args

def main():

    args = parse_args()

    utilprocs.create_log_dir()
    utilprocs.create_log_file()

    try:
        netsim_cfg_params = {
            'STATS_ENABLED': utilprocs.str2bool(os.getenv('STATS_ENABLED')),
            'CELLTRACE_ENABLED': utilprocs.str2bool(os.getenv('CELLTRACE_ENABLED')),
            'REPLAY_ENABLED': utilprocs.str2bool(os.getenv('REPLAY_ENABLED'))
        }

        fval = FileValidation(args, netsim_cfg_params)
        output = fval.initiateHealthCheck()
    except Exception:
        utilprocs.printException()
        raise

if __name__ == "__main__":
    main()