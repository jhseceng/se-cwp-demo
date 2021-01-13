#!/bin/bash
docker exec -it $(docker container ls | grep 'attacker' | awk '{print $1}') /bin/bash