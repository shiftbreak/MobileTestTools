#!/bin/bash
a=`mktemp`
b="snapshot-$(date +"%Y_%m_%d_%I_%M_%p")"
dataDir=$1
echo -e "Sandbox directory is: ${dataDir}"

ssh   -p 2222 root@localhost "rm /tmp/data.tgz; cd $dataDir/; tar -czf /tmp/data.tgz ."
scp -q  -P 2222 root@localhost:/tmp/data.tgz $a
mkdir $b
tar xzf $a -C $b/
rm $a
