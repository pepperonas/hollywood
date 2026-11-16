# hollywood: platform compatibility, sourced by every widget.
#
# Linux keeps its original behaviour.  On macOS the Linux-only paths
# (/sys, /proc) are replaced and stand-ins for tools that Homebrew does
# not ship (ccze, apg, atop, speedometer, batcat) are appended to PATH.
# They are appended, not prepended: a real installation always wins.

HW_SHARE="$(cd "$(dirname "$0")/../../share/hollywood" 2>/dev/null && pwd)"
HW_OS="$(uname -s)"

HW_CODE_DIRS="/usr"
HW_IMG_DIRS="/usr"
HW_NODE_DIRS="/sys /dev"
HW_STAT="stat"
HW_READABLE="-readable"

case "$HW_OS" in
	Darwin)
		PATH="$PATH:$HW_SHARE/shims"
		export PATH
		HW_CODE_DIRS="/usr /Library/Developer/CommandLineTools/usr /Library/Developer/CommandLineTools/Library"
		HW_IMG_DIRS="/usr/share /System/Library/CoreServices /System/Library/QuickLook /Library/Frameworks"
		HW_NODE_DIRS="/dev /System/Library/Extensions /private/etc"
		HW_STAT="stat -x"
		HW_READABLE="-perm -444"
	;;
esac

# Name of the interface carrying the default route
hw_default_iface() {
	case "$HW_OS" in
		Darwin)
			route -n get default 2>/dev/null | awk '/interface:/ {print $2; exit}'
		;;
		*)
			while read Iface Destination Gateway Flags RefCnt Use Metric Mask MTU Window IRTT; do
				[ "$Mask" = "00000000" ] && break
			done < /proc/net/route
			echo "$Iface"
		;;
	esac
}

# Ctrl-C in any pane ends the show: close the window all widgets live in.
# (Upstream ran "pkill -9 -f lib/hollywood/", which also hits every other
# process that merely has that path on its command line, an editor for one.)
hw_quit() {
	[ -n "$TMUX_PANE" ] && tmux kill-window -t "$TMUX_PANE" >/dev/null 2>&1
	exit 0
}
