# CLAUDE.md

macOS port of Dustin Kirkland's `hollywood` (Apache-2.0): tmux panes full of busy-looking
terminal output. Repo `pepperonas/hollywood` (public), page <https://hollywood.celox.io>,
brew `pepperonas/tap/hollywood`. The sister project is `~/claude/wallstreet`.

## Layout

- `bin/hollywood` — launcher (bash): session, window, random splits, re-deal every `-d` seconds.
- `lib/hollywood/*` — 20 widgets, one script per pane. **Line 2 of every widget sources
  `share/hollywood/compat.sh`** (pinned by a test).
- `share/hollywood/compat.sh` — the only place that knows the platform. Linux values are
  upstream's; Darwin swaps paths/options and appends `shims/` to `PATH`.
- `share/hollywood/shims/` — stand-ins for `ccze`, `apg` (Perl), `speedometer`, `atop`, `batcat` (sh).
- `tools/` — `termshot.py` (tmux window → PNG), `screenshots.sh`, `website_art.py`,
  `badges.py`, `release_notes.py`, `tap-formula.sh`.
- `website/` — project page, built with `~/claude/_templates/apps/product-page` from `website/site.json`.

## Controls (1.1.0)

- `share/hollywood/ctl STATE <close PANE|deal|pause|more|less|help|quit>` is what the keys
  run. It only writes flags into the show's state directory (`mktemp -d …/hollywood.XXXXXXXX`:
  `window`, `splits`, `max`, `panes`, `banned`, `deal`, `paused`) and talks to tmux; the
  launcher's loop reads them once a second.
- Keys are bound in the tmux key table `hollywood`, which is the session option `key-table`
  of the own session only. Never bind in `root` and never set `mouse`/`key-table` in a
  session the launcher did not create (`HOLLYWOOD_OWN_SESSION`) — tests pin both.
- `cleanup` removes the state directory **before** `kill-session`: the launcher runs inside
  that session and dies with it (the directory stayed behind, found in the first run).
- Testing the bindings needs a client: `script -q /dev/null tmux attach -t hollywood &`,
  then `tmux send-keys -K -c <client> x`. Plain `send-keys -t pane` bypasses key tables.
  Mouse buttons were not exercised, only the keys.

## Rules

- Version lives in `VERSION` **and** `bin/hollywood` (`VERSION="…"`), `CHANGELOG.md` and
  `packaging/hollywood.rb` — tests pin all four.
- Never bring back `pkill -f lib/hollywood/`: it kills every process with that path on its
  command line (it killed the shell running the tests here, twice). Widgets quit via `hw_quit`.
- Address the widget window by its tmux id (`$WIN`), never the session by name.
- Screenshots leave out `htop`, `atop`, `logs`, `tree`, `stat`: they show this machine.
- Release = bump the four version places, changelog entry, `git tag vX.Y.Z`, push with tags;
  then `tools/tap-formula.sh > ../homebrew-tap/Formula/hollywood.rb` and push the tap.
- Page: `python3 $K/build.py website/site.json website --hero docs/website/hero.png --icon docs/website/mark.svg --force`,
  then `./website/deploy.sh` (`server` when the kit's timer/vhost changed). `"tls": "wildcard"`.

## Tests

`python3 -m unittest discover -s tests` — no tmux needed. A full run is checked by hand:
detached session (`tmux new-session -d -x 170 -y 48`), `send-keys`, `list-panes`, Ctrl-C,
then no session and no `lib/hollywood/` process may be left.
