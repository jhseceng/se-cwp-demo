#!/bin/bash
#Quick and dirty

JID=$(aws ec2 describe-instances --query "Reservations[*].Instances[*].InstanceId" --filter "Name=instance-state-name,Values=running" --filter "Name=tag:demo-purpose,Values=Jenkins" --region $REGION --output text)
echo "Jenkins server ID: $JID"
CMD="cd /var/tmp;docker-compose down;docker-compose up -d"
/usr/local/bin/exec-cmd -i $JID -c "$CMD" -w 10