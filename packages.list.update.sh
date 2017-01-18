#!/bin/bash
set -e
dest="$(dirname $0)/packages.list.txt"

echo "Writing packages list to '$dest'"
(
wget -O - https://anonscm.debian.org/cgit/blends/projects/med.git/plain/tasks/bio | grep Depends | cut -f2 -d: | tr ", " "\n" | tr -d "|" | sort -u | while
   read packagename
do
	a=$(apt-cache show $packagename | head -n 2)
	p=""
	q=""
	if echo $a|grep -q "Source: "; then
		q=$(echo $a | sed -e '/^.*Source:/s/^.*Source: *//' -e 's/ *Version:.*//' -e 's/ *(.*) *//')
		echo $q
	else
		p=$(echo $a | sed -e '/Package/s/^Package: *//' -e 's/ *Version:.*//')
		echo $p
	fi
	# for debugging
	#echo "p='$p'"
	#echo "q='$q'"
	#echo 
done
) | grep -v "^E:" | sort -u | egrep -v "^ *$"> $dest
