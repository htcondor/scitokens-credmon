import os
import stat
import logging
import logging.handlers
import sys

try:
    import htcondor
except ImportError:
    htcondor = None

    
def setup_logging(log_path = None, log_level = None):
    '''
    Detects the path and level for the log file from the condor_config and sets 
    up a logger. Instead of detecting the path and/or level from the 
    condor_config, a custom path and/or level for the log file can be passed as
    optional arguments.

    :param log_path: Path to custom log file
    :param log_level: Custom log level
    :return: logging.Logger object with handler WatchedFileHandler(log_path)
    '''

    # Get the log path
    if (log_path is None) and (htcondor is not None) and ('SEC_CREDENTIAL_MONITOR_LOG' in htcondor.param):
        log_path = htcondor.param['SEC_CREDENTIAL_MONITOR_LOG']
    elif (log_path is None):
        raise RuntimeError('The log file path must be specified in condor_config as SEC_CREDENTIAL_MONITOR_LOG or passed as an argument')

    # Get the log level
    if (log_level is None) and (htcondor is not None) and ('SEC_CREDENTIAL_MONITOR_LOG_LEVEL' in htcondor.param):
        log_level = logging.getLevelName(htcondor.param['SEC_CREDENTIAL_MONITOR_LOG_LEVEL'])
    if log_level is None:
        log_level = logging.INFO

    # Set up the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_handler = logging.handlers.WatchedFileHandler(log_path)
    log_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(log_handler)

    # Return a child logger with the same name as the script that called it
    child_logger = logging.getLogger(os.path.basename(sys.argv[0]))
    
    return child_logger
    
def get_cred_dir(cred_dir = None):
    '''
    Detects the path for the credential directory from the condor_config,
    makes sure the credential directory exists with the correct permissions,
    and returns the path to the credential directory. Instead of detecting the
    path from the condor_config, a custom path for the credential directory can
    be passed as an optional argument.

    :param cred_dir: Path to custom credential directory
    :return: Path to the credential directory
    '''

    # Get the location of the credential directory
    if (cred_dir is None) and (htcondor is not None) and ('SEC_CREDENTIAL_DIRECTORY' in htcondor.param):
        cred_dir = htcondor.param['SEC_CREDENTIAL_DIRECTORY']
    else:
        raise RuntimeError('The credential directory must be specified in condor_config as SEC_CREDENTIAL_DIRECTORY or passed as an argument')

    # Create the credential directory if it doesn't exist
    if not os.path.exists(cred_dir):
        os.makedirs(cred_dir, (stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR))

    # Make sure the permissions on the credential directory are correct
    try:
        if (os.stat(cred_dir).st_mode & (stat.S_IRGRP | stat.S_IROTH | stat.S_IWGRP | stat.S_IWOTH | stat.S_IXGRP | stat.S_IXOTH)):
            os.chmod(cred_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    except OSError:
        raise RuntimeError('The credmon cannot verify the permissions of the credential directory.')
    if not os.access(cred_dir, (os.R_OK | os.W_OK | os.X_OK)):
        raise RuntimeError('The credmon does not have access to the credential directory.')
        
    return cred_dir


def drop_pid(cred_dir):
    """
    Drop a PID file in the cred dir for condor to find.
    """
    curr_pid = os.getpid()
    pid_path = os.path.join(cred_dir, "pid")
    with open(pid_path, "w") as pid_fd:
        pid_fd.write("{0}".format(curr_pid))
    return

def credmon_incomplete(cred_dir):
    """
    Remove CREDMON_COMPLETE
    """
    # Arguably we should check for uptime, but it's just aklog that
    # occurs as a result, so no premature optimisation
    complete_name = os.path.join(cred_dir, 'CREDMON_COMPLETE')
    if os.path.isfile(complete_name):
        os.unlink(complete_name)

def credmon_complete(cred_dir):
    """
    Touch CREDMON_COMPLETE
    """
    complete_name = os.path.join(cred_dir, 'CREDMON_COMPLETE')
    with open(complete_name, 'a'):
        os.utime(complete_name, None)
    return

def atomic_rename(tmp_file, target_file):
    """
    If successful HTCondor will only be dealing with fully prepared and
    usable credential cache files.

    :param tmp_file: The temp file path containing
        the TGT acquired from the ngbauth service.
    :type tmp_file: string
    :param target_file: The target file.
    :return: Whether the chmod/rename was successful.
    :rtype: bool
    """
    
    os.chmod(tmp_file, stat.S_IRUSR)
    #os.chown(tmp_file, 0, 0)
    os.rename(tmp_file, target_file)

