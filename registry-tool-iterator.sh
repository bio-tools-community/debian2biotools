#!/bin/bash

if [ ! -x /usr/bin/realpath ]; then
	echo "E: Please install realpath"
	exit 1
fi

DONTUPDATE=true
DONTOVERWRITE=true
DONTCLONE=true

TOOLDIR=$(realpath $(dirname $0))

set -e

#EDAMPACKAGESINGIT="mummer fastaq barrnap muscle fastqc uc-echo arden artemis sra-sdk bowtie2 rna-star trimmomatic fastx-toolkit mothur jalview snpomatic condetri picard-tools dindel"

# And also:
# filo 
GITDIR=/home/moeller/git/debian-med

JSONBUFFERDIR=/home/moeller/git/json-buffer
JSONBUFFERSUBDIR=records

if [ ! -d "$GITDIR" ]; then
	echo "E: Directory '$GITDIR' is not existing. Expected a whole range of git repositories from Debian Med here. Please check."
	exit -1
fi

if [ ! -d "$JSONBUFFERDIR" ]; then
	echo "E: The diretory destined to hold the generated records is not existing. $JSONBUFFERDIR'" 
	exit -1
fi

dest="$JSONBUFFERDIR"/"$JSONBUFFERSUBDIR" 
if [ ! -d "$JSONBUFFERDIR"/"$JSONBUFFERSUBDIR" ]; then
	echo "W: Creating directory '$dest'"
	mkdir "$dest"
else
	echo "I: Found destination directory '$dest'"
fi
unset dest

if [ ! -r "$TOOLDIR/packages.list.txt" ]; then
	echo "E: Expected list of packages to work on in '$GITDIR/packages.list.txt'. Fie not found/readable."
	exit 1
fi

if ! $DONTCLONE; then
	#for p in $EDAMPACKAGESINGIT
	cat "$TOOLDIR/packages.list.txt" | while read p
	do
		cd "$GITDIR"  # We may have moved into a subdir
		echo -n "I: Preparing package '$p'"

		if $DONTOVERWRITE && [ -r "$JSONBUFFERDIR"/"$JSONBUFFERSUBDIR"/"$p".json ] ; then
			echo " not overwriting exiting '$JSONBUFFERDIR/$JSONBUFFERSUBDIR/$p.json'"
			continue
		fi

		origin="https://anonscm.debian.org/git/debian-med/$p.git"
		#origin="ssh://anonscm.debian.org/git/debian-med/$p.git"
		if [ -d "$GITDIR"/"$p" ]; then
			if $DONTUPDATE; then
				echo " is existing, will not check for any later version"
			else
				echo " is existing, will pull latest version from Debian Med git repository '$origin'"
				cd "$GITDIR"/"$p"
				if ! git pull; then
					echo
					echo "E: Could not pull latest revision for '$p' from $origin - skipped"
					continue
				fi
			fi
		else
			echo " is not existing, will clone from Debian Med git repository '$origin'"
			if ! git clone --quiet --branch=master --single-branch $origin; then
				echo
				echo "E: Could not clone package '$p' from $origin - skipped"
				continue
			fi
		fi

		cd "$GITDIR"/"$p"
		git checkout master

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
fi


#for p in $EDAMPACKAGESINGIT
cat "$TOOLDIR/packages.list.txt" | grep -v ^# | while read p
do
	echo -n "I: Package '$p'"
	if [ ! -d "$GITDIR"/"$p" ]; then
		echo " not existing in '$GITDIR/$p' - skipped"
		continue
	fi
	if [ ! -r "$GITDIR"/"$p"/debian/control ]; then
		echo " with incomplete local repository, searched for $GITDIR/$p/debian/control  - skipped"
		continue
	fi

	dest="$JSONBUFFERDIR"/"$JSONBUFFERSUBDIR"/"$p".json
	echo -n " creating $dest"
	cd "$GITDIR"/"$p"
	#git checkout master
	python "$TOOLDIR"/registry-tool.py "$GITDIR"/"$p" > $dest
	echo " [OK]"
	unset dest
done
