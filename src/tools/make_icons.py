"""Generuje wszystkie ikony aplikacji (własny projekt – bez logo Google): dwa dymki rozmowy.

  python3 tools/make_icons.py data/icons
"""
import os
import sys

GRAD = ('<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#22d3ee"/>'
        '<stop offset=".55" stop-color="#8b5cf6"/><stop offset="1" stop-color="#ec4899"/></linearGradient>')
BUBBLE = "M14 18h26a6 6 0 0 1 6 6v12a6 6 0 0 1-6 6H26l-8 7v-7h-4a6 6 0 0 1-6-6V24a6 6 0 0 1 6-6z"
BUBBLE2 = "M44 27h6a6 6 0 0 1 6 6v10a6 6 0 0 1-6 6h-2v6l-7-6h-9a6 6 0 0 1-5-3"


def light(dot=False):
    """Jasny motyw systemu: kolorowe tło z gradientem, białe dymki."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs>{GRAD}</defs>
<rect x="2" y="2" width="60" height="60" rx="15" fill="url(#g)"/>
<path d="{BUBBLE}" fill="#fff" opacity=".95"/>
<path d="{BUBBLE2}" fill="none" stroke="#fff" stroke-width="3.2" stroke-linejoin="round" opacity=".85"/>
<circle cx="20" cy="30" r="2.6" fill="#8b5cf6"/><circle cx="27" cy="30" r="2.6" fill="#8b5cf6"/>
<circle cx="34" cy="30" r="2.6" fill="#8b5cf6"/>{DOT if dot else ""}</svg>
'''


def dark(dot=False):
    """Ciemny motyw systemu: granatowe tło bez obwódki, dymki w gradiencie."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs>{GRAD}</defs>
<rect x="2.5" y="2.5" width="59" height="59" rx="15" fill="#151827"/>
<path d="{BUBBLE}" fill="url(#g)"/>
<path d="{BUBBLE2}" fill="none" stroke="#22d3ee" stroke-width="3.2" stroke-linejoin="round"/>
<circle cx="20" cy="30" r="2.6" fill="#0c0e1a"/><circle cx="27" cy="30" r="2.6" fill="#0c0e1a"/>
<circle cx="34" cy="30" r="2.6" fill="#0c0e1a"/>{DOT if dot else ""}</svg>
'''


DOT = '<circle cx="52" cy="12" r="10" fill="#22d3ee" stroke="#0c0e1a" stroke-width="3"/>'


def main(out):
    os.makedirs(out, exist_ok=True)
    files = {"app-light.svg": light(), "app-dark.svg": dark(),
             # "tray2": GNOME caches tray icons by name for the session, so a new look needs a new name
             "lgc-tray2-light.svg": light(), "lgc-tray2-light-unread.svg": light(True),
             "lgc-tray2-dark.svg": dark(), "lgc-tray2-dark-unread.svg": dark(True)}
    for name, svg in files.items():
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            f.write(svg)
    hic = os.path.join(out, "hicolor", "scalable", "apps")
    os.makedirs(hic, exist_ok=True)
    with open(os.path.join(hic, "io.github.jaro.LinuxGoogleChat.svg"), "w", encoding="utf-8") as f:
        f.write(light())
    print("ikony:", ", ".join(sorted(files)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/icons")
