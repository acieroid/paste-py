URL=http://localhost:8081

if [[ -n $1 ]]; then
    FILE=$1
else
    echo "Usage: $0 file [lang]"
    exit
fi

if [[ -n $2 ]]; then
    LANG=$2
else
    LANG=
fi

PASTE=$(curl -d "hl=${LANG}&escape=on&script" --data-urlencode paste@${FILE} $URL 2>/dev/null)

echo "Link: $URL/$PASTE"