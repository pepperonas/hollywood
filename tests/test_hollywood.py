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
        self.assertRegex(code(ROOT / "bin/hollywood"),
                         r'\[ -n "\$HOLLYWOOD_OWN_SESSION" \] && tmux kill-session')

    def test_nothing_kills_processes_by_pattern(self):
        # upstream's "pkill -9 -f lib/hollywood/" also hit an editor with a widget open
        for path in [ROOT / "bin/hollywood", COMPAT, *WIDGETS]:
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
