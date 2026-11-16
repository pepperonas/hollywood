<!--# block name="none" --><!--# endblock -->
# hollywood for macOS — Hacker Screen for Your Terminal

> hollywood is a free, open-source (Apache-2.0) program that splits a terminal into tmux panes and fills each one with busy-looking output: a world map as ASCII art, falling characters, hex dumps, scrolling source code, SSH key art, network throughput and more - twenty widgets, dealt again every few seconds. This is the macOS port of Dustin Kirkland's hollywood: it replaces the Linux-only paths and ships small stand-ins for the programs Homebrew does not have, so it runs on a Mac with one command and behaves on Linux as before. It makes no network requests and needs no configuration.

This is the Markdown version of https://hollywood.celox.io/ for agents and text tools. A short summary with every link lives at https://hollywood.celox.io/llms.txt.

## Download

- **Newest release:** https://hollywood.celox.io/download (picks the file for your platform; always the current release)
- **Current version:** <!--# include virtual="/ssi/version.txt" stub="none" --> · released <!--# include virtual="/ssi/date.txt" stub="none" -->
- **Release data as JSON:** https://hollywood.celox.io/latest.json
- **Requirements:** macOS · Linux: macOS or Linux · tmux

Files in the current release:

<!--# include virtual="/ssi/files.md" stub="none" -->

## Features

- **Twenty widgets** — A world map as ASCII art, falling characters, hex dumps, source code, SSH key art, generated passwords, error codes, manual pages, process monitors, network throughput and progress bars — each in its own pane.
- **Never the same screen twice** — The panes are split at random, horizontally and vertically, and after a delay all but one are closed and dealt again. `-s` sets the number of panes, `-d` the seconds between deals.
- **At home on the Mac** — The original is written for Ubuntu and reads `/sys` and `/proc`. One compatibility file replaces what only Linux has, so every widget finds its material on macOS — and on Linux everything stays as it was.
- **Stand-ins for what Homebrew lacks** — `ccze`, `apg` and `speedometer` are not in Homebrew, and `atop` is Linux-only. hollywood brings small replacements for all four. Install the real program and it takes over.
- **One key ends it** — Ctrl-C in any pane closes the window and every widget with it. Nothing keeps running, and no other process is touched — the original ended its widgets by a name pattern that could hit unrelated programs.
- **Stays on your machine** — hollywood makes no network requests, has no account, no configuration file and no telemetry. The widgets run at the lowest scheduling priority, so the show does not get in the way of real work.

### What it looks like

- **The full show** — Nine panes at once, arranged for the picture. ([image](https://hollywood.celox.io/assets/gallery/stage.jpg))
- **World map** — A satellite picture, drawn with characters. ([image](https://hollywood.celox.io/assets/gallery/map.jpg))
- **Falling characters** — The one everybody knows. ([image](https://hollywood.celox.io/assets/gallery/cmatrix.jpg))
- **Hex dump** — System binaries, byte by byte, in colour. ([image](https://hollywood.celox.io/assets/gallery/hexdump.jpg))
- **Source code** — Files from the system, highlighted and scrolling by. ([image](https://hollywood.celox.io/assets/gallery/code.jpg))
- **Passwords** — Generated, pronounceable and spelled out. ([image](https://hollywood.celox.io/assets/gallery/apg.jpg))

## Install

1. **Install** — With Homebrew: `brew install pepperonas/tap/hollywood` brings hollywood and every program its widgets use. Without Homebrew, `curl -fsSL https://github.com/pepperonas/hollywood/releases/latest/download/install.sh | sh` puts it into `~/.local` and names what is missing.
2. **Run** — Type `hollywood` in a terminal. On a laptop screen `hollywood -s 8` is a good start: eight panes instead of one per widget.
3. **Quit** — Press Ctrl-C in any pane. The window closes, the tmux session that hollywood started ends, and you are back at your prompt.

## Verify

<!--# include virtual="/ssi/checksums.md" stub="none" -->

- The installer script compares the archive with this checksum before it installs anything.

## FAQ

**Is hollywood free?** Yes. It is open source under the Apache-2.0 licence, without ads, accounts or telemetry. The original was written by Dustin Kirkland; this port keeps his licence.

**Why is it not in Homebrew's main repository?** Homebrew has no formula for hollywood, and several programs the original relies on are missing there as well. This port has its own tap: `brew install pepperonas/tap/hollywood`.

**What does it need?** macOS or Linux and `tmux`. Each widget uses one small program such as `cmatrix`, `jp2a` or `htop`; a widget whose program is missing simply does not appear. Homebrew installs all of them.

**How do I update?** With Homebrew: `brew upgrade hollywood`. Otherwise run the installer script again; it replaces the installed copy with the newest release.

**Does it do anything to my system?** No. It only reads and displays: files that every user may read, a generated key that is deleted at once, random data sent to nowhere. It needs no root and sends nothing over the network.

**Is the download genuine?** Every release is built by GitHub Actions from the tagged source. This page shows the SHA-256 of each file; compare it with `shasum -a 256`, or let the installer script do it.

## Limits

- hollywood shows busy-looking output; it does not hack, scan or monitor anything.
- Some widgets show real data of the machine they run on: processes, log files, file names and source files. Look at the panes before sharing the screen.
- On macOS the stand-ins for ccze, apg, speedometer and atop look similar to the originals, not identical.
- It needs tmux; there is no Windows version.
- Developed and run on macOS with Apple silicon; on Linux it is covered by unit tests, not by a full run. For Debian and Ubuntu the original package is the natural choice.

## Links

- Source code: https://github.com/pepperonas/hollywood
- Changelog: https://hollywood.celox.io/changelog.md
- Licence (Apache-2.0): https://github.com/pepperonas/hollywood/blob/main/LICENSE
- Support the project: https://www.paypal.com/donate/?business=martin.pfeffer@celox.io&currency_code=EUR&item_name=hollywood
- Author: Martin Pfeffer, https://celox.io — Imprint https://celox.io/impressum/ · Privacy https://celox.io/datenschutz/
