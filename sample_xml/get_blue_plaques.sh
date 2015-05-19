#!/bin/sh

# Locations of Blue Plaques, from http://openplaques.org/

# Data Licence:
# You are more than welcome to re-use the data in any way you see fit. The data
# is released under the Public Domain Dedication and License 1.0 and we make no
# claims of copyright over either the data we've collected ourselves, nor the
# hundreds of hours of collective value that have been added by our co-curators.
# That said, we can accept no liability for any issues that may arise over the
# re-use of this data, and you are advised to make your own assessment. If you
# do re-use the data we'd love it if you could acknowledge Open Plaques and link
# back to us - however you are under no obligation to do so.

# Type: XML 1.0
# Encoding: UTF-8
# Size: 19M

set -e

FILENAME=gb_20140923.xml
URL=https://dl.dropboxusercontent.com/u/21695507/openplaques/gb_20140923.xml

if [ -r ${FILENAME} ]
then
	echo "File ${FILENAME} exists. Skipping..." >&2
else
	curl --output ${FILENAME} ${URL}
fi
