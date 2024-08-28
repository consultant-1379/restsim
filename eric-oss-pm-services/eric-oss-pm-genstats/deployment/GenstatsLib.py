import sys, os
from subprocess import PIPE, Popen, STDOUT
from shlex import split

def command_run(user_name, commandArgument, section="default", posix=True):

    class stdErrOutError(Exception):
        pass

    if user_name == "root":
        password = "shroot"
    elif user_name == "netsim":
        password = user_name
    else:
        print("ERROR: Unknown user. Exiting...")
        sys.exit(1)
    bashCommand = "su - " + user_name + " -c \'" + commandArgument + "\'"
    try:
        print ("Shell Command: "+ bashCommand)
        process = os.system('echo %s|sudo -S %s' % (password, bashCommand))
    except OSError:
        print ("OSError raised")
        print ("At " + section)
        sys.exit(1)
    except ValueError:
        print ("ValueError raised: Popen is called with invalid arguments.")
        print ("At " + section)
        sys.exit(1)
    except stdErrOutError:
        print ("stdErrOutError raised: stderr or stdout from Popen child process contains error")
        print ("At " + section)
        sys.exit(1)
    except:
        print ("Unexpected error: At " + section), sys.exc_info()[0]
        raise
        sys.exit(1)