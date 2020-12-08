import json

import boto3

AWS_SQS_QUEUE_NAME = "test-queue"


class SQSQueue(object):
    def __init__(self, queue_name: str, region_name: str):
        self.queue_name = queue_name
        self.region_name = region_name

        self.resource = boto3.resource("sqs", region_name=self.region_name)
        self.queue = self.resource.get_queue_by_name(QueueName=self.queue_name)

    def __repr__(self):
        return f"Queue name is {self.queue_name} and region is {self.region_name}"

    def __str__(self):
        return f"Queue name is {self.queue_name} and region is {self.region_name}"

    def send(self, send_message=None) -> object:
        if send_message is None:
            send_message = {}
        response_data = json.dumps(send_message)
        response = self.queue.send_message(MessageBody=response_data)
        return response

    def receive(self):
        try:
            queue = self.resource.get_queue_by_name(QueueName=self.queue_name)
            for message in queue.receive_messages():
                assert isinstance(message.body, object)
                data = json.loads(message.body)
                message.delete()
            return data
        except Exception as e:
            print(e)
            return []


if __name__ == "__main__":
    q = SQSQueue(queue_name=AWS_SQS_QUEUE_NAME, region_name="eu-west-1")
    json_dict = {
        "metadata": {
            "customerIDString": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "offset": 14947764,
            "eventType": "DetectionSummaryEvent",
            "eventCreationTime": 1536846439000,
            "version": "1.0",
        },
        "event": {
            "ProcessStartTime": 1536846339,
            "ProcessEndTime": 0,
            "ProcessId": 38684386611,
            "ParentProcessId": 38682494050,
            "ComputerName": "CS-SE-EZ64",
            "UserName": "demo",
            "DetectName": "Process Terminated",
            "DetectDescription": "Terminated a process related to the deletion of backups,which is often indicative "
                                 "of ransomware activity.",
            "Severity": 4,
            "SeverityName": "High",
            "FileName": "explorer.exe",
            "FilePath": "\\Device\\HarddiskVolume1\\Windows",
            "CommandLine": "C:\\Windows\\Explorer.EXE",
            "SHA256String": "6a671b92a69755de6fd063fcbe4ba926d83b49f78c42dbaeed8cdb6bbc57576a",
            "MD5String": "ac4c51eb24aa95b77f705ab159189e24",
            "MachineDomain": "CS-SE-EZ64",
            "FalconHostLink": "https:\/\/falcon.crowdstrike.com\/activity\/detections\/detail\/ec86abd353824e96765ecbe18eb4f0b4\/38655257584?_cid=xxxxxxxxxxxxxxxxxx",
            "SensorId": "ec86abd353824e96765ecbe18eb4f0b4",
            "DetectId": "ldt:ec86abd353824e96765ecbe18eb4f0b4:38655257584",
            "LocalIP": "xx.xx.xx.xx",
            "MACAddress": "xx-xx-xx-xx-xx",
            "Tactic": "Malware",
            "Technique": "Ransomware",
            "Objective": "Falcon Detection Method",
            "PatternDispositionDescription": "Prevention,process killed.",
            "PatternDispositionValue": 16,
            "PatternDispositionFlags": {
                "Indicator": "false",
                "Detect": "false",
                "InddetMask": "false",
                "SensorOnly": "false",
                "Rooting": "false",
                "KillProcess": "true",
                "KillSubProcess": "false",
                "QuarantineMachine": "false",
                "QuarantineFile": "false",
                "PolicyDisabled": "false",
                "KillParent": "false",
                "OperationBlocked": "false",
                "ProcessBlocked": "false",
            },
        },
    }
    Message = json_dict

    response = q.send(send_message=Message)
    # print(response)
    data = q.receive()
    print(data)
