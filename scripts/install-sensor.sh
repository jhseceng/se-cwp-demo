#!/bin/bash
if [ -z $1 ]
then
  echo "Usage: install-sensor {InstanceId}"
else
  aws ssm send-command --document-name AWS-ConfigureAWSPackage --instance-ids $1 --parameters '{"action":["Install"],"installationType":["Uninstall and reinstall"],"name":["FalconSensor"]}' --region $REGION
fi
