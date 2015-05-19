#!/bin/sh

# XMark sample data, from http://www.xml-benchmark.org/

# Type: XML 1.0
# Encoding: UTF-8
# Size: 38M (100M decompressed)

set -e

FILENAME=xmark.xml.gz
URL=http://www.ins.cwi.nl/projects/xmark/Assets/standard.gz

if [ -r ${FILENAME} ]
then
	echo "File ${FILENAME} exists. Skipping..." >&2
else
	curl --output ${FILENAME} ${URL}
fi
