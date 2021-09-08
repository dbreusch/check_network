# check_network
A utility to keep an eye on the status of your internet connection.

Composed of three main file groups:
1. Python script `check_network.py` and its configuration file `check_network.yml`
2. Utility scripts to run and manage the log
3. Launchctl plists to run `check_network.py` in the background

## Python script and configuration file
### check_network.py
This is the heart of this utility: a Python script to programmatically test your internet connection.

Results are written to a log file (name and location set in configuration file). This log can be switched in two ways:
- by sending a SIGUSR1: the active log file is moved to a timestamped file and restarted.  Existing timestamped files are then merged into a single daily log file (timestamped to the day). This usage is expected to happen daily, just after midnight, to build up a daily record of log files.
- by sending a SIGUSR2: the active log file is moved to a timestamped file and restarted.  This is intended as an ad hoc way to restart the log (e.g., for troubleshooting).

#### Command line arguments
`check_network.py` takes two optional arguments:
- -c filename | --config=filename  configuration file (defaults to check_network.yml)
- -v | --verbose  write metalog messages (messages about the app)

#### pidfile
After startup, `check_network.py` will write its PID to a file (hardcoded as `check_network.pid`) to make it easier to send signals to the running process.  The location of this file is set in the configuration file with option `scratch_dir` (defaults to "/var/tmp").

This file will be removed automatically on clean shutdown.

Future enhancement: make name of pidfile configurable so that more than one instance of check_network can be active at once.

### check_network.yml
A configuration file for `check_network.py`.  If this file is not present, options have defaults in the script.  In this case, only one URL will be available for checking.  The default configuration file repeats standard options and adds four additional URLs for testing.

Note that the wrapper script `run_check_network` (see below) assumes the configuration file is in the same directory as `check_network.py`.

#### Example check_network.yml
```
log_dir: /var/tmp/nlogs
log_fn: check_network

metalog_fn: check_network
metalog_dir: /var/tmp/nlogs

sleep_time: 60
rotate: 1

api_list:
  - name: worldtimeapi
    type: time
    url: http://worldtimeapi.org/api/timezone/America/Los_angeles
    key: utc_datetime
    timestr: "%Y-%m-%dT%H:%M:%S.%f+00:00"

  - name: worldclockapi
    type: time
    url: http://worldclockapi.com/api/json/utc/now
    key: currentDateTime
    timestr: "%Y-%m-%dT%H:%MZ"

  - name: swapi
    type: other
    url: https://swapi.dev/api/

  - name: geonames
    type: other
    url: "http://api.geonames.org/weatherJSON?formatted=true&north=48&south=47&east=-122&west=-123&username=gandalf&style=full"

  - name: httpcat
    type: other
    url: https://http.cat/200
```
log_dir and log_fn specify where the normal network logging messages are stored.
metalog_dir and metalog_fn specify where, when running in verbose mode, messages about the logging process are stored (for example, when the log is rolled over, a message is written to the metalog).
sleep_time is the number of seconds between network checks.
rotate: whether the URLs are rotated through between checks (assuming more than one is defined).  Note that the URL will always be rotated after an error.

Warning: as of this version of the code (1.0.0), `log_dir` and `metalog_dir` must already exist or the respective file open will fail.  This is something I intend to improve in the future.

## Utility scripts to run and manage the log
- `run_check_network`
Wrapper script to run `check_network.py`, accepts the same arguments.  Runs `check_network.py` using the `poetry` virtual environment manager.

- `check_network_switch.py`
Sends a SIGUSR1 to the running `check_network.py` process to rollover the log file.

## Launchctl plists to run check_network in the background
For macOS environments, two launchctl plists support starting the script and switching the log.
-  `local.check_network.start.plist`
Start the network monitoring script (RunAtLoad=True)
- `local.check_network.switch-log-file.plist`
Trigger a daily log rollover (just after midnight)

# The virtual environment
`check_network.py` runs in a virtual environment managed by `poetry`.  It assumes that `poetry` is installed and available and will exit if it is not.

# Output files
Output files:
  `log_dir/check_network.log`
  `log_dir/check_network_yyyy-mm-dd.log`
  `log_dir/check_network_yyyy-mm-ddTHH:MM:SS.log`

If verbose is true:
  `metalog_dir/check_network.err`
  `metalog_dir/check_network.out`

# Installation
## The virtual environment
`check_network.py` runs in a virtual environment managed by [poetry](https://python-poetry.org/docs/basic-usage/).  It assumes that `poetry` is installed and available and will exit if it is not.

To install Python dependencies under `poetry` (so you can run this script), in the main folder (which will contain `pyproject.toml`), run `poetry install`.

## Customizing files and setup
Utility scripts to edit for local directories and command line arguments:
- `run_check_network`
- `check_network_switch.py`
Move (or copy) these to a `bin` folder on your path for convenience.

Configuration file `check_network.yml`: edit for your runtime options.

If this is a macOS setup, edit these plists for local directories and command line arguments:
- `local.check_network.start.plist`
- `local.check_network.switch-log-file.plist`
Move (or copy) these to ~/Library/LaunchAgents.

# Startup and shutdown
If using launchctl, load `local.check_network.start.plist` to start running `check_network.py` and logging your internet status.  Unload it to stop.

If you want to automatically rollover the log -- and are using launchctl -- load `local.check_network.switch-log-file.plist` to have this scheduled.  Unload it to stop.

If you just want to use the command line (or crontab), run script `run_check_network` with the desired arguments.

Whichever method is used to start `check_network.py`, it can be cleanly shutdown either with Ctrl-C or by sending a SIGKILL or SIGTERM signal.
