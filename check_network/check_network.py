import requests, time, os, signal, sys
import argparse, yaml, subprocess, glob
from datetime import datetime
from dateutil import tz

SLEEP_TIME_PRD = 60
SLEEP_TIME_DEV = 10

URL1 = "http://worldtimeapi.org/api/timezone/America/Los_angeles"
URL2 = "http://worldclockapi.com/api/json/utc/now"

# --------------------------------------------------------------------
class MetaLog:
    def __init__(self, verbose, metalog_dir, metalog_fn):
        self.__verbose = verbose
        self.__metalog_dir = metalog_dir
        self.__metalog_fn = metalog_fn
        self.__fhinfo = None
        self.__fherr = None

    def logOpen(self):
        if self.__verbose:
            self.__fhinfo = open(self.__metalog_dir+"/"+self.__metalog_fn+".out", "w")
            self.__fherr = open(self.__metalog_dir+"/"+self.__metalog_fn+".err", "w")

    def logInfo(self, msg):
        if self.__verbose:
            log_time = datetime.now().strftime("%a %d %T")
            if self.__fhinfo:
                self.__fhinfo.write(f'{log_time} {msg}\n')
                self.__fhinfo.flush()

    def logError(self, msg):
        if self.__verbose:
            log_time = datetime.now().strftime("%a %d %T")
            if self.__fherr:
                self.__fherr.write(f'{log_time} Error: {msg}\n')
                self.__fherror.flush()

    def logClose(self):
        if self.__fhinfo:
            self.__fhinfo.close()
        if self.__fherr:
            self.__fherr.close()

# --------------------------------------------------------------------
class LogFile:
    def __init__(self, log_dir, log_fn, metalog):
        # these are accessible via getter/setter fns
        self.__log_dir = log_dir
        self.__log_fn = log_fn
        self.__save_fn = None
        self.__file_handle = None

        # these are strictly private
        self.__filename = f"{self.__log_dir}/{self.__log_fn}"
        self.__curr_time = None
        self.__file_open = False
        self.__metalog = metalog

    # getter/setter for __log_dir
    @property
    def log_dir(self):
        return self.__log_dir

    @log_dir.setter
    def log_dir(self, value):
        self.__log_dir = value

    # getter/setter for __log_fn
    @property
    def log_fn(self):
        return self.__log_fn

    @log_fn.setter
    def log_fn(self, value):
        self.__log_fn = value

    # getter for __save_fn
    @property
    def save_fn(self):
        return self.__save_fn

    # getter for __file_handle
    @property
    def file_handle(self):
        return self.__file_handle

    # create a permanent filename with log_fn and curr date/time
    def setArchiveFilename(self):
        self.__curr_time = datetime.now().strftime("%FT%T")
        self.__save_fn = f"{self.__filename}_{self.__curr_time}.log"

    # open the log file
    def logOpen(self):
        if self.__file_open:
            self.__metalog.logError("Log file already open")
        else:
            if self.__file_handle is None:
                self.__metalog.logInfo("Opening log file")
                self.setArchiveFilename()
                self.__file_handle = open(f"{self.__filename}.log", "w")
                self.__file_open = True
            else:
                self.__metalog.logError("Log file handle is already open")

#    # open the log file
#    def logOpen(self):
#        if self.__file_open:
#            self.__metalog.logError("Log file already open")
#        else:
#            if self.__file_handle is None:
#                self.__metalog.logInfo("Opening log file")
#                if self.__save_fn is None:
#                    self.setArchiveFilename()
#                self.__file_handle = open(self.__log_dir+"/"+self.__save_fn, "w")
#                self.__file_open = True
#            else:
#                self.__metalog.logError("Log file handle is already open")

    # close the log file
    def logClose(self):
        if not self.__file_open:
            self.__metalog.logError("Log file not open, cannot close")
        else:
            self.__metalog.logInfo("Closing log file")
            if self.__file_handle is None:
                self.__metalog.logError("Log file handle is None, cannot close")
            else:
                self.__file_handle.close()
                self.__file_handle = None
            self.__file_open = False

            # save to timestamped file
            try:
                os.rename(f"{self.__filename}.log", self.__save_fn)
            except:
                self.__metalog.logError("Unable to rename log file after logClose")
                
    # change the log file
    def logChange(self, sigtype):
        self.__metalog.logInfo("Changing log file")
        self.logClose()
        if sigtype == "USR1":
            self.__metalog.logInfo("USR1 merging log files")
            tempFN = self.__save_fn.split('T')[0]
            cmd = f"cat {tempFN}T* > {tempFN}.log"
            res = subprocess.run(cmd, shell=True)
            files = glob.glob(f"{tempFN}T*")
            for f in files:
                try:
                    os.remove(f)
                except:
                    pass
        if sigtype == "USR2":
            self.__metalog.logInfo("USR2 renaming log files")
        self.logOpen()

#    # change the log file
#    def logChange(self, sigtype):
#        self.__metalog.logInfo("Changing log file")
#        self.logClose()
#        if sigtype == "USR1":
#        if sigtype == "USR2":
#            self.setArchiveFilename()
#        self.logOpen()

# --------------------------------------------------------------------
class SignalHandler:
    def __init__(self):
        self.__kill_now = False
        self.__log_change = False
        self.__sigtype = None

        # handler for SIGUSR1
        # daily log change over
        signal.signal(signal.SIGUSR1, self.sigusr1)

        # handler for SIGUSR2
        # ad hoc log change over
        signal.signal(signal.SIGUSR2, self.sigusr2)

        # handlers for SIGINT, SIGTERM
        # interrupt/terminate the job
        signal.signal(signal.SIGINT,  self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    # getter/setter for __kill_now
    @property
    def kill_now(self):
        return self.__kill_now

    @kill_now.setter
    def kill_now(self, value):
        self.__kill_now = value

    # getter/setter for __log_change
    @property
    def log_change(self):
        return self.__log_change

    @log_change.setter
    def log_change(self, value):
        self.__log_change = value

    # getter/setter for __sigtype
    @property
    def sigtype(self):
        return self.__sigtype

    @sigtype.setter
    def sigtype(self, value):
        self.__sigtype = value

    # define signal handler functions
    def exit_gracefully(self, *args):
        self.__kill_now = True
        self.__sigtype = "TERM"

    def sigusr1(self, *args):
        self.__log_change = True
        self.__sigtype = "USR1"

    def sigusr2(self, *args):
        self.__log_change = True
        self.__sigtype = "USR2"

# --------------------------------------------------------------------
def convert_utc_to_local(time_in_utc, timestr):
    from_zone = tz.gettz('UTC')
    to_zone = tz.tzlocal()
    utc = datetime.strptime(time_in_utc, timestr)
    utc = utc.replace(tzinfo=from_zone)
    return utc.astimezone(to_zone)

# --------------------------------------------------------------------
def check_network(logFile, api):
    try:
        response = requests.get(url=api["url"], timeout=30)
        response.raise_for_status()
    except requests.ConnectionError as e:
        fh = logFile.file_handle
        fh.write("  *** Connection Error\n")
        fh.write(str(e)+'\n')      
        fh.flush()
        return None
    except requests.Timeout as e:
        fh = logFile.file_handle
        fh.write("  *** Timeout Error\n")
        fh.write(str(e)+'\n')      
        fh.flush()
        return None
    except requests.RequestException as e:
        fh = logFile.file_handle
        fh.write("  *** General Error\n")
        fh.write(str(e)+'\n')      
        fh.flush()
        return None
    except Exception as e:
        fh = logFile.file_handle
        fh.write("  *** Another kind of error!\n")
        fh.write(str(e)+'\n')      
        fh.flush()
        return None
    else:
        if api["type"] == "time":
            result = response.json()[api["key"]]
        else:
            result = "Ok"

    return result

# --------------------------------------------------------------------
def get_config( config_file ):
    # define default configuration values
    config = {
        "log_dir": "/var/tmp",
        "log_fn": "check_network",
        "metalog_dir": "/var/tmp",
        "metalog_fn": "check_network",
        "sleep_time": 60,
        "scratch_dir": "/var/tmp",
        "rotate": 0,
        "api_list": [
            {
             "name": "worldtimeapi",
             "type": "time",
             "url": "http://worldtimeapi.org/api/timezone/America/Los_angeles",
             "key": "utc_datetime",
             "timestr": "%Y-%m-%dT%H:%M:%S.%f+00:00"
            }
          ]
        }

    # read configuration file
    if os.path.exists( config_file ):
        with open(config_file) as f:
            config_dict = yaml.load(f, Loader=yaml.SafeLoader)
    else:
        print(f"Configuration file {config_file} not found. Exiting.")
        sys.exit(1)

    # override configuration from config file
    for key in config_dict:
        config[key] = config_dict[key]
    
    return config

# --------------------------------------------------------------------

if __name__ == '__main__':
    # get command line arguments
    parser = argparse.ArgumentParser( description = "A Network Health Monitor" )
    parser.add_argument("-c","--config",help="Configuration file name (check_network.yml)", nargs="?",default="check_network.yml")
    parser.add_argument("-v","--verbose",help="Show info messages (false)", action="store_true")
    args = parser.parse_args() # parse the command line

    # define configuration
    config = get_config( args.config )

    # get and save current PID to a file
    pid = os.getpid()
    pidFile = config["scratch_dir"] + "/check_network.pid"
    fh = open( pidFile, "w")
    fh.write(f'{pid}\n')
    fh.close()

    # create the metalog (for info messages)
    metalog = MetaLog(args.verbose, config["metalog_dir"], config["metalog_fn"])
    metalog.logOpen()

    # start logging
    logFile = LogFile(config["log_dir"], config["log_fn"], metalog)
    logFile.logOpen()

    handler = SignalHandler()
    num_api = len(config['api_list'])
    api_ix = 0
    while not handler.kill_now:
        curr_api = config['api_list'][api_ix]
        if handler.log_change:
            logFile.logChange( handler.sigtype )
            handler.log_change = False

        curr_time = datetime.now().strftime("%a %d %T")
        data = check_network(logFile, curr_api)
        if data is None:
            fh = logFile.file_handle
            try:
                fh.write(f"{curr_time} {curr_api['name']} Network error\n")
                fh.flush()
            except:
                metalog.logError("Log file handle invalid!")
                sys.exit(-1)
            api_ix = (api_ix + 1) % num_api
        else:
            if "timestr" in curr_api:
                status = convert_utc_to_local(data, curr_api['timestr']).time()
            else:
                status = data
            fh = logFile.file_handle
            try:
                fh.write(f"{curr_time} {curr_api['name']} {status}\n")
                fh.flush()
            except:
                metalog.logError("Log file handle invalid!")
                sys.exit(-1)
            if config['rotate']:
                api_ix = (api_ix + 1) % num_api

        time.sleep(config["sleep_time"])

    logFile.logClose()

    if os.path.exists(pidFile):
        os.remove(pidFile)

    metalog.logInfo("Done!")
    metalog.logClose()
