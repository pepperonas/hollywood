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

## Controls (1.3.0)

- **By itself the show swaps ONE pane** every `-d` seconds (`ctl swap`: `respawn-pane -k`
  in the pane that has shown its widget longest - pane option `@since` - and is neither
  kept nor, if avoidable, selected). The full rebuild (`deal`) happens only on `n` or with
  `-r`. Do not bring the periodic rebuild back as default: it threw away selection, sizes
  and everything the user had arranged (user report 2026-11-17).
- `+`/`-`/`r`/`x`/`a` never set the `deal` flag. `add()` halves the largest pane (`-d`: the
  selection stays). `splits` follows the real pane count and only feeds the next `n`.
- `k` sets the pane option `@keep`; swap, `less` and `deal` spare such panes.
- The tests' stand-in for tmux (`FAKE_TMUX`) keeps a table of panes and understands the
  format strings ctl uses - a new format string needs a line there.

- `share/hollywood/ctl STATE <command>` is what keys, mouse and toolbar run: `close [PANE]`,
  `swap [PANE]`, `keep [PANE]`, `zoom [PANE]`, `open WIDGET`, `restore`, `deal`, `pause`, `more`, `less`, `menu`,
  `panemenu PANE`, `button NAME`, `help`, `helppage`, `quit`. It only writes flags into the
  show's state directory (`mktemp -d …/hollywood.XXXXXXXX`: `window`, `widgets`, `splits`,
  `max`, `panes`, `banned`, `deal`, `paused`) and talks to tmux; the launcher's loop reads
  them once a second and redraws the toolbar (`toolbar`, `status-format[0]`).
- The toolbar's buttons are tmux click ranges (`#[range=user|NAME]`, tmux >= 3.4);
  `MouseDown1Status` hands `#{mouse_status_range}` to `ctl button`. A test keeps the
  buttons, the `button` case in ctl and the commands in step.
- Pane names are the pane option `@widget` (not the title: programs overwrite titles),
  shown by `pane-border-status top`.
- **Every binding is `run-shell -b`.** Without `-b` tmux waits for the command - and a
  popup started from there waits for the server: the whole show froze on `?`. The help
  popup is therefore opened by tmux itself (`display-popup -E "ctl … helppage"`).
- Keys are bound in the tmux key table `hollywood`, which is the session option `key-table`
  of the own session only. Never bind in `root` and never set `mouse`/`key-table` in a
  session the launcher did not create (`HOLLYWOOD_OWN_SESSION`) — tests pin both.
- `ctl open` puts a name into a command line: `known()` lets only file names of the widget
  directory pass (pinned with hostile names).
- `cleanup` removes the state directory **before** `kill-session`: the launcher runs inside
  that session and dies with it.
- Testing the bindings needs a client: `script -q /dev/null tmux attach -t hollywood &`,
  then `tmux send-keys -K -c <client> x`. Plain `send-keys -t pane` bypasses key tables.
  Wrap every tmux call of such a test in `timeout`: a blocked server hangs them all.
  After `tmux kill-server` wait a second before `new-session`, or the new session lands in
  the dying server. Mouse buttons and menu picks were not exercised, only the keys and
  `ctl` directly.
- `tools/termshot.py` draws the pane names and the toolbar into the pictures;
  `tools/screenshots.sh` sets both for its staged layout (a test compares its bar with the
  real one).

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
