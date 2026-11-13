"""Gdzie leżą dane aplikacji (ikony, obrazy) – w źródłach albo po instalacji z .deb."""
import os

_here = os.path.dirname(os.path.abspath(__file__))
_candidates = [
    os.environ.get("LGC_DATA", ""),
    os.path.join(_here, "..", "..", "data"),                # uruchomienie ze źródeł
    "/usr/share/linux-google-chat/data",                     # zainstalowany .deb
]
DATA = next((os.path.abspath(p) for p in _candidates if p and os.path.isdir(p)), _candidates[-1])
ICON_DIR = os.path.join(DATA, "icons")


def data(*parts):
    return os.path.join(DATA, *parts)
