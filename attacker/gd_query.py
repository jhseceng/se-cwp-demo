import nmap
from flask import make_response ,jsonify
import boto3
import requests
events_of_interest = ['Recon:EC2/PortProbeUnprotectedPort','Recon:EC2/Portscan','CryptoCurrency:EC2/BitcoinTool.B!DNS']
# @app.route("/gdquery", methods=['GET'])
region = 'eu-west-1'


def query_gd():

    client = boto3.client('guardduty', region_name=region)
    detector_id = get_detector()
    fc = {'Criterion': {'type': {'Eq': events_of_interest}}}
    gd_findings = get_findings(fc)

    _get_finding_by_id = lambda detector_id, finding_id: client.get_findings(
        DetectorId=detector_id,
        FindingIds=[
            finding_id,
        ]
    )
    findings_buffer = []

    for _finding_id in gd_findings['FindingIds']:
        _finding = (_get_finding_by_id(detector_id, _finding_id))
        # if _finding['Findings'][0]['Type'] in events_of_interest:
        findings_buffer.append(_finding['Findings'][0])
    # res = make_response(jsonify(
    #     findings_buffer), 200)
    # res.headers['Content-type'] = 'application/json'
    # return res
    print(findings_buffer[0])
    return findings_buffer



def nmap_host(target_ip):

     # target_ip = request.form.get('target')
     nm = nmap.PortScanner()
     scan_res = nm.scan('target_ip', '80')
     res = make_response(jsonify(
         scan_res), 200)
     res.headers['Content-type'] = 'application/json'
     return res

def get_detector():
    client = boto3.client('guardduty', region_name=region)
    detectors_list = client.list_detectors()

    if not detectors_list["DetectorIds"]:
        print("GuardDuty is not enabled ... enable GuardDuty on master account")
        return
    else:
        detector_id = detectors_list['DetectorIds'][0]
        response = client.list_findings(
            DetectorId=detector_id,
            FindingCriteria=fc,
            MaxResults=10
        )
    return detector_id

def get_findings(fc):
    client = boto3.client('guardduty', region_name=region)
    try:
        detector_id = get_detector()
        response = client.list_findings(
            DetectorId=detector_id,
            FindingCriteria=fc,
            MaxResults=10
        )
        return response
    except Exception as e:
        print('Got exception getting Guardduty findings\n {}'.format(e))





if __name__ == '__main__':
    # nmap_host('127.0.0.1')
    # query_gd()
    instanceid = "i-0fc47dfb6917ddf43"
    fc = {"Criterion": {"resource.instanceDetails.instanceId": {"Eq": [instanceid]}}}
    findings = get_findings(fc)
    print(findings)
