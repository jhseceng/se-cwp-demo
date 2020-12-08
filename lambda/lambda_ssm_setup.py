import json
import logging
import os
import time

import boto3
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SUCCESS = "SUCCESS"
FAILED = "FAILED"

region = os.environ['AWS_REGION']
package_name = os.environ['package_name']
s3bucket = os.environ['s3bucket']
FILEPATH = 'falcon/manifest.json'

def delete_document():
    try:
        ssm_client = boto3.client('ssm', region_name=region)
        response = ssm_client.delete_document(
            Name=package_name,
            Force=True)
        if response['ResponseMetadata']['HTTPStatusCode']==200:
            logger.info('Deleted Document')
            return True
        else:
            return
    except Exception as e:
        logger.info('Got exception {} trying to delete ssm document - continue'.format(e))
        return False


def create_document():
    try:
        start_time = time.time()
        ssm_client = boto3.client('ssm', region_name=region)
        s3_client = boto3.client('s3')
        s3_object = s3_client.get_object(Bucket=s3bucket, Key=FILEPATH)
        data = s3_object.get('Body').read().decode('utf-8')
        # documentContent = openFile.read()
        logger.info('Create document conent {}'.format(data))
        documentContent = data
        createDocRequest = ssm_client.create_document(
            Content=documentContent,
            Attachments=[
                {
                    'Key': 'SourceUrl',
                    'Values': [
                        'https://' + s3bucket + '.s3-' + region + '.amazonaws.com/falcon',
                    ]
                },
            ],
            Name=package_name,
            DocumentType='Package',
            DocumentFormat='JSON'
        )
        response_data=createDocRequest.get('ResponseMetadata')
        logger.info('return type {}'.format(response_data))

        print('Created ssm package {}:'.format(package_name))
        return True
    except Exception as e:
        print('Error creating document {}'.format(e))
        return False


def cfnresponse_send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False):
    responseUrl = event['ResponseURL']
    logger.info('Got response {} {} {} {}'.format(event,context,responseStatus,responseData))
    print(responseUrl)

    responseBody = {'Status': responseStatus,
                    'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
                    'PhysicalResourceId': physicalResourceId or context.log_stream_name, 'StackId': event['StackId'],
                    'RequestId': event['RequestId'], 'LogicalResourceId': event['LogicalResourceId'], 'NoEcho': noEcho,
                    'Data': responseData}

    json_responseBody = json.dumps(responseBody)

    print("Response body:\n" + json_responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        response = requests.put(responseUrl,
                                data=json_responseBody,
                                headers=headers)
        print("Status code: " + response.reason)
    except Exception as e:
        print("send(..) failed executing requests.put(..): " + str(e))


def create_ssm_document():
    if create_document():
        logger.info
    return True


def lambda_handler(event, context):
    logger.info('Got event {}'.format(event))
    response_data = {}
    if event['RequestType'] in ['Create']:
        logger.info('Event = ' + event['RequestType'])
        if create_document():
            CRWD_Discover_result = 'Success'
            logger.info('sending cfn success')
            cfnresponse_send(event, context, SUCCESS, CRWD_Discover_result)
            return
        else:
            CRWD_Discover_result = 'Failed'
            cfnresponse_send(event, context, FAILED, CRWD_Discover_result)
            return
    elif event['RequestType'] in ['Update']:
        logger.info('Event = ' + event['RequestType'])

        cfnresponse_send(event, context, 'SUCCESS', response_data)
        return
    elif event['RequestType'] in ['Delete']:
        delete_document()
        logger.info('Event = ' + event['RequestType'])
        response_data["Status"] = "Success"
        cfnresponse_send(event, context, 'SUCCESS', response_data)
        return

if __name__ == '__main__':
    event = {
  "RequestType":"Create",
  "ServiceToken":"arn:aws:lambda:us-east-2:517716713836:function:devdays10-CreateSSMDocument-14YFU5VEOMO12",
  "ResponseURL":"https:\/\/cloudformation-custom-resource-response-useast2.s3.us-east-2.amazonaws.com\/arn%3Aaws%3Acloudformation%3Aus-east-2%3A517716713836%3Astack\/devdays10\/0582c230-0412-11eb-af35-0a88c1bcd424%7CTriggerLambda%7Cfd9e5caa-a2c8-4f3b-a7d8-71767f00fb24?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20201001T182718Z&X-Amz-SignedHeaders=host&X-Amz-Expires=7200&X-Amz-Credential=AKIAVRFIPK6PJGXMVAWW%2F20201001%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Signature=49ab44a3e5cfdfc3392429576e14f6bab2d61cb3f1113735ffba0c7d001ea533",
  "StackId":"arn:aws:cloudformation:us-east-2:517716713836:stack\/devdays10\/0582c230-0412-11eb-af35-0a88c1bcd424",
  "RequestId":"fd9e5caa-a2c8-4f3b-a7d8-71767f00fb24",
  "LogicalResourceId":"TriggerLambda",
  "ResourceType":"Custom::TriggerLambda",
  "ResourceProperties":{
    "ServiceToken":"arn:aws:lambda:us-east-2:517716713836:function:devdays10-CreateSSMDocument-14YFU5VEOMO12"
  }
}
    context = ()
    lambda_handler(event, context)