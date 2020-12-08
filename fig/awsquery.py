##query.py
##python3.7
##DCS 9/12/18
##Work@Crowdstrike

#query.py: as a detection is read, query API will see if it is from an EC2 instance and return relevant data

from time import sleep
import requests
import boto3
import json
import urllib
from time import sleep
import threading


class AWSQuery():
    def __init__(self,logger,ec2_queue):
        self.logger = logger
        self.ec2_queue = ec2_queue
        # self.cache = cache
        self.region = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/placement/availability-zone').read().decode()[:-1]
        self.client_id = self.get_ssm_secure_string('Falcon_ClientID')['Parameter']['Value']
        self.client_secret = self.get_ssm_secure_string('Falcon_Secret')['Parameter']['Value']


    def main(self, check_queue):
    # main will contain an infinite loop that will listen for events on the Queue
    # and process them

        while True:
            sleep(.1)
            if check_queue.empty():
                pass
            else:
                detection_event = check_queue.get()
                t = threading.Thread(target=self.hostnameMatch, args=(detection_event, self.ec2_queue))
                t.start()

    def hostnameMatch(self, detection_event, ec2_queue):
        # networkMatch will get the hostnames and query the falcon API to see if the hostname is an AWS instance.
        # @returns None
        instance_info =  self.checkawsinstance(detection_event[0])
        if instance_info != 'None':
            aws_account_id = instance_info.get('service_provider_account_id')
            instance_id = instance_info.get('instance_id')
            placement_zone = 'None'
            private_ip = instance_info.get('LocalIP')
            ec2_queue.put([aws_account_id, instance_id, placement_zone, private_ip, detection_event[1]])
            return


    def checkawsinstance(self, ComputerName):
        print('calling checkawsinstance {}'.format(ComputerName))
        host_aid = self.get_falcon_aid_from_hotsname(ComputerName[0])
        falcon_host_info = self.get_falcon_host_info(host_aid)
        service_provider =  falcon_host_info.get('service_provider','None')
        if service_provider == 'AWS_EC2':
            return falcon_host_info
        else:
            return 'None'

    def get_ssm_secure_string(self, parameter_name):
        ssm = boto3.client("ssm", region_name=self.region)
        return ssm.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )

    def get_auth_header(self, auth_token):
        if auth_token:
            auth_header = "Bearer " + auth_token
            headers = {
                "Authorization": auth_header
            }
            return headers

    def get_auth_token(self):
        url = "https://api.crowdstrike.com/oauth2/token"
        payload = 'client_secret=' + self.client_secret + '&client_id=' + self.client_id
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.ok:
            response_object = (response.json())
            token = response_object.get('access_token', '')
            if token:
                return \
                    token
        return

    def falcon_api_post(self, url, _headers, _data):
        try:
            response = requests.request("POST", url, headers=_headers, data=_data)

            json_obj = json.loads(response.text.encode('utf8'))
            if len(json_obj['resources']) != 0:
                return json_obj['resources'][0]
            else:
                return
        except Exception as e:
            print('Exception e{} posting to api'.format(e))

    def falcon_api_get(self, url, params):
        auth_token = self.get_auth_token()
        headers = self.get_auth_header(auth_token)
        response = requests.request("GET", url, headers=headers, params=params)

        json_obj = json.loads(response.text.encode('utf8'))
        if len(json_obj['resources']) != 0:
            return json_obj['resources'][0]
        else:
            return

    def get_falcon_aid_from_hotsname(self, hostname):
        print('calling get_falcon_aid {}'.format(hostname))
        host_query_filter = "hostname: '" + hostname + "'"
        auth_token = self.get_auth_token()
        auth_header = self.get_auth_header(auth_token)
        falcon_aid = self.query_falcon_host(auth_header, host_query_filter)
        return falcon_aid

    def query_falcon_host(self, auth_header, host_filter):

        url = "https://api.crowdstrike.com/devices/queries/devices/v1"
        PARAMS = {"offset": 0,
                  "limit": 10,
                  "filter": host_filter
                  }
        auth_token = self.get_auth_token()
        auth_header = self.get_auth_header(auth_token)
        response = requests.request("GET", url, headers=auth_header, params=PARAMS)

        json_obj = json.loads(response.text.encode('utf8'))
        if len(json_obj['resources']) != 0:
            return json_obj['resources'][0]
        else:
            return

    def get_falcon_host_info(self, aid):
        url = "https://api.crowdstrike.com/devices/entities/devices/v1"
        params = {"ids": aid}

        auth_token = self.get_auth_token()
        headers = self.get_auth_header(auth_token)
        info = self.falcon_api_get(url, params)
        return (info)

    def get_falcon_aid_from_instanceid(self, instanceid):
        host_query_filter = "instance_id: '" + instanceid + "'"
        auth_token = self.get_auth_token()
        auth_header = self.get_auth_header(auth_token)
        falcon_aid = self.query_falcon_host(auth_header, host_query_filter)
        return falcon_aid

