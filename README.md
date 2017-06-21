# Export of Debian annotation to the bio.tools repository

This folder collects tools to automated the transformation of Debian
package annotation in the a syntax of the ELIXIR registry 'bio.tools' [3].

The tools are tailored to packages curated by the Debian Med project.
A key technology in this process is the EDAM ontology [1], This addresses
the categorisation of tools and collections of tools that contribute to
computational biology in its broadest sense.

The bio.tools entry can retrieve some information directly from the
available annotation by e.g. using dpkg-parsechangelog.  The EDAM
annotation is however external to Debian and considered sufficiently
beneficial to the Debian packages to have these annotated along the
regular packaging. Since package annotation is immediately amendable
via the git repository of Debian Med [4], this shall also invite
Debian-external contributors.

## Tools

The following tools are available
 * packages.list.update.sh
 * registry-tool.py
 * registry-tool-iterator.sh

The packages.list.update.sh script retrieves a list of binry packages
(the ones with code executed by the user) from the Debian Med tasks pages
and determines the source packages for these (the ones with the source
code and especially also the package annotation). A list of packages is
created as the file 'packages.list.txt'.

The registry-tool.py script is not meant to be executed directly.
It translates all information gathere from a single package source tree
into a single json file. The latter is provided in a form that may be
directly uploaded to the bio.tools repository.

The registry-tool-iterator.sh reads the packages.list.txt file and checks
out the master branch of each such referenced package. The iterator
checks the format of each EDAM file and in a second iteration creates
the json files mean to export from Debian to the bio.tools repository.

## Data flow

While the upload of packages is at ease for packages that are yet unknown
to the  bio.tools registry, the information for entries already existing
demands a manual act of merging. There is yet no means in the bio.tools
repository to support that process (i.e.  provenance management).

To the rescue comes a git repository [5] to which the files created by
the registry-tool are submitted.  The information in bio.tools placed
in an independent branch. A third branch merges the two to prepare
the submission.

Steffen Möller, Matúš Kalaš, Hervé Ménager
St. Malo/Lyngby/Trondheim/Niendorf(2x)/Bucharest 2015-2017

[1] http://edamontology.org/
[2] http://www.yaml.org/
[3] https://bio.tools
[4] https://anonscm.debian.org/cgit/debian-med
[5] https://github.com/bio-tools-community/json-buffer
