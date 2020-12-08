import boto3
import json
import sys
import argparse
import requests
import time
from datetime import datetime, timedelta
region = 'eu-west-1'



def run_install_package(package_name, action, instance_ids, document_name):
    parameters = {
        'action': [action],
        'installationType': ['Uninstall and reinstall'],
        'name': [package_name]
        # 'version': ['']
        }
    client = boto3.client('ssm')
    try:
        response = client.send_command(
            InstanceIds=instance_ids,
            DocumentName=document_name,
            TimeoutSeconds=300,
            Comment='Install package',
            Parameters=parameters
        )
        n = 5
        while n > 0:
            cmd_status = client.list_commands(response['Commands']['CommandId'])
            if cmd_status == 'Pending' or cmd_status == 'InProgress':
                time.sleep(5)
                # Wait 25 secs for response
                n -=1
            else:
                break

        if cmd_status == 'Success':
            res = {'Success':'InstanceIds'}
        else:
            res= {'Failure':'InstanceIds'}
        return res





    except Exception as e:
        print('Exception running package install {}'.format(e))
    print(response)







def get_ssm_info(commandId):

    client = boto3.client('ssm')
    cmd_doc = client.get_document(Name='AWS-ConfigureAWSPackage')
    cmd = client.get_command_invocation(
        CommandId=commandId,
        InstanceId='i-007bca2758712801e'
    )
    doc_desc = client.describe_document(
        # Name='AWS-ConfigureAWSPackage'
        Name='FalconSensor')
    cmd_invoke = client.list_command_invocations(
        CommandId=commandId,
    )
    cmd_list = client.list_commands(
        CommandId=commandId,
    )
    print('cmd invocation \n{}\n'.format(cmd))
    print('cmd doc \n{}\n'.format(cmd_doc))
    print('describe doc \n{}\n'.format(doc_desc))
    print('desc invoke doc \n{}\n'.format(cmd_invoke))
    print(cmd_list['Commands'][0]['Parameters'])


def get_managed_instances():
    # managed_instance_dict={}
    client = boto3.client('ssm', region_name=region)
    # filter_online = [{'Key': 'PingStatus', 'Values': ['Online', ]}, ]
    # filter_crwd_managed = [{'Key': 'tag-key', 'Values': ['CRWD_MANAGED']}, ]
    # response = client.describe_instance_information(Filters=filter_crwd_managed)
    # if response.get('InstanceInformationList'):
    #     for instance in response['InstanceInformationList']:
    #         managed_instance_dict.update({instance['InstanceId']: instance['ComputerName']})
    # return managed_instance_dict

    # Return list of dicts
    managed_instance_list = []
    filter_online = [{'Key': 'PingStatus', 'Values': ['Online', ]}, ]
    filter_crwd_managed = [{'Key': 'tag-key', 'Values': ['CRWD_MANAGED']}, ]
    response = client.describe_instance_information(Filters=filter_online)
    if response.get('InstanceInformationList'):
        for instance in response['InstanceInformationList']:
            managed_instance_list.append({instance['InstanceId']: instance['ComputerName']})
    return managed_instance_list


def get_instance_info(instance_id):
    ec2_client = boto3.client('ec2', region_name=region)
    instance_info = ec2_client.describe_instances(InstanceIds=[instance_id])
    return instance_info






if __name__ == '__main__':
    get_ssm_info('926bef0c-3487-4567-9d7a-15ba5ebd7de2')
    # run_install_package('FalconSensor', 'Uninstall', ['i-08941f506bbeb7b3b'], 'AWS-ConfigureAWSPackage', )
    instance_dict = get_managed_instances()
    print(instance_dict)

