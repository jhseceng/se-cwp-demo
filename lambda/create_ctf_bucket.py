import logging
import os
import json
import time
# from functools import cached_property
import boto3
import requests

from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SUCCESS = "SUCCESS"
FAILED = "FAILED"

region = os.environ['AWS_REGION']


s3_destination_bucket = os.environ['s3_destination_bucket']



class S3BucketHandler:
    def __init__(self, region_name):
        self.region = region_name
        self.client = boto3.client('s3', region_name=self.region)

    def update(self, bucket_name, files):
        if not self._bucket_exists(bucket_name):
            self._create_bucket(bucket_name)
        for f in files:
            self._upload_file(f, bucket_name, "falcon/" + f)

    def create_bucket(self, bucket_name):
        if self._bucket_exists(bucket_name):
            return False
        else:

            logger.info("Creating Bucket {}".format(bucket_name))
            return self._create_bucket(bucket_name)

    def delete_objects(self, bucket_name):
        response = self.client.list_objects_v2(Bucket=bucket_name)
        try:
            if response.get('Contents'):
                for s3_object in response['Contents']:
                    logger.info('Deleting {}'.format(s3_object['Key']))
                    self.client.delete_object(Bucket=bucket_name, Key=s3_object['Key'])
                return True
        except Exception as e:
            logger.info('Got exception {} deleting files in bucket {}'.format(e, bucket_name))

    def delete_bucket(self, bucket_name):
        res = self.client.delete_bucket(Bucket=bucket_name)
        logger.info('Got result {}'.format(res))
        if res['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False

    def s3_copy_file(self, source_bucket, destination_bucket, s3_file):
        # Copy Source Object
        copy_source_object = {'Bucket': source_bucket, 'Key': s3_file}

        # S3 copy object operation
        self.client.copy_object(CopySource=copy_source_object, Bucket=destination_bucket, Key=s3_file)
        return True

    def _bucket_exists(self, bucket_name):
        """
        Checks that the S3 bucket exists in the region
        :param bucket_name: The name of the S3 bucket
        :return: True or False
        """
        try:
            response = self.client.list_buckets()
        except ClientError as e:
            print('Error listing buckets {}'.format(e))

        # Output True if bucket exists

        for bucket in response['Buckets']:
            if bucket_name == bucket["Name"]:
                print('Bucket already exists:')
                return True
        return False

    def _create_bucket(self, bucket_name):
        """Create an S3 bucket

        :param bucket_name: Bucket to create
        :return: True if bucket created, else False
        """

        print('Creating bucket:')
        location = {'LocationConstraint': self.region}
        try:
            result = self.client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
            if result['ResponseMetadata']['HTTPStatusCode'] == 200:
                return True
            else:
                return False
        except Exception as e:
            logger.info("Got exception {} creating bucket".format(e))

    def _upload_file(self, file_name, bucket, object_name=None):
        """Upload a file to an S3 bucket

        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """
        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        try:
            start_time = time.time()
            print('Uploading file {}:'.format(file_name))
            content = open(file_name, 'rb')
            self.client.put_object(
                Bucket=bucket,
                Key=object_name,
                Body=content
            )
            print("Successfully finished uploading files to s3 bucket. Took {}s".format(
                time.time() - start_time))
        except Exception as e:
            print('Upload error {}'.format(e))
            return False
        return True

    # @cached_property
    def _client(self):
        return boto3.client('s3', region_name=self.region)


def create_ctf_bucket(dest_bucket):
    CTFBucket = S3BucketHandler(region)
    if CTFBucket.create_bucket(dest_bucket):
        return True
    else:
        return False


def delete_ctf_bucket(bucket):
    CTFBucket = S3BucketHandler(region)
    CTFBucket.delete_objects(bucket)
    CTFBucket.delete_bucket(bucket)


def cfnresponse_send(event, context, responseStatus, responseData, physicalResourceId='', noEcho=False):
    responseUrl = event['ResponseURL']

    print(responseUrl)

    responseBody = {'Status': responseStatus, 'StackId': event['StackId'],
                    'PhysicalResourceId': str(event['ServiceToken']), 'RequestId': event['RequestId'], 'NoEcho': noEcho,
                    'LogicalResourceId': event['LogicalResourceId'], 'Data': responseData}

    json_responseBody = json.dumps(responseBody)

    print("Response body:\n" + json_responseBody)
    logger.info('Response body:\n {}'.format(responseBody))
    logger.info('PhysicalResourceId {}'.format(responseBody['PhysicalResourceId']))

    headers = {
        'content-type' : '',
        'content-length' : str(len(json_responseBody))
    }

    try:
        response = requests.put(responseUrl,
                                data=json_responseBody,
                                headers=headers)
        print("Status code: " + response.reason)
    except Exception as e:
        print("send(..) failed executing requests.put(..): " + str(e))


def lambda_handler(event, context):
    logger.info('Got event {}'.format(event))
    logger.info('Context {}'.format(context))
    logger.info('Context.log_stream_name {}'.format(context.log_stream_name))
    logger.info('Context type {}'.format(type(context)))
    responseData = {}
    if event['RequestType'] in ['Create']:
        logger.info('Event = ' + event['RequestType'])

        if create_ctf_bucket(s3_destination_bucket):
            CRWD_Discover_result = 'Success'
            logger.info('sending cfn success')
            cfnresponse_send(event, context, SUCCESS, responseData)
            return
        else:
            CRWD_Discover_result = 'Failed'
            cfnresponse_send(event, context, SUCCESS, responseData)
            return
    elif event['RequestType'] in ['Update']:
        logger.info('Event = ' + event['RequestType'])
        cfnresponse_send(event, context, SUCCESS, responseData)
        return
    elif event['RequestType'] in ['Delete']:
        delete_ctf_bucket(s3_destination_bucket)
        logger.info('Event = ' + event['RequestType'])
        cfnresponse_send(event, context, SUCCESS, responseData)
        return


if __name__ == '__main__':
    event = {
        "RequestType": "Create",
        "ServiceToken": "arn:aws:lambda:us-east-2:517716713836:function:devdays10-CreateSSMDocument-14YFU5VEOMO12",
        "ResponseURL": "https:\/\/cloudformation-custom-resource-response-useast2.s3.us-east-2.amazonaws.com\/arn%3Aaws%3Acloudformation%3Aus-east-2%3A517716713836%3Astack\/devdays10\/0582c230-0412-11eb-af35-0a88c1bcd424%7CTriggerLambda%7Cfd9e5caa-a2c8-4f3b-a7d8-71767f00fb24?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20201001T182718Z&X-Amz-SignedHeaders=host&X-Amz-Expires=7200&X-Amz-Credential=AKIAVRFIPK6PJGXMVAWW%2F20201001%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Signature=49ab44a3e5cfdfc3392429576e14f6bab2d61cb3f1113735ffba0c7d001ea533",
        "StackId": "arn:aws:cloudformation:us-east-2:517716713836:stack\/devdays10\/0582c230-0412-11eb-af35-0a88c1bcd424",
        "RequestId": "fd9e5caa-a2c8-4f3b-a7d8-71767f00fb24",
        "LogicalResourceId": "TriggerLambda",
        "ResourceType": "Custom::TriggerLambda",
        "ResourceProperties": {
            "ServiceToken": "arn:aws:lambda:us-east-2:517716713836:function:devdays10-CreateSSMDocument-14YFU5VEOMO12"
        }
    }
    context = ()
    lambda_handler(event, context)
