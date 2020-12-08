#!/bin/bash
# Usage initialize_webserver.sh CID falcon_packagename s3bucketname
# Example initialize_webserver -c "12345678" -f "falcon-sensor_5.30.0-9507_amd64.deb" -b "falcon_bootstrap"
while getopts 'c:f:b:' OPTION;
do
  case "$OPTION" in
    c)
      CID="$OPTARG";;
    f)
      FILENAME="$OPTARG";;
    b)
      S3BUCKET="$OPTARG";;
    *) echo "usage: $0 [-a] [-v]" >&2
       exit 1 ;;
  esac
done

apt-get update
apt install docker.io python3-pip build-essential libssl-dev libffi-dev dnsutils -y --force-yes

cd /home/ubuntu || exit 1
sudo apt install python-pip -y --force-yes
sudo pip install awscli
#
# Optional install of CS agent from S3 bucket
#
#sudo aws s3 ls
#sudo aws s3 cp s3://"$S3BUCKET"/"$FILENAME" /home/ubuntu
#sudo apt-get install libnl-3-200 libnl-genl-3-200 -y
#sudo dpkg -i "$FILENAME"
#sudo /opt/CrowdStrike/falconctl -s --cid=$CID
#sudo systemctl start falcon-sensor
#
#
pip3 install docker-compose
cd /var/tmp || exit 1
echo "version: '3'" > docker-compose.yml
echo "services:" >> docker-compose.yml
echo "  jenkins:" >> docker-compose.yml
echo "    image: franklinjff/jenkins:version1" >> docker-compose.yml
echo "    environment:" >> docker-compose.yml
echo "      JAVA_OPTS: \"-Djava.awt.headless=true\"" >> docker-compose.yml
echo "      JAVA_OPTS: \"-Djenkins.install.runSetupWizard=false\"" >> docker-compose.yml
echo "    ports:" >> docker-compose.yml
echo "      - \"50000:50000\"" >> docker-compose.yml
echo "      - \"8080:8080\"" >> docker-compose.yml
docker-compose up -d
