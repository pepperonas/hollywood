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
# what the launcher adds to a real show: the widget's name on every pane and the toolbar
for line in $(tmux list-panes -t $S -F '#{pane_id}=#{pane_start_command}' | sed 's/"//g'); do
	tmux set-option -p -t "${line%%=*}" @widget "${line##*/}"
done
tmux set-option -w -t $S pane-border-status top
b="#[fg=colour252,bg=colour238]"
e="#[default]#[norange] "
tmux set-option -t $S status-format[0] "#[fg=colour114,bold] hollywood #[default] #[range=user|swap]$b s swap $e#[range=user|keep]$b k keep $e#[range=user|close]$b x close $e#[range=user|menu]$b a open $e#[range=user|zoom]$b z zoom $e#[range=user|pause]$b p pause $e#[range=user|deal]$b n deal $e#[range=user|less]$b - ${e}9 panes #[range=user|more]$b + $e#[range=user|help]$b ? $e#[range=user|quit]$b q quit $e#[align=right]#[fg=colour244]next swap in 7 s "
sleep 14
shot stage

# Single widgets, large
# Wait until the pane really shows something: a picture of an empty pane is
# worse than none (the sound wave has dark stretches, cmatrix starts empty).
filled() { [ "$(tmux capture-pane -p -t $S | grep -c '[^[:space:]]')" -ge "$1" ]; }
one() {
	fresh "$2" "$3" "$W/$1"
	sleep "${4:-7}"
	tries=0
	until filled $(($3 / 2)); do
		tries=$((tries + 1))
		[ "$tries" -le 40 ] || { echo "screenshots: $1 stays empty" >&2; exit 1; }
		sleep 1
	done
	shot "$1"
}
one map 120 36 5
one cmatrix 120 36 9
one hexdump 120 36 6
one code 120 36 8
# the key art alone: a pane this low shows the last lines only, not the temp path above them
one sshart 44 12 5
one apg 120 30 8

tmux kill-session -t $S 2>/dev/null || true
