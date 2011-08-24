#!/bin/sh
URL=http://paste.awesom.eu
DEFAULTUSER=Babass
PREFEREDLANG=default

if test -n "$1" ; then
    FILE=$1
else
    echo "Usage: $0 file [lang] [user]"
    exit
fi

if test -n "$2" ; then
    LANG=$2
else
    case `echo $1| awk -F . '{ print ($(NF))}'` in
	    hs)		LANG=haskell;;
    	    py)		LANG=python;;
	    *)		LANG=$PREFEREDLANG;;
    esac
fi

if test -n "$3" ; then
	USER=$3
else
	USER=$DEFAULTUSER
fi

PASTE=$(curl -d "hl=${LANG}&user=${USER}&escape=on&script" --data-urlencode paste@${FILE} $URL 2>/dev/null)

echo "$URL/$PASTE"
