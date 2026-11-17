"""Tests for hollywood: the launcher, the widgets, the compatibility layer and
the stand-ins for tools Homebrew does not ship.  Nothing here needs tmux.

    python3 -m unittest discover -s tests -v
"""
import os
import pathlib
import re
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIDGETS = sorted((ROOT / "lib/hollywood").iterdir())
SHIMS = ROOT / "share/hollywood/shims"
COMPAT = ROOT / "share/hollywood/compat.sh"
COMMENT = re.compile(r"^\s*#.*$", re.M)
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def code(path):
    return COMMENT.sub("", path.read_text())


def run(cmd, stdin=None, **kw):
    return subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=20, **kw)


def compat_as(system, expr):
    """Source compat.sh with uname faked to SYSTEM and print EXPR."""
    with tempfile.TemporaryDirectory() as tmp:
        fake = pathlib.Path(tmp) / "uname"
        fake.write_text("#!/bin/sh\necho %s\n" % system)
        fake.chmod(0o755)
        env = dict(os.environ, PATH=tmp + os.pathsep + os.environ["PATH"])
        widget = ROOT / "lib/hollywood/figlet"
        script = 'set -- ; . "%s"; printf "%%s" "%s"' % (COMPAT, expr)
        # $0 must look like a widget, compat.sh finds share/ relative to it
        return run(["sh", "-c", script, str(widget)], env=env).stdout


class Launcher(unittest.TestCase):
    def test_is_valid_bash(self):
        self.assertEqual(run(["bash", "-n", str(ROOT / "bin/hollywood")]).returncode, 0)

    def test_version_option_prints_the_version(self):
        version = (ROOT / "VERSION").read_text().strip()
        self.assertEqual(run([str(ROOT / "bin/hollywood"), "--version"]).stdout.strip(),
                         "hollywood " + version)

    def test_unknown_option_is_a_usage_error(self):
        r = run([str(ROOT / "bin/hollywood"), "--bogus"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr)

    def test_cpu_count_has_a_macos_fallback(self):
        self.assertIn("sysctl -n hw.ncpu", code(ROOT / "bin/hollywood"))

    def test_widgets_are_tracked_by_window_id(self):
        # targeting the session by name hits whatever window is current once
        # the widget window is gone
        src = code(ROOT / "bin/hollywood")
        self.assertIn("WIN=$(tmux new-window -P -F '#{window_id}'", src)
        self.assertNotRegex(src, r"list-panes -t \$PKG\b")

    def test_session_is_only_killed_when_owned(self):
        src = code(ROOT / "bin/hollywood")
        self.assertEqual(src.count("kill-session"), 1)
        self.assertRegex(src, r'if \[ -n "\$HOLLYWOOD_OWN_SESSION" \]; then\s+tmux unbind-key[^\n]*\s+tmux kill-session')

    def test_nothing_kills_processes_by_pattern(self):
        # upstream's "pkill -9 -f lib/hollywood/" also hit an editor with a widget open
        for path in [ROOT / "bin/hollywood", ROOT / "share/hollywood/ctl", COMPAT, *WIDGETS]:
            self.assertNotIn("pkill", code(path), path.name)


class Widgets(unittest.TestCase):
    def test_there_are_twenty(self):
        self.assertEqual(len(WIDGETS), 20)

    def test_all_are_valid_sh(self):
        for w in WIDGETS:
            shell = "bash" if "bash" in w.read_text().split("\n", 1)[0] else "sh"
            self.assertEqual(run([shell, "-n", str(w)]).returncode, 0, w.name)

    def test_all_are_executable(self):
        for w in WIDGETS:
            self.assertTrue(os.access(w, os.X_OK), w.name)

    def test_all_source_the_compat_layer_first(self):
        for w in WIDGETS:
            lines = w.read_text().split("\n")
            self.assertTrue(lines[0].startswith("#!"), w.name)
            self.assertEqual(lines[1], '. "$(dirname "$0")/../../share/hollywood/compat.sh"', w.name)

    def test_no_widget_reads_linux_only_paths(self):
        for w in WIDGETS:
            for path in ("/proc/", "/sys "):
                self.assertNotIn(path, code(w), (w.name, path))

    def test_no_widget_uses_gnu_only_find_options(self):
        for w in WIDGETS:
            self.assertNotRegex(code(w), r"find [^|]*\s-readable", w.name)

    def test_interactive_widgets_end_the_show_on_ctrl_c(self):
        for w in WIDGETS:
            self.assertIn("hw_quit", w.read_text(), w.name)

    def test_key_art_does_not_show_user_and_host(self):
        # ssh-keygen's default comment is user@host and ends up in the fingerprint line
        self.assertRegex(code(ROOT / "lib/hollywood/sshart"), r'ssh-keygen [^\n]*-C "hollywood"')

    def test_picture_widget_survives_spaces_in_paths(self):
        self.assertIn("while IFS= read -r f", code(ROOT / "lib/hollywood/jp2a"))

    def test_man_widget_strips_uncompressed_page_names(self):
        sed = re.search(r'sed (-e .*?) \|', code(ROOT / "lib/hollywood/man")).group(1)
        names = "ls.1\nls.1.gz\nperl.1m\nfoo.1tcl\n"
        out = run(["sh", "-c", "sed " + sed], stdin=names).stdout.split()
        self.assertEqual(out, ["ls", "ls", "perl", "foo"])


class Compat(unittest.TestCase):
    def test_linux_keeps_upstream_paths(self):
        self.assertEqual(compat_as("Linux", "$HW_CODE_DIRS|$HW_NODE_DIRS|$HW_STAT|$HW_READABLE"),
                         "/usr|/sys /dev|stat|-readable")

    def test_linux_path_gets_no_shims(self):
        self.assertNotIn("shims", compat_as("Linux", "$PATH"))

    def test_macos_appends_the_shims(self):
        path = compat_as("Darwin", "$PATH")
        self.assertTrue(path.endswith(str(SHIMS)), path)

    def test_macos_avoids_sys_and_gnu_find(self):
        out = compat_as("Darwin", "$HW_NODE_DIRS|$HW_STAT|$HW_READABLE")
        self.assertNotIn("/sys", out)
        self.assertEqual(out.split("|")[1:], ["stat -x", "-perm -444"])

    def test_macos_directories_have_no_spaces(self):
        # the widgets pass these lists unquoted to find
        for var in ("$HW_CODE_DIRS", "$HW_IMG_DIRS", "$HW_NODE_DIRS"):
            for d in compat_as("Darwin", var).split():
                self.assertTrue(d.startswith("/"), (var, d))

    def test_default_interface_is_found_on_this_machine(self):
        out = run(["sh", "-c", '. "%s"; hw_default_iface' % COMPAT, str(WIDGETS[0])]).stdout.strip()
        if not out:
            self.skipTest("no default route here")
        self.assertRegex(out, r"^[A-Za-z0-9_.:-]+$")

    def test_quit_closes_the_own_window_only(self):
        src = code(COMPAT)
        self.assertIn('tmux kill-window -t "$TMUX_PANE"', src)


class Ccze(unittest.TestCase):
    shim = str(SHIMS / "ccze")

    def test_text_passes_through(self):
        out = run([self.shim, "-A"], stdin="hello world\n").stdout
        self.assertEqual(ANSI.sub("", out), "hello world\n")

    def test_every_line_is_reset_at_the_end(self):
        for line in run([self.shim, "-A"], stdin="a\nb\n").stdout.splitlines():
            self.assertTrue(line.endswith("\x1b[0m"), repr(line))

    def test_default_colour_option(self):
        self.assertTrue(run([self.shim, "-A", "-c", "default=green"], stdin="x\n").stdout.startswith("\x1b[0;32m"))

    def test_bold_colour_option(self):
        out = run([self.shim, "-A", "-c", "default=green", "-c", 'dir=bold green'], stdin="x\n").stdout
        self.assertTrue(out.startswith("\x1b[0;32m"))

    def test_errors_are_red_and_ok_is_green(self):
        out = run([self.shim, "-A"], stdin="error then ok\n").stdout
        self.assertIn("\x1b[1;31merror", out)
        self.assertIn("\x1b[1;32mok", out)

    def test_unknown_colour_is_ignored(self):
        r = run([self.shim, "-A", "-c", "default=plaid"], stdin="x\n")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(ANSI.sub("", r.stdout), "x\n")


class Apg(unittest.TestCase):
    shim = str(SHIMS / "apg")

    def test_one_line_password_syllables_spelling(self):
        for _ in range(20):
            out = run([self.shim, "-qlt", "-n", "1"]).stdout
            self.assertRegex(out, r"^\w+ \([\w-]+\) [\w-]+\n$")

    def test_syllables_spell_the_password(self):
        for _ in range(20):
            pw, syl, _ = run([self.shim]).stdout.split()
            self.assertEqual(syl.strip("()").replace("-", ""), pw)

    def test_spelling_has_one_word_per_character(self):
        for _ in range(20):
            pw, _, spelled = run([self.shim]).stdout.split()
            self.assertEqual(len(spelled.split("-")), len(pw))

    def test_capitals_are_spelled_in_capitals(self):
        for _ in range(40):
            pw, _, spelled = run([self.shim]).stdout.split()
            for ch, word in zip(pw, spelled.split("-")):
                if ch.isalpha():
                    self.assertEqual(word.isupper(), ch.isupper(), (pw, spelled))


class OtherShims(unittest.TestCase):
    def test_all_shims_are_executable(self):
        for shim in SHIMS.iterdir():
            self.assertTrue(os.access(shim, os.X_OK), shim.name)

    def test_perl_shims_compile(self):
        for name in ("ccze", "apg"):
            self.assertEqual(run(["perl", "-c", str(SHIMS / name)]).returncode, 0, name)

    def test_shell_shims_are_valid(self):
        for name in ("atop", "batcat", "speedometer"):
            self.assertEqual(run(["sh", "-n", str(SHIMS / name)]).returncode, 0, name)

    def test_speedometer_without_interface_fails(self):
        self.assertEqual(run([str(SHIMS / "speedometer")]).returncode, 1)

    def test_speedometer_with_unknown_interface_fails(self):
        self.assertEqual(run([str(SHIMS / "speedometer"), "-rx", "nosuchif0", "-tx", "nosuchif0"]).returncode, 1)

    def test_batcat_hands_over_to_bat(self):
        self.assertIn('exec bat "$@"', (SHIMS / "batcat").read_text())


FAKE_TMUX = r'''#!/usr/bin/env python3
# stand-in for tmux: records what it is asked and keeps a table of panes
# (id widget keep active since width height) that the commands change
import os, sys
log, table = os.environ["FAKE_LOG"], os.environ["FAKE_PANES"]
args = sys.argv[1:]
open(log, "a").write(" ".join(args) + "\n")
rows = [l.split() for l in open(table).read().splitlines() if l.strip()]
save = lambda: open(table, "w").write("".join(" ".join(r) + "\n" for r in rows))
target = lambda a: a[a.index("-t") + 1] if "-t" in a else ""
cmds, cur = [], []
for a in args:
    if a == ";":
        cmds.append(cur); cur = []
    else:
        cur.append(a)
cmds.append(cur)
for a in cmds:
    if not a:
        continue
    if a[0] == "list-panes":
        fmt = a[a.index("-F") + 1] if "-F" in a else "#{pane_id}"
        for r in rows:
            out = fmt
            for key, val in (("#{?@keep,1,0}", r[2]), ("#{?@since,#{@since},0}", r[4]), ("#{pane_active}", r[3]),
                             ("#{pane_id}", r[0]), ("#{@widget}", r[1]), ("#{pane_width}", r[5]), ("#{pane_height}", r[6])):
                out = out.replace(key, val)
            print(out)
    elif a[0] == "split-window":
        rows.append(["%9", "new", "0", "0", "999", "40", "10"]); save(); print("%9")
    elif a[0] == "kill-pane":
        rows = [r for r in rows if r[0] != target(a)]; save()
    elif a[0] == "respawn-pane":
        pass
    elif a[0] == "show-options":
        print("".join(r[2] for r in rows if r[0] == target(a)).replace("0", ""))
    elif a[0] == "set-option" and "-p" in a:
        for r in rows:
            if r[0] == target(a):
                if "@keep" in a:
                    r[2] = "0" if "-u" in a else "1"
                elif "@widget" in a:
                    r[1] = a[-1]
                elif "@since" in a:
                    r[4] = "1000"
        save()
'''


class Controls(unittest.TestCase):
    """share/hollywood/ctl against a stand-in for tmux that records what it is asked."""
    ctl = str(ROOT / "share/hollywood/ctl")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.tmp.name)
        self.state = root / "state"
        self.state.mkdir()
        (self.state / "window").write_text("@1\n")
        (self.state / "banned").write_text("")
        (self.state / "splits").write_text("4\n")
        (self.state / "max").write_text("20\n")
        (self.state / "panes").write_text("%1 map\n%2 cmatrix\n%3 hexdump\n")
        (self.state / "widgets").write_text(str(ROOT / "lib/hollywood") + "\n")
        # id widget keep active since width height
        self.panes = root / "panes"
        self.panes.write_text("%1 map 0 1 100 80 20\n%2 cmatrix 0 0 200 40 10\n%3 hexdump 0 0 300 40 10\n")
        self.log = root / "log"
        fake = root / "bin"
        fake.mkdir()
        (fake / "tmux").write_text(FAKE_TMUX)
        (fake / "tmux").chmod(0o755)
        self.env = dict(os.environ, PATH=str(fake) + os.pathsep + os.environ["PATH"],
                        FAKE_LOG=str(self.log), FAKE_PANES=str(self.panes))

    def on_screen(self):
        return {r.split()[0]: r.split()[1] for r in self.panes.read_text().splitlines()}

    def tearDown(self):
        self.tmp.cleanup()

    def run_ctl(self, *args):
        return run([self.ctl, str(self.state), *args], env=self.env)

    def calls(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def banned(self):
        return (self.state / "banned").read_text().split()

    def test_close_kills_the_pane_and_bans_its_widget(self):
        self.run_ctl("close", "%2")
        self.assertEqual(self.banned(), ["cmatrix"])
        self.assertIn("kill-pane -t %2", self.calls())

    def test_a_widget_is_banned_only_once(self):
        self.run_ctl("close", "%2")
        (self.state / "panes").write_text("%1 map\n%4 cmatrix\n%3 hexdump\n")
        self.panes.write_text("%1\n%4\n%3\n")
        self.run_ctl("close", "%4")
        self.assertEqual(self.banned(), ["cmatrix"])

    def test_the_last_pane_cannot_be_closed(self):
        self.panes.write_text("%1\n")
        self.run_ctl("close", "%1")
        self.assertEqual(self.banned(), [])
        self.assertFalse([c for c in self.calls() if c.startswith("kill-pane")])

    def test_a_pane_outside_the_show_is_left_alone(self):
        # the key table is active in the whole session, the launcher's shell included
        self.run_ctl("close", "%99")
        self.assertEqual(self.banned(), [])
        self.assertFalse([c for c in self.calls() if c.startswith("kill-pane")])

    def test_a_pane_reused_by_tmux_bans_its_newest_widget(self):
        (self.state / "panes").write_text("%1 map\n%2 cmatrix\n%3 hexdump\n%2 figlet\n")
        self.run_ctl("close", "%2")
        self.assertEqual(self.banned(), ["figlet"])

    def test_deal_leaves_a_flag_for_the_launcher(self):
        self.run_ctl("deal")
        self.assertTrue((self.state / "deal").exists())

    def test_pause_toggles(self):
        self.run_ctl("pause")
        self.assertTrue((self.state / "paused").exists())
        self.run_ctl("pause")
        self.assertFalse((self.state / "paused").exists())

    def test_more_adds_one_pane_and_leaves_the_others(self):
        self.run_ctl("more")
        self.assertEqual(list(self.on_screen())[:3], ["%1", "%2", "%3"])
        self.assertEqual(len(self.on_screen()), 4)
        self.assertEqual((self.state / "splits").read_text().strip(), "4")
        self.assertFalse((self.state / "deal").exists(), "more must not build the screen anew")
        self.assertFalse([c for c in self.calls() if c.startswith("kill-pane")])
        new = self.on_screen()["%9"]
        self.assertNotIn(new, ("map", "cmatrix", "hexdump"), "a widget that is on screen already")
        self.assertTrue((ROOT / "lib/hollywood" / new).exists())

    def test_the_largest_pane_is_the_one_that_is_split(self):
        self.run_ctl("more")
        split = [c for c in self.calls() if c.startswith("split-window")][0]
        self.assertIn("-t %1 ", split)
        self.assertIn(" -h ", split)          # 80 x 20: wider than high, even in character cells
        self.assertIn(" -d ", split)          # the selection stays where it is

    def test_more_never_opens_a_closed_widget(self):
        every = sorted(w.name for w in WIDGETS)
        (self.state / "banned").write_text("\n".join(w for w in every if w != "figlet") + "\n")
        self.run_ctl("more")
        self.assertEqual(self.on_screen()["%9"], "figlet")

    def test_less_takes_the_newest_pane_that_is_neither_kept_nor_selected(self):
        self.run_ctl("less")
        self.assertEqual(list(self.on_screen()), ["%1", "%2"])
        self.assertEqual(self.banned(), [], "less closes a pane, it does not ban its widget")
        self.assertEqual((self.state / "splits").read_text().strip(), "2")
        self.assertFalse((self.state / "deal").exists())

    def test_less_spares_kept_panes(self):
        self.run_ctl("keep", "%3")
        self.run_ctl("less")
        self.assertEqual(list(self.on_screen()), ["%1", "%3"])

    def test_the_last_pane_survives_less(self):
        self.panes.write_text("%1 map 0 1 100 80 20\n")
        self.run_ctl("less")
        self.assertEqual(list(self.on_screen()), ["%1"])

    def test_no_pane_is_added_when_every_widget_is_on_screen(self):
        (self.state / "max").write_text("3\n")
        self.run_ctl("more")
        self.assertEqual(len(self.on_screen()), 3)

    def test_swap_changes_the_oldest_idle_pane_in_place(self):
        self.run_ctl("swap")
        respawn = [c for c in self.calls() if c.startswith("respawn-pane")]
        self.assertEqual(len(respawn), 1)
        # %1 is older but selected: the user is looking at it
        self.assertIn("-k -t %2 ", respawn[0])
        self.assertEqual(len(self.on_screen()), 3)
        self.assertNotIn(self.on_screen()["%2"], ("map", "cmatrix", "hexdump"))
        self.assertFalse([c for c in self.calls() if c.startswith(("kill-pane", "split-window"))])

    def test_swap_takes_the_selected_pane_when_it_is_the_only_free_one(self):
        self.run_ctl("keep", "%2")
        self.run_ctl("keep", "%3")
        self.run_ctl("swap")
        self.assertIn("-k -t %1 ", [c for c in self.calls() if c.startswith("respawn-pane")][0])

    def test_kept_panes_are_never_swapped_by_the_clock(self):
        for pane in ("%1", "%2", "%3"):
            self.run_ctl("keep", pane)
        self.run_ctl("swap")
        self.assertFalse([c for c in self.calls() if c.startswith("respawn-pane")])

    def test_swap_of_a_named_pane_is_the_users_wish(self):
        self.run_ctl("keep", "%3")
        self.run_ctl("swap", "%3")
        self.assertIn("-k -t %3 ", [c for c in self.calls() if c.startswith("respawn-pane")][0])
        self.run_ctl("swap", "%99")
        self.assertEqual(len([c for c in self.calls() if c.startswith("respawn-pane")]), 1)

    def test_keep_toggles(self):
        keep = lambda: [r.split()[2] for r in self.panes.read_text().splitlines()]
        self.run_ctl("keep")
        self.assertEqual(keep(), ["1", "0", "0"])
        self.run_ctl("keep", "%1")
        self.assertEqual(keep(), ["0", "0", "0"])
        self.run_ctl("keep", "%99")
        self.assertEqual(keep(), ["0", "0", "0"])

    def test_closing_a_pane_updates_the_count_for_the_next_deal(self):
        self.run_ctl("close", "%2")
        self.assertEqual((self.state / "splits").read_text().strip(), "2")

    def test_quit_closes_the_window_of_the_show(self):
        self.run_ctl("quit")
        self.assertIn("kill-window -t @1", self.calls())

    def test_close_without_a_pane_takes_the_active_one(self):
        self.run_ctl("close")
        self.assertEqual(self.banned(), ["map"])
        self.assertIn("kill-pane -t %1", self.calls())

    def test_zoom_toggles_the_named_pane(self):
        self.run_ctl("zoom", "%3")
        self.assertIn("resize-pane -Z -t %3", self.calls())

    def test_zoom_leaves_panes_outside_the_show_alone(self):
        self.run_ctl("zoom", "%99")
        self.assertFalse([c for c in self.calls() if c.startswith("resize-pane")])

    def test_open_starts_the_widget_and_lifts_its_ban(self):
        (self.state / "banned").write_text("figlet\ncmatrix\n")
        self.run_ctl("open", "figlet")
        self.assertEqual(self.banned(), ["cmatrix"])
        self.assertTrue([c for c in self.calls() if c.startswith("split-window") and c.endswith("/lib/hollywood/figlet'")])
        self.assertIn("%9 figlet", (self.state / "panes").read_text().splitlines())
        self.assertEqual(self.on_screen()["%9"], "figlet")
        self.assertEqual(len(self.on_screen()), 4)

    def test_open_takes_only_names_of_widgets(self):
        # the name ends up in a command line: nothing that is not a widget file may pass
        for name in ("../../bin/hollywood", "/bin/sh", "nosuchwidget", "", ".hidden", "figlet; touch x"):
            self.run_ctl("open", name)
        self.assertFalse([c for c in self.calls() if c.startswith("split-window")])

    def test_restore_lifts_every_ban_and_leaves_the_screen_alone(self):
        (self.state / "banned").write_text("figlet\ncmatrix\n")
        self.run_ctl("restore")
        self.assertEqual(self.banned(), [])
        self.assertFalse((self.state / "deal").exists())
        self.assertEqual(len(self.on_screen()), 3)

    def test_restore_with_nothing_closed_does_not_deal(self):
        self.run_ctl("restore")
        self.assertFalse((self.state / "deal").exists())

    def test_a_toolbar_button_does_what_its_key_does(self):
        self.run_ctl("button", "pause")
        self.assertTrue((self.state / "paused").exists())
        self.run_ctl("button", "more")
        self.assertEqual(len(self.on_screen()), 4)
        self.run_ctl("button", "keep")
        self.assertEqual(self.panes.read_text().splitlines()[0].split()[2], "1")
        self.run_ctl("button", "quit")
        self.assertIn("kill-window -t @1", self.calls())

    def test_a_click_beside_the_buttons_does_nothing(self):
        # tmux reports an empty range for a click on plain text of the bar
        for name in ("", "bogus", "open", "panemenu", "helppage"):
            self.run_ctl("button", name)
        self.assertFalse([c for c in self.calls() if not c.startswith("list-panes")])
        self.assertEqual(sorted(p.name for p in self.state.iterdir()),
                         ["banned", "max", "panes", "splits", "widgets", "window"])

    def test_the_widget_menu_lists_every_widget_with_its_state(self):
        (self.state / "banned").write_text("figlet\n")
        self.run_ctl("menu")
        menu = [c for c in self.calls() if c.startswith("display-menu")][0]
        for w in WIDGETS:
            self.assertIn(" %s " % w.name, menu)
        self.assertIn("x figlet", menu)

    def test_the_pane_menu_acts_on_the_pane_that_was_clicked(self):
        self.run_ctl("panemenu", "%2")
        menu = [c for c in self.calls() if c.startswith("display-menu")][0]
        self.assertIn("-T  cmatrix ", menu)
        self.assertIn("close '%2'", menu)
        self.assertIn("zoom '%2'", menu)

    def test_the_help_page_names_every_key(self):
        text = run([self.ctl, str(self.state), "helppage"], env=self.env, stdin="\n").stdout
        for key in ("s ", "k ", "x ", "a ", "r ", "n ", "p ", "+ -", "q ", "double click", "right click"):
            self.assertIn(key, text)

    def test_without_a_state_directory_nothing_happens(self):
        r = run([self.ctl, str(self.state) + "-gone", "quit"], env=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.calls(), [])


class Interaction(unittest.TestCase):
    src = code(ROOT / "bin/hollywood")

    def function(self, name):
        return re.search(r"^%s\(\) \{\n.*?^\}" % name, (ROOT / "bin/hollywood").read_text(), re.M | re.S).group(0)

    def test_banned_widgets_are_not_dealt_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            pathlib.Path(tmp, "banned").write_text("cmatrix\nmap\n")
            script = '%s\nWIDGET_DIR="%s"; STATE="%s"; candidates' % (
                self.function("candidates"), ROOT / "lib/hollywood", tmp)
            dealt = run(["bash", "-c", script]).stdout.split()
        self.assertEqual(len(dealt), 18)
        self.assertFalse({"cmatrix", "map"} & set(dealt))

    def test_with_nothing_banned_everything_is_dealt(self):
        with tempfile.TemporaryDirectory() as tmp:
            pathlib.Path(tmp, "banned").write_text("")
            script = '%s\nWIDGET_DIR="%s"; STATE="%s"; candidates' % (
                self.function("candidates"), ROOT / "lib/hollywood", tmp)
            self.assertEqual(len(run(["bash", "-c", script]).stdout.split()), 20)

    def test_controls_exist_only_in_a_session_the_launcher_created(self):
        # mouse and key-table are session options: in somebody else's session they are theirs
        body = self.function("controls")
        self.assertRegex(body, r'\[ -n "\$HOLLYWOOD_OWN_SESSION" \] \|\| return 0')
        outside = self.src.replace(COMMENT.sub("", body), "")
        for word in (r"mouse on", r"key-table", r"(?<!un)bind-key"):
            self.assertNotRegex(outside, word)

    def test_keys_live_in_their_own_table_not_in_root(self):
        body = COMMENT.sub("", self.function("controls"))
        binds = re.findall(r"bind-key (.*)", body)
        self.assertGreaterEqual(len(binds), 18)
        self.assertTrue(all(b.startswith("-T $PKG ") for b in binds), binds)

    def test_every_control_is_bound(self):
        body = COMMENT.sub("", self.function("controls"))
        for key in ("MouseDown1Pane", "DoubleClick1Pane", "MouseDown3Pane", "MouseDrag1Border",
                    "MouseDown1Status", "s", "k", "x", "z", "a", "r", "n", "p", "Space", "+", "-", "?", "q"):
            self.assertRegex(body, r"bind-key -T \$PKG %s " % re.escape(key))

    def test_every_toolbar_button_has_a_command_and_a_key(self):
        bar = self.function("toolbar")
        names = set(re.findall(r"range=user\|(\w+)", bar))
        self.assertEqual(names, {"swap", "keep", "close", "menu", "restore", "deal", "pause", "zoom", "less", "more", "help", "quit"})
        ctl = (ROOT / "share/hollywood/ctl").read_text()
        allowed = set(re.search(r"case \"\$arg\" in\s+([a-z|]+)\)", ctl).group(1).split("|"))
        self.assertEqual(names, allowed, "a button without a command, or a command without a button")
        for name in names:
            self.assertRegex(ctl, r"(?m)^\t(\w+\|)*%s(\|\w+)*\)$" % name)
        self.assertIn("MouseDown1Status run-shell -b \"$ctl button '#{mouse_status_range}'\"", self.function("controls"))

    def test_no_key_holds_up_the_tmux_server(self):
        # run-shell without -b waits for its command - and a popup or a menu started
        # from there waits for the server: the show froze on "?" (found in the first run)
        body = COMMENT.sub("", self.function("controls"))
        self.assertGreaterEqual(body.count("run-shell -b "), 15)
        self.assertEqual(body.count("run-shell "), body.count("run-shell -b "))
        self.assertRegex(body, r'bind-key -T \$PKG \? display-popup [^\n]*helppage')

    def test_the_clock_stands_still_while_paused_or_zoomed(self):
        loop = self.src[self.src.index("i=0\nwhile true"):]
        self.assertRegex(loop, r'elif \[ -e "\$STATE/paused" \] \|\| zoomed; then\s+:\s+else\s+i=\$\(\(i\+1\)\)')

    def test_by_itself_the_show_changes_one_pane_and_not_the_screen(self):
        # upstream rebuilt everything every ten seconds: selection, sizes and whatever
        # the user had arranged were gone each time
        loop = self.src[self.src.index("i=0\nwhile true"):]
        self.assertRegex(loop, r'if \[ "\$CHANGE" = deal \]; then\s+deal\s+else\s+"\$SHARE_DIR/ctl" "\$STATE" swap\s+fi')
        self.assertRegex(self.src, r"(?m)^CHANGE=swap$")
        self.assertRegex(self.src, r"-r\|--redeal\)\s+CHANGE=deal")
        self.assertRegex(self.src, r"-d \$DELAY\$\(\[ \$CHANGE = deal \] && echo ' -r'\)")

    def test_a_deal_spares_the_panes_the_user_keeps(self):
        deal = self.function("deal")
        self.assertNotIn("kill-pane -a", deal)
        self.assertIn("#{?@keep,1,0} #{pane_id}", deal)
        self.assertRegex(deal, r'echo "\$stay" \| grep -qxF "\$id" \|\| tmux kill-pane -t "\$id"')
        self.assertIn("tail -n 1", deal)        # without a kept pane one stays, or the window goes

    def test_a_closed_terminal_cleans_up_too(self):
        self.assertIn("trap cleanup INT TERM HUP EXIT", self.src)

    def test_every_pane_carries_the_name_of_its_widget(self):
        self.assertIn('set-option -p -t "$id" @widget "$3"', self.function("start_widget"))
        self.assertIn('@since "$(date +%s)"', self.function("start_widget"))
        self.assertIn("#{?@keep, [kept],}", self.function("controls"))
        self.assertIn('@widget "$widget1"', self.src)
        self.assertIn("#{@widget}", self.function("controls"))

    def test_the_picture_of_the_toolbar_is_the_toolbar(self):
        # tools/screenshots.sh draws the bar itself; it must show the real buttons, in order
        def buttons(text):
            return re.findall(r"range=user\|(\w+)\]\$\{?b\}? ([^$#]*?) \$", text)
        real = [b for b in buttons(self.function("toolbar")) if b[0] != "restore"]   # only shown after a close
        shot = buttons((ROOT / "tools/screenshots.sh").read_text())
        self.assertGreaterEqual(len(real), 9)
        self.assertEqual(shot, real)

    def test_the_state_is_removed_before_the_session_is_killed(self):
        # the launcher runs inside the session and dies with it
        body = self.function("cleanup")
        self.assertLess(body.index('rm -rf "$STATE"'), body.index("kill-session"))

    def test_the_key_table_is_cleared_on_the_way_out(self):
        self.assertIn("unbind-key -a -T $PKG", self.function("cleanup"))

    def test_a_deal_asked_by_key_restarts_the_clock(self):
        loop = self.src[self.src.index("i=0\nwhile true"):]
        self.assertRegex(loop, r'if \[ -e "\$STATE/deal" \]; then\s+rm -f "\$STATE/deal"\s+deal\s+i=0')

    def test_ctl_is_executable_and_valid(self):
        self.assertTrue(os.access(ROOT / "share/hollywood/ctl", os.X_OK))
        self.assertEqual(run(["sh", "-n", str(ROOT / "share/hollywood/ctl")]).returncode, 0)


class Project(unittest.TestCase):
    def test_launcher_carries_the_version(self):
        version = (ROOT / "VERSION").read_text().strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertIn('VERSION="%s"' % version, (ROOT / "bin/hollywood").read_text())

    def test_changelog_starts_with_the_version(self):
        version = (ROOT / "VERSION").read_text().strip()
        first = re.search(r"^## \[(\d+\.\d+\.\d+)\]", (ROOT / "CHANGELOG.md").read_text(), re.M)
        self.assertEqual(first.group(1), version)

    def test_formula_carries_the_version(self):
        version = (ROOT / "VERSION").read_text().strip()
        formula = (ROOT / "packaging/hollywood.rb").read_text()
        self.assertIn("/v%s/hollywood.tar.gz" % version, formula)
        self.assertIn('version "%s"' % version, formula)

    def test_formula_depends_on_what_the_installer_looks_for(self):
        formula = (ROOT / "packaging/hollywood.rb").read_text()
        for dep in ("tmux", "bat", "bmon", "cmatrix", "figlet", "htop", "jp2a", "moreutils", "mplayer", "pv", "tree"):
            self.assertIn('depends_on "%s"' % dep, formula)

    def test_licence_and_notice_are_there(self):
        self.assertIn("Apache License", (ROOT / "LICENSE").read_text())
        notice = (ROOT / "NOTICE").read_text()
        self.assertIn("Dustin Kirkland", notice)

    def test_installer_names_the_release_asset(self):
        release = (ROOT / ".github/workflows/release.yml").read_text()
        self.assertIn("assets/hollywood.tar.gz", release)
        self.assertIn('"$BASE/$NAME.tar.gz"', (ROOT / "install.sh").read_text())


if __name__ == "__main__":
    unittest.main()
