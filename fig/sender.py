##sender.py
##python3.7
##DCS 9/12/18
##Work@Crowdstrike

#sender-py: sender will receive a json object to be sent to the OB endpoint

import traceback
import boto3
import urllib.request
import os

class Sender():
    def __init__(self,logger):
        self.logger = logger
        try:
            self.session = boto3.Session()
            self.region = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/placement/availability-zone').read().decode()[:-1]

        except:
            self.logger.errorWrite("Unable to load SecurityHub Endpoint Auth... Is it enabled for the IAM role?")
            os._exit(0)
        self.client = boto3.client('securityhub', region_name=self.region)

    def send(self,log):
        try:
            findings = [log]
            import_response = self.client.batch_import_findings(Findings=findings)
            self.logger.statusWrite("Got response sending  %s:" %(import_response))
        except:
            tb = traceback.format_exc()
            self.logger.errorWrite("Unable to post log to endpoint: %s Log: %s" %(tb,findings))

    def getRegion(self):
        return self.region
