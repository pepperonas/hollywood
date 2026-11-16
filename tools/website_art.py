#!/usr/bin/env python3
"""Artwork for the README and the project page.

    python3 tools/website_art.py

Writes docs/website/mark.svg, docs/website/hero.png (2912x1440, the layout the
product-page kit expects: motif left, room for the text on the right) and
docs/banner.png (the same picture at 1456x720 for the README).  The motif is
docs/screenshots/stage.png, so run tools/screenshots.sh first.  Needs a
Chromium-family browser; set TERMSHOT_BROWSER to its binary if none is found.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAME, TAGLINE = "hollywood", "Your terminal, ready for its close-up."
BG, GLOW, WARM = "#0b0d12", "64,201,124", "224,175,104"
W, H = 2912, 1440

MARK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="14" fill="#11141b"/>
<path d="M11 14h42v9H11z" fill="#e8ecf5"/>
<path d="M16 14l-5 9h7l5-9zM30 14l-5 9h7l5-9zM44 14l-5 9h7l5-9z" fill="#11141b"/>
<rect x="11" y="27" width="42" height="24" rx="3" fill="#1b2029"/>
<path d="M18 33l7 6-7 6" fill="none" stroke="#5ee08a" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="29" y="43" width="14" height="4" rx="2" fill="#5ee08a"/>
</svg>
"""

PAGE = """<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;width:{w}px;height:{h}px;background:{bg};overflow:hidden;
  font-family:-apple-system,"Helvetica Neue",Arial,sans-serif}}
.glow{{position:absolute;left:-200px;top:-300px;width:2300px;height:2000px;
  background:radial-gradient(closest-side,rgba({glow},.20),rgba({glow},0))}}
.warm{{position:absolute;left:900px;top:-200px;width:1300px;height:1100px;
  background:radial-gradient(closest-side,rgba({warm},.10),rgba({warm},0))}}
.term{{position:absolute;left:120px;top:190px;width:1640px;border-radius:26px;overflow:hidden;
  background:#11121a;border:2px solid #2c2e3f;box-shadow:0 60px 140px rgba(0,0,0,.6)}}
.bar{{height:62px;background:#16171f;display:flex;align-items:center;padding-left:28px;gap:16px}}
.bar i{{width:22px;height:22px;border-radius:50%;background:#3a3d52;display:block}}
.term img{{display:block;width:1640px}}
.fade{{position:absolute;left:1380px;top:0;width:1532px;height:{h}px;
  background:linear-gradient(90deg,rgba(0,0,0,0),{bg} 32%)}}
.brand{{position:absolute;right:150px;bottom:250px;display:flex;align-items:center;gap:54px}}
.brand svg{{width:200px;height:200px}}
.brand b{{display:block;font-size:150px;letter-spacing:-4px;color:#eef0f7;line-height:1}}
.brand span{{display:block;font-size:52px;color:#a9b1d6;margin-top:16px}}
</style><div class="glow"></div><div class="warm"></div>
<div class="term"><div class="bar"><i></i><i></i><i></i></div><img src="{shot}"></div>
<div class="fade"></div>
<div class="brand">{mark}<div><b>{name}</b><span>{tagline}</span></div></div>
"""


def browser():
    names = [os.environ.get("TERMSHOT_BROWSER"),
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
             "/Applications/Chromium.app/Contents/MacOS/Chromium",
             "google-chrome", "chromium", "chromium-browser"]
    for name in filter(None, names):
        if os.path.isfile(name):
            return name
        if shutil.which(name):
            return shutil.which(name)
    sys.exit("website_art: no Chromium-family browser found (set TERMSHOT_BROWSER)")


def main():
    shot = ROOT / "docs" / "screenshots" / "stage.png"
    if not shot.exists():
        sys.exit("website_art: %s is missing - run tools/screenshots.sh first" % shot)
    out = ROOT / "docs" / "website"
    out.mkdir(parents=True, exist_ok=True)
    (out / "mark.svg").write_text(MARK, encoding="utf-8")
    page = PAGE.format(w=W, h=H, bg=BG, glow=GLOW, warm=WARM, shot=shot.as_uri(),
                       mark=MARK, name=NAME, tagline=TAGLINE)
    hero = out / "hero.png"
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / "hero.html"
        src.write_text(page, encoding="utf-8")
        subprocess.run([browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", "--window-size=%d,%d" % (W, H),
                        "--allow-file-access-from-files", "--screenshot=%s" % hero, src.as_uri()],
                       check=True, capture_output=True)
    print(hero)
    banner = ROOT / "docs" / "banner.png"
    subprocess.run(["magick", str(hero), "-resize", "1456x720", "-strip", str(banner)], check=True)
    print(banner)


if __name__ == "__main__":
    main()
