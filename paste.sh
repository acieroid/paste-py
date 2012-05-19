#!/bin/sh
URL="http://paste.awesom.eu"
DEFAULTUSER=""
# Print the paste url ?
PRINT="YES"
# Copy the paste url ?
COPY=""
COPY_CMD=""

which xclip > /dev/null
if [ $? -eq 0 ] ; then
    COPY_CMD="`which xclip` -i"
else
    which xsel > /dev/null
    if [ $? -eq 0 ] ; then
        COPY_CMD="`which xsel`"
    fi
fi

if [ -e "$1" -o "$1" = "-" ] ; then
    FILE="$1"
else
    echo "Usage: $0 [file|-] [lang] [user]"
    exit
fi

if [ -n "$2" ] ; then
    LANG="$2"
else
    EXT="`echo \"$1\"|sed -e 's/.*\.//'`"
    LANG=""
fi

if [ -n "$3" ] ; then
    USER="$3"
else
    USER="$DEFAULTUSER"
fi

PASTE=$(curl -d "hl=${LANG}&ext=${EXT}&user=${USER}&escape=on&script" --data-urlencode paste@${FILE} "$URL" 2>/dev/null)

FINAL="$URL/$PASTE"
if [ "$PRINT" = "YES" ] ; then
    echo "$FINAL"
fi

if [ "$COPY" = "YES" -a -n "$COPY_CMD" ] ; then
    echo "$FINAL" | $COPY_CMD
fi
