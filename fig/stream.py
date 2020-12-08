##python3.7
##Dixon Styres 8/29/18
##Work@Crowdstrike

#streaming.py This class interacts with the streaming API and fills a common Queue with detection Events

import hashlib
import os
import base64
import time
import datetime
import hmac
import requests
import json
import threading
import traceback

class Stream():
    def __init__(self, detection_queue,logger, group):
        #get keys from config files
        self.KEY = group[0].encode("utf-8")
        self.UUID = group[1]
        self.canonical = 'firehose.crowdstrike.com/sensors/entities/datafeed/v1'
        self.app_id = group[2]
        self.priority = group[3]
        self.detection_queue = detection_queue
        self.logger = logger

    def main(self):
        #see if we have a saved offset to resume at, else set it high and get the
        #next event
        try:
            with open("offset", 'r') as f:
                offset = f.readline()
        except :
            offset = 99999999
        try:
            response = self.get_streams()
        except:
            self.logger.errorWrite( "Failed to run")
            time.sleep(15)
        threads = []
        i = 0
        try:
            for stream in response['resources']:
                i = i + 1
                data_url = stream['dataFeedURL']
                token = stream['sessionToken']['token']
                threads.append(threading.Thread(target=self.stream, args=(data_url, token, offset)))
                threads[-1].start()
                time.sleep(5)
            self.logger.statusWrite("Waiting for stream threads completed")
            for t in threads:
                t.join()
                self.logger.statusWrite("Event Occurance Completed")
        except:
            self.logger.errorWrite("Failed to get stream token")
        self.main()

    def sha(self,content):
        # Calculate MD5 hash of request body. Blank if request body is blank
        # @params content: the request body
        # @returns encoded base64string
        if content != None:
            hash = hashlib.md5(content).hexdigest()
            base64string = base64.encodestring(hash)
        else:
            base64string = ''
        return base64string

    def get_streams(self):
        # get stream auth token
        # @returns the data_url and token for the stream
        body = None
        md5 = self.sha(body)
        t1 = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
        query_string = 'appId=%s' % self.app_id
        #Computer Request String
        request = '%s\n%s\n%s\n%s\n%s' % ('GET', md5, t1, self.canonical, query_string)
        #Calculate signature
        hash = hmac.new(self.KEY, request.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(hash).decode()

        request_url = 'https://%s?%s' % (self.canonical, query_string)
        headers = {'Authorization': 'cs-hmac %s:%s:%s' % (self.UUID, signature, 'customers'), 'Date': t1}
        r = requests.get(request_url, headers=headers)
        response = r.json()
        try:
            data_url = response['resources'][0]['dataFeedURL']
            token = response['resources'][0]['sessionToken']['token']
            self.logger.statusWrite("get_stream got a response")
            return response
        except:
            self.logger.errorWrite("Unable to get stream_url or token check appId... Sleeping for 5")
            self.logger.errorWrite("request status code %s\n%s" %(r.status_code,traceback.format_exc()))
            time.sleep(5)
            self.main()

    def stream(self, url, token, offset):
        #open the falcon stream from the url and Token
        #@param url: the stream url
        #@oaram token: the stream token
        #@param offset: the offset into the event log to begin at
        url += "&offset=%s" %offset
        try:
            epoch_time = int(time.time())
            headers={'Authorization': 'Token %s' % token, 'Connection': 'Keep-Alive'}
            r = requests.get(url, headers=headers, stream=True)
            self.logger.statusWrite("Streaming API Connection established")
            for line in r.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    decoded_line = json.loads(decoded_line)
                    if(decoded_line['metadata']['eventType'] == "DetectionSummaryEvent"):
                        if(int(self.priority) <= int(decoded_line['event']['Severity'])):
                            self.detection_queue.put(decoded_line)
                            self.logger.statusWrite("Adding to detection_queue")
                        else:
                            self.logger.statusWrite("New detection event, less than threshold %s. Skipping..." %self.priority)
                    self.logger.offsetWrite(decoded_line['metadata']['offset'])
                if(int(time.time()) > (300+epoch_time)):
                    self.logger.statusWrite("Event Window Expired")
                    return
        except:
            self.logger.errorWrite("Error reading last stream chunk")
            self.logger.errorWrite("request status code %s\n%s" %(r.status_code, traceback.format_exc()))
            os._exit(1)
