#!/usr/bin/env bash
# Screenshots for the README and the project page: docs/screenshots/*.png
#
#   tools/screenshots.sh
#
# "stage" is a fixed arrangement of widgets, so the picture is the same kind
# of picture every time; hollywood itself picks widgets and splits at random.
# Widgets that would show this machine's processes, logs or files (htop,
# atop, logs, tree, stat) are left out on purpose.  Needs tmux and a
# Chromium-family browser (see tools/termshot.py).
set -eu
cd "$(dirname "$0")/.."
W="$PWD/lib/hollywood"
OUT=docs/screenshots
S=hwshots
mkdir -p "$OUT"

shot() { python3 tools/termshot.py "$S" "$OUT/$1.png" >/dev/null && echo "$OUT/$1.png"; }
fresh() { tmux kill-session -t $S 2>/dev/null || true; tmux new-session -d -s $S -x "$1" -y "$2" "$3"; }

# The stage: three rows
fresh 172 50 "$W/map"
tmux split-window -v -l 26 -t $S.0 "$W/hexdump"
tmux split-window -v -l 12 -t $S.1 "$W/apg"
tmux split-window -h -l 104 -t $S.0 "$W/cmatrix"
tmux split-window -h -l 62 -t $S.1 "$W/code"
tmux split-window -h -l 88 -t $S.3 "$W/figlet"
tmux split-window -h -l 44 -t $S.4 "$W/sshart"
tmux split-window -h -l 70 -t $S.6 "$W/speedometer"
tmux split-window -h -l 34 -t $S.7 "$W/pv"
sleep 14
shot stage

# Single widgets, large
one() { fresh "$2" "$3" "$W/$1"; sleep "${4:-7}"; shot "$1"; }
one map 120 36 5
one cmatrix 120 36 9
one hexdump 120 36 6
one code 120 36 8
one sshart 60 20 5
one mplayer 120 36 8

tmux kill-session -t $S 2>/dev/null || true
