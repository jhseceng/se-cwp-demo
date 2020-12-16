import json
import os

import boto3
import requests

region = os.environ['region']






def query_falcon_host(_auth_header, _host_filter):

    _url = "https://api.crowdstrike.com/devices/queries/devices/v1"
    _PARAMS = {"offset": 0,
              "limit": 10,
              "filter": _host_filter
              }
    _auth_token = get_auth_token()
    _auth_header = get_auth_header(_auth_token)
    _response = requests.request("GET", _url, headers=_auth_header, params=_PARAMS)

    _json_obj =json.loads(_response.text.encode('utf8'))
    if len(_json_obj['resources']) != 0:
        return _json_obj['resources'][0]
    else:
        return


def get_aws_instance_id_by_tag(_tagname, _tagvalue):
    ec2_client = boto3.client('ec2', region_name=region)
    _Filter = [
        {
            'Name': 'tag:' + _tagname,
            'Values': [_tagvalue]
        }
    ]
    result = ec2_client.describe_instances(Filters=_Filter)
    _instance_list = []
    if len(result['Reservations']) != 0:
        for _result in result['Reservations']:
            _instance_info = {
                "InstanceId": _result['Instances'][0]['InstanceId'],
                "tagname": _tagvalue,
                }
            _instance_list.append(_instance_info)
    return _instance_list


def show_managed_instances():
    auth_token = ''
    auth_header = ''
    tag_name = 'demo-purpose'
    tag_values = ['Jenkins', 'Attacker', 'Bastion']

    instance_list = []
    for tag_value in tag_values:
        aws_instance = get_aws_instance_id_by_tag(tag_name, tag_value)
        instance_list.extend(aws_instance)

    auth_token = get_auth_token()
    if auth_token:
        auth_header = "Bearer " + auth_token

    for instance in instance_list:
        host_query_filter = "platform_name: 'Linux' + instance_id: '" + instance['InstanceId'] + "'"

        falcon_aid = query_falcon_host(auth_header, host_query_filter)
        falcon_instance_info = get_falcon_host_info(aid)

        if falcon_aid:
            instance["falcon_aid"] = falcon_aid
            instance["agent_version"] = falcon_instance_info["agent_version"]
            instance["os_version"]=falcon_instance_info["os_version"]
            instance["policy_type"]= falcon_instance_info["policies"][0]["policy_type"]
        else:
            instance["falcon_aid"] = 'None'
    # return instance_list

def get_ssm_secure_string(parameter_name):
    ssm = boto3.client("ssm", region_name=region)
    return ssm.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )

def get_auth_header(_auth_token):
    if _auth_token:
        _auth_header = "Bearer " + _auth_token
        _headers = {
            "Authorization": _auth_header
        }
        return _headers


def get_auth_token():
    try:
        _client_id = get_ssm_secure_string('Falcon_ClientID')['Parameter']['Value']
        _client_secret = get_ssm_secure_string('Falcon_Secret')['Parameter']['Value']
    except Exception as e:
        print('Exception {}'.format(e))
    url = "https://api.crowdstrike.com/oauth2/token"

    payload = 'client_secret='+_client_secret+'&client_id='+_client_id
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.ok:
        _response_object = (response.json())
        _token = _response_object.get('access_token', '')
        if _token:
            return \
                _token
    return

def falcon_api_post(_url, _headers, _data):
    try:
        _response = requests.request("POST", _url, headers=_headers, data=_data)

        _json_obj =json.loads(_response.text.encode('utf8'))
        if len(_json_obj['resources']) != 0:
            return _json_obj['resources'][0]
        else:
            return
    except Exception as e:
        print('Exception e{} posting to api'.format(e))

def falcon_api_get(_url,_params):
    _auth_token = get_auth_token()
    _headers = get_auth_header(_auth_token)
    _response = requests.request("GET", _url, headers=_headers, params=_params)

    _json_obj =json.loads(_response.text.encode('utf8'))
    if len(_json_obj['resources']) != 0:
        return _json_obj['resources'][0]
    else:
        return

def get_falcon_aid_from_hotsname(hostname):
    host_query_filter = "hostname: '" + hostname + "'"
    auth_token = get_auth_token()
    auth_header = get_auth_header(auth_token)
    falcon_aid = query_falcon_host(auth_header, host_query_filter)
    return falcon_aid


def query_falcon_host(auth_header, host_filter):

    url = "https://api.crowdstrike.com/devices/queries/devices/v1"
    PARAMS = {"offset": 0,
              "limit": 10,
              "filter": host_filter
              }
    auth_token = get_auth_token()
    auth_header = get_auth_header(auth_token)
    response = requests.request("GET", url, headers=auth_header, params=PARAMS)

    json_obj =json.loads(response.text.encode('utf8'))
    if len(json_obj['resources']) != 0:
        return json_obj['resources'][0]
    else:
        return

def get_falcon_host_info(aid):
    url = "https://api.crowdstrike.com/devices/entities/devices/v1"
    params = {"ids": aid}

    auth_token = get_auth_token()
    headers = get_auth_header(auth_token)
    info = falcon_api_get(url, params)
    return(info)


def get_falcon_aid_from_instanceid(instanceid):
    host_query_filter = "instance_id: '" + instanceid + "'"
    auth_token = get_auth_token()
    auth_header = get_auth_header(auth_token)
    falcon_aid = query_falcon_host(auth_header, host_query_filter)
    return falcon_aid



def manage_falcon_host(_aid, action):
    """

    :param _aid: aid of host in falcon console.
    :param action: allowed values unhide_host / hide_host
    :return:
    """
    url = "https://api.crowdstrike.com/devices/entities/devices-actions/v2?action_name="+action
    payload = json.dumps({"ids": [_aid]})
    _auth_token = get_auth_token()
    _auth_header = get_auth_header(_auth_token)
    headers = {

        'Content-Type': 'application/json',
    }
    headers.update(_auth_header)
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 202:
            return True
        else:
            return
    except Exception as e:
        # logger.info('Got exception {} hiding host'.format(e))
        print('Got exception {} hiding host'.format(e))
        return

def get_stream():
    url = 'https://api.crowdstrike.com:443/sensors/entities/datafeed/v2'
    falcon_api_get(url,'appId=my_app_id')

if __name__ == '__main__':
    instanceid = "i-06ffdb839a2a6820a"
    hostname = 'ip-172-16-64-29.us-west-1.compute.internal'
    # aid = "7fa6a2b861524219a94bf2f9816b2452"
    # instances = show_managed_instances()
    # print("Instances {}".format(instances))
    aid = get_falcon_aid_from_hotsname(hostname)
    # aid = get_falcon_aid_from_instanceid(instanceid)
    # action = "unhide_host"
    get_stream()
    auth_token = get_auth_token()
    auth_header = get_auth_header(auth_token)
    # manage_falcon_host(aid, action)
    # manage_falcon_host(aid, action, auth_header)
    # print("aid is {}".format(aid))
    falcon_instance_info = get_falcon_host_info(aid)
    print (falcon_instance_info)

