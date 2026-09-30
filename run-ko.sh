#!/bin/sh
# Run from the homework directory so relative example files work.
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$#" -eq 0 ]; then
    printf '%s\n' '사용법: ./run-ko.sh cpu-sched/scheduler.py -l 5,3,1 -c'
    exit 0
fi
case "$1" in
    /*) homework=$1 ;;
    *) homework=$base/$1 ;;
esac
if [ ! -f "$homework" ]; then
    printf '숙제 파일을 찾을 수 없습니다: %s\n' "$1" >&2
    exit 1
fi
shift
cd -- "$(dirname -- "$homework")"
exec python3 -X utf8 "$(basename -- "$homework")" "$@"
