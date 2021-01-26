#!/bin/bash
echo "Welcome to the CrowdStrike attack simulation!"
docker exec -it $(docker container ls | grep 'attacker' | awk '{print $1}') /bin/sh