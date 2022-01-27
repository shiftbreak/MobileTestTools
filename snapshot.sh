#!/bin/bash
a=`mktemp`
b="snapshot-$(date +"%Y_%m_%d_%I_%M_%p")"
e="installipa -i ${1}"
c=`ssh -i ~/.ssh/id_rsa -p 2222 root@localhost "installipa -l 2>/dev/null"`
package="NULL"
for l in `echo $c`; do
	if echo $l | grep -iqF "$1"; then
		package=$l
	fi
done
if [[ package == "NULL" ]]; then
	exit "Not found"
fi

dataDir=`ssh -i ~/.ssh/id_rsa -p 2222 root@localhost "installipa -i $package 2>/dev/null" | grep Data | sed 's/Data: //'`
echo -e "Sandbox directory is: ${dataDir}"

ssh -q -i ~/.ssh/id_rsa -p 2222 root@localhost "rm /tmp/data.tgz; cd $dataDir/; tar -czf /tmp/data.tgz ./*"
scp -q -i ~/.ssh/id_rsa -P 2222 root@localhost:/tmp/data.tgz $a
mkdir $b
tar xzf $a -C $b/
rm $a
