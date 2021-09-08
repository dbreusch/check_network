#!/usr/bin/env python3
import os, subprocess

pidFile = "/var/tmp/check_network.pid"
if os.path.exists(pidFile):
    fh = open(pidFile, "r")
    pid = fh.readlines()[0].split()[0]
#    print(pid)
    fh.close()

    cmd = f'/usr/local/bin/bash -c "kill -s SIGUSR1 {pid}"'
#    print(cmd)
    res = subprocess.run(cmd, shell=True)
#    print(res)
