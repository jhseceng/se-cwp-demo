##logger.py
##python 3.7
##DCS 9/17/18

#logger.py opens a local logfile for write and writes logs to it

import time
import json
import logging
from logging.handlers import RotatingFileHandler

class Logger():
    def __init__(self):
        """
        Creates a rotating output log
        """
        self.outputlog = logging.getLogger("")
        self.outputlog.setLevel(logging.INFO)
        # add a rotating handler
        handler = RotatingFileHandler("output.txt", maxBytes=20971520,backupCount=5)
        self.outputlog.addHandler(handler)

    def statusWrite(self,log):
        #write will take as input an execution log and write it to the log along with the time
        # @params log: the log to write to the file
        logfile = open("OBGlog.txt", "a")
        ts = time.ctime()
        logfile.write(ts + " %s\n" %log)
        logfile.close()

    def errorWrite(self,log):
        #write will take as input an eroor log and write it to the log along with the time
        # @params log: the log to write to the file
        logfile = open("OBGErrorLog.txt", "a")
        ts = time.ctime()
        logfile.write(ts + " %s\n" %log)
        logfile.close()

    def outputWrite(self,log):
        #write will take as input an output log and write it to the log along with the time
        # @params log: the log to write to the file
        ts = time.ctime()
        self.outputlog.info(ts + "\n ")
        self.outputlog.info(json.dumps(log,indent=4))

    def offsetWrite(self,log):
        #write will take as input an offset log and write it to the log along with the time
        # @params log: the log to write to the file
        logfile = open("offset", "w")
        logfile.write(str(log))
        logfile.close()
