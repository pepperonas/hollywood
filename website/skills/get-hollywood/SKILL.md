---
name: get-hollywood
description: Download, verify and install the newest hollywood - the free, open-source program that fills a terminal with Hollywood-style technobabble in tmux panes (macOS port, also Linux). Use when someone asks for the tool, its latest version, how to install it on a Mac, or how to check that a download is genuine.
license: Apache-2.0
---

# Get hollywood

hollywood is a free, open-source (Apache-2.0) program that splits a terminal into tmux panes and fills each one with busy-looking output: a world map as ASCII art, falling characters, hex dumps, scrolling source code, SSH key art, network throughput and more - twenty widgets, dealt again every few seconds. This is the macOS port of Dustin Kirkland's hollywood: it replaces the Linux-only paths and ships small stand-ins for the programs Homebrew does not have, so it runs on a Mac with one command and behaves on Linux as before. It makes no network requests and needs no configuration.

## 1. Find the newest release

`GET https://hollywood.celox.io/latest.json` returns `version`, `published`, `notes` and `assets[]`, each with `target`,
`name`, `url`, `size` (bytes) and `sha256`. It is refreshed from GitHub Releases every 15 minutes. On the
page itself, browsers with WebMCP expose the same data as the tools `get_latest_release`,
`get_download_url` and `get_checksums`.

## 2. Download

- Stable link, always the newest file for the visitor's platform: <https://hollywood.celox.io/download>
- macOS · Linux: <https://hollywood.celox.io/download/unix> — macOS or Linux · tmux

## 3. Verify

- The file's SHA-256 must equal the matching `assets[].sha256` in `latest.json`.

- The installer script compares the archive with this checksum before it installs anything.

## 4. Install

1. With Homebrew: `brew install pepperonas/tap/hollywood` brings hollywood and every program its widgets use. Without Homebrew, `curl -fsSL https://github.com/pepperonas/hollywood/releases/latest/download/install.sh | sh` puts it into `~/.local` and names what is missing.
2. Type `hollywood` in a terminal. On a laptop screen `hollywood -s 8` is a good start: eight panes instead of one per widget.
3. Press `q`, or Ctrl-C in any pane. The window closes, the tmux session that hollywood started ends, and you are back at your prompt. The status line at the bottom names the other keys.

## Limits

- hollywood shows busy-looking output; it does not hack, scan or monitor anything.
- Some widgets show real data of the machine they run on: processes, log files, file names and source files. Look at the panes before sharing the screen.
- On macOS the stand-ins for ccze, apg, speedometer and atop look similar to the originals, not identical.
- It needs tmux; there is no Windows version.
- Developed and run on macOS with Apple silicon; on Linux it is covered by unit tests, not by a full run. For Debian and Ubuntu the original package is the natural choice.

More: [product page](https://hollywood.celox.io/) · [Markdown version](https://hollywood.celox.io/index.md) · [changelog](https://hollywood.celox.io/changelog.md) · [source](https://github.com/pepperonas/hollywood)
