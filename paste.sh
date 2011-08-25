#!/bin/sh
URL=http://paste.awesom.eu
DEFAULTUSER=
PREFEREDLANG=
#PRINT & COPY are some kind of booleans, if they are empty they stand for False, otherwise, they stand for True
PRINT=a
COPY=

if test -n "$1" ; then
    FILE=$1
else
    echo "Usage: $0 file [lang] [user]"
    exit
fi

if test -n "$2" ; then
    LANG=$2
else
    EXT=`echo "$1"|sed -e 's/.*\.//'`
    LANG=
fi

if test -n "$3" ; then
	USER=$3
else
	USER=$DEFAULTUSER
fi

PASTE=$(curl -d "hl=${LANG}&ext=${EXT}&user=${USER}&escape=on&script" --data-urlencode paste@${FILE} $URL 2>/dev/null)

FINAL="$URL/$PASTE"
if test -n "$PRINT" ; then 
	echo "$FINAL"
fi

if test -n "$COPY" ; then
	echo $FINAL|xclip -i
fi
