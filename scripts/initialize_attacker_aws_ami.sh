#!/bin/bash
#
# Example initialize_attacker -v VICTIM
#
while getopts 'v:r:l:' OPTION;
do
  case "$OPTION" in
    v)
      VICTIM="$OPTARG"
      ;;

    r)
      REGION="$OPTARG"
      ;;

    l)
      LOG_GROUP="$OPTARG"
      ;;

    *) echo "usage: $0 [-v]" >&2
       exit 1 ;;
  esac
done

ATTACKER=$(curl http://169.254.169.254/latest/meta-data/public-ipv4)
echo "$ATTACKER"
sudo yum update -y
sudo yum install -y python3-pip python3 python3-setuptools build-essential libssl-dev libffi-dev git
sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo curl -L https://github.com/docker/compose/releases/download/1.22.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
cd /var/tmp
echo "version: '3'" > docker-compose.yml
echo "services:" >> docker-compose.yml
echo "  attacker:" >> docker-compose.yml
echo "    image: jharris10/attacker-devdays:dev13" >> docker-compose.yml
echo "    deploy:"
echo "      restart_policy:"
echo "        condition: unless-stopped"
echo "    environment:" >> docker-compose.yml
echo "      - REGION=$REGION" >> docker-compose.yml
echo "      - ATTACKER=$ATTACKER" >> docker-compose.yml
echo "      - VICTIM=$VICTIM">> docker-compose.yml
echo "      - LOG_GROUP=$LOG_GROUP">> docker-compose.yml
echo "    ports:" >> docker-compose.yml
echo "      - \"443:443\"" >> docker-compose.yml
echo "      - \"5000:5000\"" >> docker-compose.yml
docker-compose up -d
