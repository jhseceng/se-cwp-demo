#!/bin/bash
echo 'Starting'
while getopts 't:' OPTION;
do
  case "$OPTION" in
    t)
      VICTIM="$OPTARG"
      ;;

    *) echo "usage: $0 [-t]" >&2
       exit 1 ;;
  esac
done


REGION=`curl http://169.254.169.254/latest/dynamic/instance-identity/document|grep region|awk -F\" '{print $4}'`
echo $REGION
echo 'Configuring region'
aws configure set region $REGION

#installing from current directory 
sudo yum update -y
sudo yum install -y python3-pip python3 python3-setuptools build-essential libssl-dev libffi-dev git
sudo amazon-linux-extras install docker

sudo service docker start
sudo usermod -a -G docker ec2-user
sudo curl -L https://github.com/docker/compose/releases/download/1.22.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
echo "version: '3'" > docker-compose.yml
echo "services:" >> docker-compose.yml
echo "  jenkins:" >> docker-compose.yml
#echo "    image: franklinjff/jenkins:version1" >> docker-compose.yml
echo "    image: jharris10/jenkins:13" >> docker-compose.yml
echo "    environment:" >> docker-compose.yml
echo "      - VICTIM=$VICTIM" >> docker-compose.yml
echo "      - JAVA_OPTS=-Djava.awt.headless=true\ -Djenkins.install.runSetupWizard=false" >> docker-compose.yml
echo "    ports:" >> docker-compose.yml
echo "      - \"50000:50000\"" >> docker-compose.yml
echo "      - \"8080:8080\"" >> docker-compose.yml
sudo docker-compose up -d