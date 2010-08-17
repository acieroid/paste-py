#!/bin/sh
URL=http://paste.awesom.eu

if test -n "$1" ; then
    FILE=$1
else
    echo "Usage: $0 file [lang]"
    exit
fi

if test -n "$2" ; then
    LANG=$2
else
    LANG=
fi

PASTE=$(curl -d "hl=${LANG}&escape=on&script" --data-urlencode paste@${FILE} $URL 2>/dev/null)

echo "$URL/$PASTE"
