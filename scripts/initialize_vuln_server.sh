#!/bin/bash
hostname -b devdays35-vuln
echo devdays35-vuln > /etc/hostname
cat /etc/hosts | sed 's/  localhost/localhost devdays35-vuln/g'
wget -O authorized_keys https://raw.githubusercontent.com/jshcodes/stuff/main/authorized_keys
mkdir /secret
wget -O /secret/devops-server-flag.txt https://raw.githubusercontent.com/jshcodes/stuff/main/vuln-flag.txt
cat authorized_keys >> /root/.ssh/authorized_keys
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm awscliv2.zip