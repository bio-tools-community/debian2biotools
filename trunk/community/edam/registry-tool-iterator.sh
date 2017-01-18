#!/bin/bash

if [ ! -x /usr/bin/realpath ]; then
	echo "E: Please install realpath"
	exit 1
fi

if [ ! -x /usr/bin/yamllint ]; then
	echo "E: Please install yamllint"
	exit 1
fi

DONTUPDATE=true
#DONTUPDATE=false

DONTOVERWRITE=true

# Set to true if no new repositories shall be downloaded
DONTCLONE=true
#DONTCLONE=false

TOOLDIR=$(realpath $(dirname $0))

set -e

#EDAMPACKAGESINGIT="mummer fastaq barrnap muscle fastqc uc-echo arden artemis sra-sdk bowtie2 rna-star trimmomatic fastx-toolkit mothur jalview snpomatic condetri picard-tools dindel"

# And also:
# filo 
GITDIR=$HOME/git/debian-med

JSONBUFFERDIR=$HOME/git/json-buffer
JSONBUFFERSUBDIR=records

if [ ! -r EDAM.owl ]; then
	echo "I: Retrieving current version of EDAM ontology"
	wget http://www.edamontology.org/EDAM.owl
fi
edamversion=$(grep doap:Version EDAM.owl | cut -f2 -d\> | cut -f1 -d\<)
echo "I: Comparing terms against EDAM version '$edamversion'"


if [ ! -d "$GITDIR" ]; then
	echo "E: Directory '$GITDIR' is not existing. Expected a whole range of git repositories from Debian Med here. Please check."
	exit -1
fi

if [ ! -d "$JSONBUFFERDIR" ]; then
	echo "E: The directory destined to hold the generated records is not existing."
	echo "   Please consider running "
        echo "      git clone https://github.com/bio-tools-community/json-buffer '$JSONBUFFERDIR'" 
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


echo
echo "I: *** Retrieving package source tree from Debian Med git repository ***"
echo

#for p in $EDAMPACKAGESINGIT
cat "$TOOLDIR/packages.list.txt" | while read p
do
	cd "$GITDIR"  # We may have moved into a subdir
	echo -n "I: Preparing package '$p'"
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
				echo "W: Could not pull latest revision for '$p' from $origin - skipped, git status shown below"
				git status
				continue
			fi
			if ! git gc; then
				echo
				echo "E: Could not garbage-collect package '$p' - fix this"
				exit 1
			fi
		fi
	else
		echo -n " is not existing "
		if $DONTCLONE; then
			echo " [skipped]"
			continue
		else
			echo -n ", will clone from Debian Med git repository '$origin'"
			if ! git clone --quiet --branch=master --single-branch $origin; then
				echo
				echo "E: Could not clone package '$p' from $origin - skipped"
				continue
			fi
			cd $p
			if ! git gc; then
				echo
				echo "E: Could not garbage-collect freshly cloned package '$p' - fix this"
				exit 1
			fi
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
		echo "E: The package '$p' has a syntactic problem with its EDAM annotation. Please fix."
		exit 1
	fi
done

echo
echo "I: *** Repository of Debian Med packages is in shape, now transcribing for bio.tools  ***"
echo


#for p in $EDAMPACKAGESINGIT
cat "$TOOLDIR/packages.list.txt" | grep -v ^# | while read p
do

	dest="$JSONBUFFERDIR"/"$JSONBUFFERSUBDIR"/"$p".json

	if $DONTOVERWRITE && [ -r "$dest" ] ; then
		echo " not overwriting exiting '$dest'"
		continue
	fi

	echo -n "I: Package '$p'"
	if [ ! -d "$GITDIR"/"$p" ]; then
		echo " not existing in '$GITDIR/$p' - skipped"
		continue
	fi
	if [ ! -r "$GITDIR"/"$p"/debian/control ]; then
		echo " with incomplete local repository, searched for $GITDIR/$p/debian/control  - skipped"
		continue
	fi

	echo -n " writing to $dest"
	cd "$GITDIR"/"$p"
	#git checkout master
	python "$TOOLDIR"/registry-tool.py "$GITDIR"/"$p" > $dest
	echo " [OK]"
	unset dest
done
