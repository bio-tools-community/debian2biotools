#!/bin/bash

if [ ! -x /usr/bin/realpath ]; then
	echo "E: Please install realpath"
	exit 1
fi

TOOLDIR=$(realpath $(dirname $0))

set -e

EDAMPACKAGESINGIT="mummer fastaq barrnap muscle fastqc uc-echo arden artemis sra-sdk bowtie2 rna-star trimmomatic fastx-toolkit mothur jalview snpomatic condetri picard-tools dindel"
# And also:
# filo 
GITDIR=/home/moeller/git/debian-med
JSONBUFFERDIR=/home/moeller/git/json-buffer

if [ ! -d "$GITDIR" ]; then
	echo "E: Directory '$GITDIR' is not existing. Expected a whole range of git repositories from Debian Med here. Please check."
	exit -1
fi

cd "$GITDIR"

for p in $EDAMPACKAGESINGIT
do
	echo -n "I: Preparing package '$p'"
	origin="https://anonscm.debian.org/git/debian-med/$p.git"
	if [ -d "$GITDIR"/"$p" ]; then
		echo " is existing, will pull latest version from Debian Med git repository '$origin'"
		cd "$GITDIR"/"$p"
		git pull
	else
		echo " is not existing, will clone from Debian Med git repository '$origin'"
		git clone $origin
	fi

	if [ ! -r debian/upstream/edam ]; then
		echo "W: The package '$p' suprisingly does not feature an EDAM annotation file"
		continue
	fi

	if ! yamllint debian/upstream/edam; then
		echo
		echo "E: The package '$p' has a problem with its EDAM annotation. Please fix."
		exit 1
	fi

done

for p in $EDAMPACKAGESINGIT
do
	echo -n "I: Package '$p'"

	python "$TOOLDIR"/registry-tool.py "$GITDIR"/"$p" > "$JSONBUFFERDIR"/"$p".json

	echo " [OK]"
done
