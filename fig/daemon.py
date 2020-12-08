##daemon.py
##python 3.7
##DCS 9/20/18
##Work @crowdstrike

#daemon.py starts our FIG and restarts it if it exits.

import subprocess

while True:
    p = subprocess.Popen(['python3','entry.py']).wait()
    """#if your there is an error from running 'entry.py',
    the while loop will be repeated,
    otherwise the program will break from the loop"""
    if p != 0:
        continue
    else:
        break
