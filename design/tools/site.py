"""Builds the data for the design site (design/site): python3 design/tools/site.py

The site's page and script are written by hand (design/site/index.html, app.js). This writes data.js beside them
from the same sources as the board: the screen mock-ups, the board's layouts and the two documents.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mock  # noqa: E402
from gfx import ROOT  # noqa: E402
from screens import ANIM, SCREENS  # noqa: E402


def decisions(text):
    sec = text.split("## 14. Decisions", 1)[1].split("\n## 15.", 1)[0]
    decided_txt, open_txt = sec.split("\nOpen.", 1)
    decided = []
    for m in re.finditer(r"^- \*\*(.+?)\*\*(.*?)(?=^- \*\*|\Z)", decided_txt, re.S | re.M):
        rest = " ".join(m.group(2).split())
        d = re.search(r"\((\d+ \w+ 2026)\)", rest)
        rest = re.sub(r"^\s*\(\d+ \w+ 2026\)[.:,]?\s*", "", rest)
        decided.append({"title": m.group(1), "date": d.group(1) if d else "", "text": rest.lstrip(":,. ")})
    opens = []
    for m in re.finditer(r"^(\d+)\. \*\*(.+?)\*\*(.*?)(?=^\d+\. \*\*|\Z)", open_txt, re.S | re.M):
        opens.append({"n": int(m.group(1)), "title": m.group(2).rstrip("."), "text": " ".join(m.group(3).split())})
    opens.sort(key=lambda o: o["n"])
    return decided, opens


def main():
    screens = {}
    for key, name, fn, desc in SCREENS:
        fr = [(s.b64(), ms) for s, ms in ANIM[key]] if key in ANIM else [(fn().b64(), 600)]
        screens[key] = {"name": name, "desc": desc, "frames": [f for f, _ in fr], "ms": [ms for _, ms in fr]}
    metas, index, layouts = [], {}, []
    for fn, key in mock.LAYOUTS:
        ctl, name, desc = fn()
        out = {}
        for cid, e in ctl.items():
            m = json.dumps(e.get("meta", {}), sort_keys=True)
            if m not in index:
                index[m] = len(metas)
                metas.append(e.get("meta", {}))
            led = e.get("led", {})
            out[cid] = [led.get("color", led.get("brightness")), index[m]]
        layouts.append({"name": name, "desc": desc, "screen": key, "controls": out})
    design = open(os.path.join(ROOT, "docs", "DESIGN.md")).read()
    arch = open(os.path.join(ROOT, "docs", "ARCHITECTURE.md")).read()
    decided, opens = decisions(design)
    draft = re.search(r"Draft \d+, [^.]+", design).group(0)
    data = {"draft": draft, "screens": screens, "layouts": layouts, "metas": metas, "track": mock.TRACK,
            "shift": mock.SHIFT, "decided": decided, "open": opens, "docs": {"design": design, "arch": arch},
            "font": json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts.json")))["f5"]}
    site = os.path.join(ROOT, "design", "site")
    os.makedirs(site, exist_ok=True)
    with open(os.path.join(site, "data.js"), "w") as f:
        f.write("window.FD = " + json.dumps(data, separators=(",", ":")) + ";\n")
    print("wrote design/site/data.js: %d screens, %d layouts, %d decided, %d open, %d kB"
          % (len(screens), len(layouts), len(decided), len(opens), os.path.getsize(os.path.join(site, "data.js")) // 1024))


if __name__ == "__main__":
    main()
