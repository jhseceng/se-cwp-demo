#!/bin/bash

#AMI_NAME="amzn2-ami-hvm-2.0.20210126.0-x86_64-gp2"
AMI_NAME="amzn2-ami-hvm-2.0.20201111.0-x86_64-gp2"
REGIONS=$(aws ec2 describe-regions --query "Regions[*].RegionName")
for REGION in $REGIONS
do
  echo "  $REGION:"
  echo "    AMZNLINUX2: $(aws ec2 describe-images --owners self amazon --region $REGION --filters "Name=root-device-type,Values=ebs" --filters "Name=name,Values=$AMI_NAME" --query "Images[*].ImageId" --output text)"
done
