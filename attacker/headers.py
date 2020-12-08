import boto3
import json
import sys
import argparse
import requests
import time
from datetime import datetime, timedelta

region ='eu-west-1'

EVENTS_OF_INTEREST = ['CryptoCurrency:EC2/BitcoinTool.B!DNS']
def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--output_file_name', default='findings_output.txt', required=False)
    args = parser.parse_args(arguments)



    client = boto3.client('guardduty')

    #Find out if GuardDuty already enabled:
    detectors_list = client.list_detectors()

    if not detectors_list["DetectorIds"]:
        print ("GuardDuty is not enabled ... enabling GuardDuty on master account")
        response = client.create_detector(Enable=True);
        # Save DetectorID handler
        DetectorId = response["DetectorId"]
    else:
        print("GuardDuty already enabled on account")
        DetectorId = detectors_list['DetectorIds'][0]

    # print all Detectorts
    print("Detector lists: ")
    for x in detectors_list["DetectorIds"]:
        print(x, end=" ")


    gd_findings = client.list_findings(
        DetectorId=DetectorId
    )

    # print all findings
    _print_finding = lambda DetectorId, FindingId: client.get_findings(
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
        if _find['Findings'][0]['Type'] in EVENTS_OF_INTEREST:
            findings_buffer.append(_find['Findings'][0])

    # print results to a text file
    with open(args.output_file_name, 'w') as outfile:
        json.dump(findings_buffer, outfile)

    # print to terminal (comment out this line if the list is too long, use text file instead)
    print(json.dumps(findings_buffer))

    # print the count of findings for the given severity.
    findings_stat = client.get_findings_statistics(
        DetectorId=DetectorId,
        FindingStatisticTypes=[
            'COUNT_BY_SEVERITY',
        ]
    )

    print('\n\nFindings Statistics: ' + json.dumps(findings_stat['FindingStatistics']))


def check_for_running_queries(log_group_name):
    client = boto3.client('logs', region_name=region, verify=None)
    res = client.describe_queries(
        logGroupName=log_group_name,
        status='Running')
    if not res["queries"]:
        return False
    else:
        return True

def query_vpc_logs(time_interval, time_value, log_group_name, query_string):
    """
    :param time_interval:
    :param time_value:
    :param log_group_name:
    :param query_string:
    :return:

    #
    #string time_interval = hours, minutes, seconds
    #int time_value = number of intervals
    """
    _flow_logs = []
    if time_interval == "hours":
        last_time = int((datetime.today() - timedelta(hours=float(time_value))).timestamp())
    elif time_interval == "minutes":
        last_time = int((datetime.today() - timedelta(minutes=float(time_value))).timestamp())
    elif time_interval == "seconds":
        last_time = int((datetime.today() - timedelta(seconds=float(time_value))).timestamp())
    else:
        last_time = int((datetime.today() - timedelta(days=float(time_value))).timestamp())

    client = boto3.client('logs',region_name=region, verify=None)
    try:
        query = client.start_query(
            logGroupName=log_group_name,
            queryString=query_string,
            startTime=int(datetime.today().timestamp()) - last_time,
            endTime=int(datetime.now().timestamp()),
            limit=5
        )
    except Exception as e:
        print('Got Exception {}'.format(e))
    print(query['queryId'])
    while check_for_running_queries(log_group_name):
        time.sleep(2)
    _response = client.get_query_results(queryId=query['queryId'])
    for _result in _response.get("results"):
        _flow_logs.append(_result[1]["value"])
    return _flow_logs



def header_scan(host):
    headers_dict = {}
    response = requests.get(host)
    headers=response.headers
    for k, v in headers.items():
        print('{}:{}'.format(k,v))
        headers_dict[k] = v
    print(type(headers_dict))
    return


if __name__ == '__main__':
    q_string = ""
    lg_name = ""
    time_int = "hours"
    time_val = "5"
    lg_name = "ghtr-LogGroup-1UQWM0EVEZS6D"
    q_string = "filter srcAddr=\"86.144.52.130\""
    logs_of_interest = query_vpc_logs(time_int, time_val, lg_name, q_string)
    if logs_of_interest:
        for log in logs_of_interest:
            print(log)
    #sys.exit(main(sys.argv[1:]))
    # header_scan('http://v5Jenkins-ALB-1884688024.eu-west-1.elb.amazonaws.com')
