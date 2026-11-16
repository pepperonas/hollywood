# Changelog

All notable changes to hollywood are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-11-16

First release of the macOS port. It is based on
[hollywood 1.27](https://github.com/dustinkirkland/hollywood) by Dustin Kirkland;
the version numbers of this project are its own.

### Added
- **Runs on macOS.** Every widget sources `share/hollywood/compat.sh`, which replaces
  what only Linux has: `/sys` and `/proc/net/route`, `find -readable`, the output of
  `stat`, and the default network interface. On Linux the widgets use the same paths
  and options as upstream.
- **Stand-ins for tools Homebrew does not ship**, in `share/hollywood/shims/`:
  `ccze` (colours log-like text), `apg` (a pronounceable password with its spelling),
  `speedometer` (network throughput from the interface counters), `atop` (hands over
  to `top`) and `batcat` (hands over to `bat`). They are appended to `PATH`, so a
  real installation always wins.
- `hollywood --version`.
- Homebrew formula (`brew install pepperonas/tap/hollywood`), `install.sh`, a release
  archive with checksums, and a test suite that runs on macOS and Linux.

### Changed
- **Ctrl-C ends the show cleanly.** Upstream ran `pkill -9 -f lib/hollywood/`, which
  also killed every other process that merely had that path on its command line - an
  editor with a widget open, for one. Widgets now close the tmux window they live in.
- The launcher tracks the widget window by its tmux id. After the window was gone,
  upstream addressed the session by name, hit the shell it was started from and
  filled that with widgets again.
- The tmux session is closed on exit only if hollywood created it; started inside an
  existing session, it leaves that session alone.
- An unknown option is a usage error (exit 2) instead of opening the man page.
- The picture widget handles paths with spaces; the man-page widget knows
  uncompressed page names (`ls.1`, `perl.1m`).

### Removed
- `wallstreet` - it is its own project now:
  [pepperonas/wallstreet](https://github.com/pepperonas/wallstreet).
- The Debian and snap packaging. For Debian and Ubuntu, use upstream's package.
