#!/bin/bash
aws ec2 describe-instances --query "Reservations[*].Instances[*].{Name: Tags[?Key=='demo-purpose'] | [0].Value, InstanceID: InstanceId}" --region $REGION --output table