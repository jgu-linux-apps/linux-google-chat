"""Tłumaczenia PL / EN i ustawienia aplikacji (~/.config/linux-google-chat/settings.json)."""
import json
import locale
import os

from gi.repository import GLib

CONFIG_DIR = os.path.join(GLib.get_user_config_dir(), "linux-google-chat")
CONFIG = os.path.join(CONFIG_DIR, "settings.json")
DEFAULTS = {"language": "auto", "theme": "system", "notifications": True, "dnd": False, "autostart": False,
            "close_to_tray": True, "spellcheck": True, "zoom": 1.0}

PL = {
    "Chat": "Chat",
    "Home": "Strona główna",
    "Reload (F5)": "Odśwież (F5)",
    "Do Not Disturb": "Nie przeszkadzać",
    "Do Not Disturb is on – notifications are muted": "Tryb Nie przeszkadzać – powiadomienia wyciszone",
    "Main menu": "Menu główne",
    "Preferences": "Ustawienia",
    "Theme": "Motyw",
    "System": "Systemowy",
    "Aurora": "Aurora",
    "Studio Pro": "Studio Pro",
    "Language": "Język",
    "Automatic (system language)": "Automatycznie (język systemu)",
    "Language change takes effect after restarting the app": "Zmiana języka zadziała po ponownym uruchomieniu",
    "Zoom": "Powiększenie",
    "Zoom in": "Powiększ",
    "Zoom out": "Pomniejsz",
    "Reset zoom": "Rzeczywisty rozmiar",
    "About Linux Google Chat": "O programie Linux Google Chat",
    "Quit": "Zakończ",
    "Show Chat": "Pokaż Chat",
    "%d unread": "%d nieprzeczytane",
    "Appearance": "Wygląd",
    "Window and menu colours; light or dark follows the system": "Kolory okna i menu; jasny lub ciemny jak system",
    "Notifications": "Powiadomienia",
    "Show new messages as GNOME notifications": "Nowe wiadomości jako powiadomienia GNOME",
    "Start with the system": "Uruchamiaj z systemem",
    "In the background – only the tray icon": "W tle – tylko ikona w zasobniku",
    "Keep running in the tray when the window is closed": "Po zamknięciu okna działaj w zasobniku",
    "Spell checking (Polish + English)": "Sprawdzanie pisowni (polski + angielski)",
    "General": "Ogólne",
    "Desktop app for Google Chat on Ubuntu": "Aplikacja Google Chat na pulpit Ubuntu",
    "Unofficial – not affiliated with Google.": "Nieoficjalna – niezwiązana z Google.",
    "Connecting to Google Chat…": "Łączenie z Google Chat…",
    "Loading…": "Wczytywanie…",
    "Downloaded: %s": "Pobrano: %s",
    "Open": "Otwórz",
    "Download failed: %s": "Nie udało się pobrać: %s",
    "No connection – retrying…": "Brak połączenia – ponawiam…",
    "Linux Google Chat keeps running in the tray": "Linux Google Chat działa dalej w zasobniku",
    "Click the tray icon to open the window again.": "Kliknij ikonę w zasobniku, aby znów otworzyć okno.",
    "made by: JGu": "made by: JGu",
    "Supported by Claude": "Supported by Claude",
}


def load_settings():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return {**DEFAULTS, **json.load(f)}
    except Exception:  # noqa: BLE001
        return dict(DEFAULTS)


def save_settings(**kv):
    s = load_settings()
    s.update(kv)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = CONFIG + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CONFIG)
    return s


def system_lang():
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        v = os.environ.get(var, "")
        if v:
            return "pl" if v.lower().startswith("pl") else "en"
    try:
        return "pl" if (locale.getlocale()[0] or "").lower().startswith("pl") else "en"
    except Exception:  # noqa: BLE001
        return "en"


_pref = load_settings().get("language", "auto")
LANG = _pref if _pref in ("pl", "en") else system_lang()


def _(s):
    return PL.get(s, s) if LANG == "pl" else s
