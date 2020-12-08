##entry.py
##python3.7
##DCS 9/12/18
##Work@Crowdstrike

#entry.py serves as the entry point for execution
#starts up the streaming API and listens for events on a queue
#once an event is added, dispatches threads to process

from queue import Queue
from time import sleep
import threading
import datetime
import awsquery
import stream
import sender
import logger
import credvault
import traceback



class Entry():
    def __init__(self):
        #startup streaming thread
        self.logger = logger.Logger()
        # self.group = fileenc.fileEnc(self.logger)
        self.group = credvault.CredVault(self.logger)
        self.group = self.group.get()
        self.detection_queue = Queue()
        self.check_queue = Queue()
        self.ec2_queue = Queue()
        # self.cache = cache.Cache(self.logger)
        self.aws_query = awsquery.AWSQuery(self.logger, self.ec2_queue)
        self.s = stream.Stream(self.detection_queue, self.logger, self.group)
        self.sender = sender.Sender(self.logger)
        self.region = self.sender.getRegion()
        # self.account = boto3.client('sts').get_caller_identity().get('Account')
        t = threading.Thread(target=self.s.main)
        print("starting stream thread ")
        t.start()
        t1 = threading.Thread(target=self.aws_query.main, args=(self.check_queue,))
        print("starting query thread ")
        t1.start()
        # t2 = threading.Thread(target=self.falconhostquery.main)
        # print("starting cacge thread ")
        # t2.start()
        print("Setup done, wait for detections........")
        self.ingest()

    def ingest(self):
        # ingest begins after the stream thread is running, it looks for new
        # detection events in the queue, and dispatches threads to process them
        # @params None
        # @returns None
        while True:
            sleep(10)
            #returns false if empty
            if self.detection_queue.empty():
                pass
            else:
                print("Queue Size: " + str(self.detection_queue.qsize()))
                #new event to be processed
                try:
                    #get it's ComputerName and IP
                    detection_event = self.detection_queue.get()
                    # mac = detection_event['event']['MACAddress']
                    ComputerName = detection_event['event']['ComputerName']
                    ip =  detection_event['event']['LocalIP']
                    self.logger.statusWrite("ComputerName and IP from event is {} {}".format(ip, ComputerName))
                except:
                    self.logger.errorWrite("Could not collect info for event")
                    continue
                #add the new detect to be chekced
                self.logger.statusWrite('Send the event to the check_queue {}'.format(detection_event))
                try:
                    self.check_queue.put([[ComputerName,ip],detection_event],timeout=1)
                except Exception as e:
                    self.logger.errorWrite(
                        "Could not write to queue Exception %s" % (e))
            if self.ec2_queue.empty():
                self.logger.statusWrite("ec2_queue is empty")
                pass
            else:
                aws_info = self.ec2_queue.get()
                self.logger.statusWrite("Got aws info from queue %s" %(aws_info))
                print("Got info from queue: ")
                #we have all the info we need a thread to send it
                self.logger.statusWrite("starting translate thread:")
                t = threading.Thread(target=self.translate, args=(aws_info[4],aws_info))
                t.start()

    def translate(self,detection_event,aws_info):
        # translate will translate the event and aws_info into what the securityhub manifest needs
        # it will then send it to the securityhub endpoint
        # @params detection_event: the detection event
        # @params aws_info: the aws metadata
        # @returns None
        self.logger.outputWrite('Called entry.translate')
        print(f"Running translate")
        manifest = {}
        try:
            manifest['SchemaVersion'] = "2018-10-08"
            manifest['ProductArn'] = "arn:aws:securityhub:%s:517716713836:product/crowdstrike/crowdstrike-falcon" %self.region
            manifest['AwsAccountId'] = aws_info[0]
            manifest['Id'] = aws_info[1] + detection_event['event']['DetectId']
            manifest['GeneratorId'] = "Falcon Host"
            manifest['Types'] = ["Namespace: Threat Detections"]
            t_utc = datetime.datetime.utcfromtimestamp(float(detection_event['metadata']['eventCreationTime'])/1000.)
            t_utc = (t_utc.isoformat()+'Z')
            t_curr = (datetime.datetime.utcfromtimestamp(datetime.datetime.timestamp(datetime.datetime.now())))
            t_curr = (t_curr.isoformat()+'Z')
            manifest['CreatedAt'] = t_utc
            manifest['UpdatedAt'] = t_curr
            manifest['RecordState'] = "ACTIVE"
            severityProduct = detection_event['event']['Severity']
            severityNormalized = severityProduct * 20
            manifest['Severity'] = {"Product": severityProduct, "Normalized": severityNormalized}
            manifest['Title'] = "Falcon Alert. Instance: %s" %aws_info[1]
            manifest['Description'] = detection_event['event']['DetectDescription']
            manifest['SourceUrl'] = detection_event['event']['FalconHostLink']
            manifest['Resources'] = [{'Type':"AwsEc2Instance", 'Id':aws_info[1], 'Region': aws_info[2]}]
        except:
            self.logger.errorWrite("Could not translate info for event %s\n%s" %(detection_event['event']['DetectId'],traceback.format_exc()))
            return
        try:
            manifest['Types'] = ["Namespace: TTPs", "Category: %s"%detection_event['event']['Tactic'] , "Classifier: %s"%detection_event['event']['Technique']]
        except:
            pass
        try:
            manifest['Process'] = {}
            manifest['Process']['Name'] = detection_event['event']['FileName']
            manifest['Process']['Path'] = detection_event['event']['FilePath']
        except:
            manifest.pop('Process', None)
        try:
            manifest['Network'] = {}
            manifest['Network']['Direction'] = "IN" if detection_event['event']['NetworkAccesses'][0]['ConnectionDirection'] == 0 else 'OUT'
            manifest['Network']['Protocol'] = detection_event['event']['NetworkAccesses'][0]['Protocol']
            manifest['Network']['SourceIpV4'] = detection_event['event']['NetworkAccesses'][0]['LocalAddress']
            manifest['Network']['SourcePort'] = detection_event['event']['NetworkAccesses'][0]['LocalPort']
            manifest['Network']['DestinationIpV4'] = detection_event['event']['NetworkAccesses'][0]['RemoteAddress']
            manifest['Network']['DestinationPort'] = detection_event['event']['NetworkAccesses'][0]['RemotePort']
        except:
            manifest.pop('Network', None)
        self.logger.outputWrite(manifest)
        self.logger.outputWrite('Sending manifest')
        self.logger.statusWrite("Calling sender send:")
        self.sender.send(manifest)
        return
Entry()
