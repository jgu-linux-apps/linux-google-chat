# linux-google-chat — Linux Google Chat

**Current version: 0.1.0 (2026-11-13)**

Google Chat in its own window on Ubuntu – a light, native GTK4/libadwaita app with the Google Chat web page inside
(WebKitGTK). It stays signed in, lives in the tray, counts unread messages on the dock icon and shows GNOME
notifications that open the right conversation.

**Unofficial – not affiliated with, endorsed or sponsored by Google.** "Google Chat" is a trademark of Google LLC.
The app icon is our own design. The interface is available in **English and Polish**.

## Features

- **Google Chat in a native window**: our own header bar (Home, Reload, Do Not Disturb, menu) with the unread count
  under the title; the Chat page itself is the real one from Google.
- **Stays signed in**: you sign in once on Google's own page – the app never sees or stores your password. The session
  (cookies, site data) is kept in `~/.local/share/linux-google-chat`.
- **Tray icon** with a dot for new messages and a menu: Show Chat (with the count), Do Not Disturb, Preferences, Quit.
  Closing the window keeps the app running in the tray (can be turned off). Needs the AppIndicator extension, which
  Ubuntu has by default.
- **Unread counter on the dock icon** (Ubuntu Dock).
- **GNOME notifications** for new messages; clicking one opens the window on that conversation.
- **Do Not Disturb**: one click mutes notifications (also from the tray); shown under the window title.
- **Downloads** go straight to your Downloads folder (no overwriting – a number is added), with an *Open* button.
- **Links** outside Google open in your default browser.
- **Spell checking** in Polish and English (uses the `hunspell-pl` / `hunspell-en-us` dictionaries).
- **Zoom**: Ctrl + / Ctrl − / Ctrl 0, remembered between runs.
- **Themes** (menu → Theme, or Preferences): **System** (standard Ubuntu/GNOME look), **Aurora** (pastel glass in light
  mode, an aurora glow on deep navy in dark mode – follows the system light/dark setting; violet → cyan gradient on the
  main buttons) and **Studio Pro** (dark, ergonomic: graphite, one muted amber accent, tabular digits).
- **App icon follows the system light/dark theme** – also while the app is closed: a tiny session service started
  with GNOME waits for the theme-change signal and swaps the icon in the dock and app grid at once.
- **Start with the system** in the background (only the tray icon), splash screen with the version, About with the
  project link.

## Installation

Download the latest `linux-google-chat_<version>_all.deb` from the
[Releases page](https://github.com/jgu-linux-apps/linux-google-chat/releases/latest):

```bash
sudo apt install ./linux-google-chat_<version>_all.deb
```

Requirements: Ubuntu 24.04+ (libadwaita ≥ 1.5, WebKitGTK 6). Dependencies install automatically.

```bash
linux-google-chat              # open
linux-google-chat --hidden     # start in the tray only
linux-google-chat --version
```

## Keyboard shortcuts

| Keys | Action |
|---|---|
| F5 | Reload |
| Ctrl + / Ctrl − / Ctrl 0 | Zoom in / out / actual size |
| Ctrl , | Preferences |
| Ctrl Q | Quit |

## Building from source

The source code lives in the repository's `src/` folder; `.deb` packages are published on
[Releases](https://github.com/jgu-linux-apps/linux-google-chat/releases). Pushing a `vX.Y.Z` tag that matches `VERSION`
in `src/src/lgc/__init__.py` runs GitHub Actions, which build the package and publish the release. Inside `src/`:

```bash
python3 tools/make_icons.py data/icons     # app and tray icons
./packaging/build-deb.sh                   # -> dist/linux-google-chat_<version>_all.deb
./bin/linux-google-chat                    # run without installing
```

Layout: `src/lgc/window.py` (window, WebKit session, links, downloads, zoom), `src/lgc/app.py` (splash, tray, dock
counter, notifications, Do Not Disturb, About), `src/lgc/themes.py`, `src/lgc/prefs.py`, `src/lgc/desktop.py` (dock
counter, autostart, light/dark icon service), `src/lgc/tray.py` (StatusNotifierItem over D-Bus), `src/lgc/i18n.py`.

## Version history

- **0.1.0** (2026-11-13) – first version.

---

made by: JGu · Supported by Claude
