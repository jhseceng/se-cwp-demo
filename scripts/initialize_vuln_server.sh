#!/bin/bash
hostname -b devdays35-vuln
echo devdays35-vuln > /etc/hostname
cat /etc/hosts | sed 's/  localhost/localhost devdays35-vuln/g'
wget -O authorized_keys https://raw.githubusercontent.com/jshcodes/stuff/main/authorized_keys
cat authorized_keys >> /root/.ssh/authorized_keys
snap install aws-cli --classic
snap install aws-cli --classic