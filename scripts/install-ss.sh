#!/bin/bash

git clone https://github.com/offensive-security/exploitdb.git /opt/exploit-database
ln -sf /opt/exploit-database/searchsploit /usr/local/bin/searchsploit
chown ec2-user:ec2-user /home/ec2-user/.searchsploit_rc