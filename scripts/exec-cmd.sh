#!/bin/bash
#Quick and dirty remote command execution via SSM
#REQUIRES: jq

usage(){
  echo "Usage: exec-cmd -i [InstanceId {string}] -c [Command {string}] -w (Command Wait {number})"
}

while getopts ':i: :c: :w: :h' OPTION;
do
  case "$OPTION" in
    i ) INSTANCE="$OPTARG"
       ;;
    c ) CMD="$OPTARG"
       ;;
    w ) WAIT="$OPTARG"
       ;;
    h ) usage
	exit 0
       ;;
    ? ) echo "Stop mumbling!"
         usage
         exit 0
       ;;
  esac
done
shift $((OPTIND -1))

if [ -z "$INSTANCE" ]
then
   usage
else
   if [ -z "$CMD" ]
   then
      usage
   else
      if [ -z "$WAIT" ]
      then
	WAIT=1
      fi
      echo "Executing command..."
      result=$(aws ssm send-command --instance-ids $INSTANCE\
       	--document-name "AWS-RunShellScript"\
       	--parameters "commands=$CMD")
      cmdId=$(echo $result | jq -r .Command.CommandId)
      echo "Awaiting response..."
      sleep $WAIT
      aws ssm list-command-invocations --command-id $cmdId\
       	--query "CommandInvocations[*].CommandPlugins[*].Output[]"\
        --details --output text
   fi
fi
