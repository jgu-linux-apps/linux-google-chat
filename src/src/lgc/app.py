"""Linux Google Chat – prototyp 0.0.1: okno GTK4/libadwaita z Google Chat w WebKitGTK 6.

Cel prototypu: sprawdzić, czy logowanie do Google działa we wbudowanym WebKicie. Zawiera już:
- trwałą sesję (ciasteczka i dane strony w ~/.local/share/linux-google-chat – po ponownym starcie
  nie trzeba się logować),
- linki spoza Google otwierane w domyślnej przeglądarce,
- powiadomienia strony jako natywne powiadomienia GNOME,
- licznik nieprzeczytanych z tytułu strony („Chat (3)”) w tytule okna.
Aplikacja nigdy nie widzi hasła – logujesz się bezpośrednio na stronie Google."""
import os
import re
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gio, GLib, Gtk, WebKit  # noqa: E402

APP_ID = "io.github.jaro.LinuxGoogleChat"
VERSION = "0.0.1"
HOME_URL = "https://chat.google.com/"
# niezalogowany użytkownik trafia z chat.google.com na stronę reklamową Workspace – wtedy prosto do logowania
LOGIN_URL = "https://accounts.google.com/ServiceLogin?service=dynamite&continue=https%3A%2F%2Fchat.google.com%2F"
MARKETING = ("https://workspace.google.com/", "https://www.google.com/chat", "https://chat.google.com/download")
DATA_DIR = os.path.join(GLib.get_user_data_dir(), "linux-google-chat")
CACHE_DIR = os.path.join(GLib.get_user_cache_dir(), "linux-google-chat")
# domeny, które zostają w oknie aplikacji (logowanie Google, Chat, załączniki); reszta -> przeglądarka
INTERNAL = re.compile(r"^https://([a-z0-9-]+\.)*(google\.com|googleusercontent\.com|gstatic\.com|google\.pl"
                      r"|youtube\.com|googleapis\.com)(/|$)")
UNREAD = re.compile(r"\((\d+)\)")


class ChatWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Chat")
        self.set_default_size(1200, 800)
        self.unread = 0
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(CACHE_DIR, exist_ok=True)
        session = WebKit.NetworkSession.new(DATA_DIR, CACHE_DIR)
        cookies = session.get_cookie_manager()
        cookies.set_persistent_storage(os.path.join(DATA_DIR, "cookies.sqlite"),
                                       WebKit.CookiePersistentStorage.SQLITE)
        cookies.set_accept_policy(WebKit.CookieAcceptPolicy.NO_THIRD_PARTY)
        self.web = WebKit.WebView(network_session=session)
        st = self.web.get_settings()
        st.set_enable_developer_extras(bool(os.environ.get("LGC_DEVTOOLS")))
        st.set_enable_smooth_scrolling(True)
        st.set_javascript_can_open_windows_automatically(False)
        self.web.connect("decide-policy", self._on_policy)
        self.web.connect("create", self._on_create)
        self.web.connect("permission-request", self._on_permission)
        self.web.connect("show-notification", self._on_notification)
        self.web.connect("notify::title", self._on_title)
        self.web.connect("load-changed", self._on_load)

        tv = Adw.ToolbarView()
        hb = Adw.HeaderBar()
        self.title_lbl = Adw.WindowTitle(title="Chat", subtitle="")
        hb.set_title_widget(self.title_lbl)
        for icon, tip, cb in (("go-home-symbolic", "Chat", lambda *_: self.web.load_uri(HOME_URL)),
                              ("view-refresh-symbolic", "Odśwież (F5)", lambda *_: self.web.reload())):
            b = Gtk.Button(icon_name=icon, tooltip_text=tip)
            b.connect("clicked", cb)
            hb.pack_start(b)
        tv.add_top_bar(hb)
        tv.set_content(self.web)
        self.set_content(tv)
        self.web.load_uri(HOME_URL)

    # ---------------------------------------------------------------- nawigacja
    def _external(self, uri):
        return uri.startswith(("http://", "https://")) and not INTERNAL.match(uri)

    def _on_policy(self, _web, decision, kind):
        if kind == WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_navigation_action().get_request().get_uri()
            if self._external(uri):
                Gio.AppInfo.launch_default_for_uri(uri, None)
                decision.ignore()
                return True
        elif kind == WebKit.PolicyDecisionType.NEW_WINDOW_ACTION:
            uri = decision.get_navigation_action().get_request().get_uri()
            if self._external(uri):
                Gio.AppInfo.launch_default_for_uri(uri, None)
                decision.ignore()
                return True
        return False

    def _on_create(self, _web, action):
        """Nowe okno z Google (np. podgląd załącznika) – w domyślnej przeglądarce."""
        uri = action.get_request().get_uri()
        if uri and uri != "about:blank":
            Gio.AppInfo.launch_default_for_uri(uri, None)
        return None

    # ---------------------------------------------------------------- powiadomienia i licznik
    def _on_permission(self, _web, req):
        if isinstance(req, WebKit.NotificationPermissionRequest):
            req.allow()
            return True
        return False

    def _on_notification(self, _web, note):
        n = Gio.Notification.new(note.get_title() or "Chat")
        n.set_body(note.get_body() or "")
        n.set_default_action("app.show")
        self.get_application().send_notification(f"chat-{note.get_id()}", n)
        return True

    def _on_title(self, *_):
        t = self.web.get_title() or ""
        m = UNREAD.search(t)
        self.unread = int(m.group(1)) if m else 0
        self.title_lbl.set_subtitle(f"{self.unread} nieprzeczytane" if self.unread else "")

    def _on_load(self, _web, event):
        if event == WebKit.LoadEvent.REDIRECTED or event == WebKit.LoadEvent.COMMITTED:
            uri = self.web.get_uri() or ""
            if uri.startswith(MARKETING):
                self.web.load_uri(LOGIN_URL)
                return
        if event == WebKit.LoadEvent.FINISHED:
            print("załadowano:", self.web.get_uri(), "|", self.web.get_title(), flush=True)


class ChatApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.win = None

    def do_startup(self):
        Adw.Application.do_startup(self)
        a = Gio.SimpleAction.new("show", None)
        a.connect("activate", lambda *_: self.win and self.win.present())
        self.add_action(a)

    def do_activate(self):
        if self.win is None:
            self.win = ChatWindow(self)
        self.win.present()


def main():
    return ChatApp().run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
