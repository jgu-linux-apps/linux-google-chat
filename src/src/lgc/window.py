"""Okno główne: nasz pasek u góry, w środku Google Chat w WebKitGTK 6.

Aplikacja nigdy nie widzi hasła – logowanie odbywa się na stronie Google. Sesja (ciasteczka, dane strony)
zostaje w ~/.local/share/linux-google-chat, więc po ponownym uruchomieniu nie trzeba się logować."""
import base64
import json
import os
import re

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk, WebKit  # noqa: E402

from .i18n import _, load_settings, save_settings  # noqa: E402

HOME_URL = "https://chat.google.com/"
# niezalogowany użytkownik trafia z chat.google.com na stronę reklamową Workspace – wtedy prosto do logowania
LOGIN_URL = "https://accounts.google.com/ServiceLogin?service=dynamite&continue=https%3A%2F%2Fchat.google.com%2F"
MARKETING = ("https://workspace.google.com/", "https://www.google.com/chat", "https://chat.google.com/download")
DATA_DIR = os.path.join(GLib.get_user_data_dir(), "linux-google-chat")
CACHE_DIR = os.path.join(GLib.get_user_cache_dir(), "linux-google-chat")
# domeny, które zostają w oknie (logowanie Google, Chat, załączniki); reszta -> domyślna przeglądarka
INTERNAL = re.compile(r"^https://([a-z0-9-]+\.)*(google\.com|googleusercontent\.com|gstatic\.com|google\.pl"
                      r"|youtube\.com|googleapis\.com)(/|$)")
MAX_FILE = 200 * 1024 * 1024
# finds the focused element (through same-origin iframes) and pastes the files there
INJECT_JS = """
const f = JSON.parse(j), t = new DataTransfer();
for (const x of f) t.items.add(new File([Uint8Array.from(atob(x.d), c => c.charCodeAt(0))], x.n, {type: x.t}));
let doc = document, el = doc.activeElement;
while (el && el.tagName === 'IFRAME') { try { doc = el.contentDocument; el = doc.activeElement; } catch (e) { break; } }
if (!el || el === doc.body) el = doc.querySelector('[contenteditable=true], textarea') || doc.body;
console.log('LGC paste ->', el.tagName, f.length);
el.dispatchEvent(new ClipboardEvent('paste', {clipboardData: t, bubbles: true, cancelable: true}));
"""
UNREAD = re.compile(r"\((\d+)\)")
ZOOM_STEPS = (0.67, 0.75, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0)


class ChatWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Chat")
        self.app = app
        self.set_default_size(1240, 820)
        self.unread = 0
        self._retry = 0
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(CACHE_DIR, exist_ok=True)
        cfg = load_settings()

        session = WebKit.NetworkSession.new(DATA_DIR, CACHE_DIR)
        cookies = session.get_cookie_manager()
        cookies.set_persistent_storage(os.path.join(DATA_DIR, "cookies.sqlite"), WebKit.CookiePersistentStorage.SQLITE)
        cookies.set_accept_policy(WebKit.CookieAcceptPolicy.NO_THIRD_PARTY)
        session.connect("download-started", self._on_download)
        ctx = WebKit.WebContext.get_default()
        ctx.set_spell_checking_languages(["pl_PL", "en_US"])
        ctx.set_spell_checking_enabled(bool(cfg["spellcheck"]))

        self.web = WebKit.WebView(network_session=session)
        st = self.web.get_settings()
        st.set_enable_developer_extras(bool(os.environ.get("LGC_DEVTOOLS")))
        st.set_enable_smooth_scrolling(True)
        ucm = self.web.get_user_content_manager()
        if os.environ.get("LGC_DEBUG"):
            st.set_enable_write_console_messages_to_stdout(True)
            ucm.add_script(WebKit.UserScript.new(
                "for(const t of ['paste','dragenter','drop'])document.addEventListener(t,e=>{const d=e.clipboardData||"
                "e.dataTransfer;console.log('LGC',t,location.host,e.isTrusted,d&&[...d.types].join(','),"
                "d&&d.files.length,e.target.tagName)},true)",
                WebKit.UserContentInjectedFrames.ALL_FRAMES, WebKit.UserScriptInjectionTime.START, None, None))
        st.set_javascript_can_open_windows_automatically(False)
        st.set_javascript_can_access_clipboard(True)  # Chat pastes images via navigator.clipboard
        self.web.set_zoom_level(float(cfg["zoom"]))
        self.web.connect("decide-policy", self._on_policy)
        self.web.connect("create", self._on_create)
        self.web.connect("permission-request", self._on_permission)
        self.web.connect("show-notification", self._on_notification)
        self.web.connect("notify::title", self._on_title)
        self.web.connect("load-changed", self._on_load)
        self.web.connect("load-failed", self._on_load_failed)
        # WebKitGTK hands the page an empty paste event for images – we paste them ourselves
        keys = Gtk.EventControllerKey(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self._on_key)
        self.web.add_controller(keys)

        # ---- pasek u góry
        hb = Adw.HeaderBar()
        self.title_w = Adw.WindowTitle(title="Chat", subtitle="")
        hb.set_title_widget(self.title_w)
        for icon, tip, cb in (("go-home-symbolic", _("Home"), lambda *_: self.web.load_uri(HOME_URL)),
                              ("view-refresh-symbolic", _("Reload (F5)"), lambda *_: self.web.reload())):
            b = Gtk.Button(icon_name=icon, tooltip_text=tip)
            b.connect("clicked", cb)
            hb.pack_start(b)
        menu = Gio.Menu()
        look = Gio.Menu()
        for k, label in (("system", _("System")), ("aurora", _("Aurora")), ("pro", _("Studio Pro"))):
            look.append(label, f"app.theme::{k}")
        menu.append_submenu(_("Theme"), look)
        zoom = Gio.Menu()
        zoom.append(_("Zoom in"), "app.zoom-in")
        zoom.append(_("Zoom out"), "app.zoom-out")
        zoom.append(_("Reset zoom"), "app.zoom-reset")
        menu.append_submenu(_("Zoom"), zoom)
        sec = Gio.Menu()
        sec.append(_("Preferences"), "app.preferences")
        sec.append(_("About Linux Google Chat"), "app.about")
        sec.append(_("Quit"), "app.quit")
        menu.append_section(None, sec)
        mb = Gtk.MenuButton(icon_name="open-menu-symbolic", menu_model=menu, primary=True, tooltip_text=_("Main menu"))
        hb.pack_end(mb)
        self.dnd_btn = Gtk.ToggleButton(icon_name="weather-clear-night-symbolic", tooltip_text=_("Do Not Disturb"),
                                        action_name="app.dnd")
        hb.pack_end(self.dnd_btn)

        self.toasts = Adw.ToastOverlay(child=self.web)
        # files dragged from Nautilus: WebKit hides their paths from the page, so we take the drop ourselves
        # (capture phase on the parent wins over WebKit's own drop target; text drags still go to the page)
        drop = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        drop.connect("drop", self._on_drop)
        self.toasts.add_controller(drop)
        tv = Adw.ToolbarView()
        tv.add_top_bar(hb)
        tv.set_content(self.toasts)
        self.set_content(tv)
        self.connect("close-request", self._on_close)
        self.web.load_uri(HOME_URL)

    # ---------------------------------------------------------------- nawigacja
    @staticmethod
    def _external(uri):
        return uri.startswith(("http://", "https://")) and not INTERNAL.match(uri)

    def _on_policy(self, _web, decision, kind):
        if kind in (WebKit.PolicyDecisionType.NAVIGATION_ACTION, WebKit.PolicyDecisionType.NEW_WINDOW_ACTION):
            uri = decision.get_navigation_action().get_request().get_uri()
            if self._external(uri):
                Gio.AppInfo.launch_default_for_uri(uri, None)
                decision.ignore()
                return True
        return False

    def _on_create(self, _web, action):
        """Nowe okno ze strony (np. podgląd załącznika, spotkanie Meet) – w domyślnej przeglądarce."""
        uri = action.get_request().get_uri()
        if uri and uri != "about:blank":
            Gio.AppInfo.launch_default_for_uri(uri, None)
        return None

    def _on_load(self, _web, event):
        if event in (WebKit.LoadEvent.REDIRECTED, WebKit.LoadEvent.COMMITTED):
            if (self.web.get_uri() or "").startswith(MARKETING):
                self.web.load_uri(LOGIN_URL)
                return
        if event == WebKit.LoadEvent.FINISHED:
            self._retry = 0
            self.app.page_ready()

    def _on_load_failed(self, _web, _event, uri, error):
        if error.matches(WebKit.NetworkError.quark(), WebKit.NetworkError.CANCELLED):
            return False
        self._retry += 1
        self.toast(_("No connection – retrying…"))
        GLib.timeout_add_seconds(min(60, 5 * self._retry), lambda: (self.web.load_uri(HOME_URL), False)[1])
        return False

    # ---------------------------------------------------------------- pobieranie
    def _on_download(self, _session, download):
        folder = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) or os.path.expanduser("~")

        def decide(d, name):
            base, ext = os.path.splitext(os.path.basename(name) or "plik")
            path, n = os.path.join(folder, base + ext), 1
            while os.path.exists(path):
                path, n = os.path.join(folder, f"{base} ({n}){ext}"), n + 1
            d.set_destination(path)
            return True
        download.connect("decide-destination", decide)
        download.connect("finished", lambda d: self.toast(_("Downloaded: %s") % os.path.basename(
            d.get_destination() or ""), d.get_destination()))
        download.connect("failed", lambda d, err: self.toast(_("Download failed: %s") % err.message))

    # ---------------------------------------------------------------- powiadomienia i licznik
    # ---------------------------------------------------------------- wklejanie obrazów
    def _on_key(self, _ctl, keyval, _code, state):
        if not (state & Gdk.ModifierType.CONTROL_MASK) or Gdk.keyval_to_lower(keyval) != Gdk.KEY_v:
            return False
        cb = self.get_clipboard()
        fm = cb.get_formats()
        if os.environ.get("LGC_DEBUG"):
            print("LGC ctrl+v formats:", fm.to_string(), flush=True)
        if fm.contain_gtype(Gdk.FileList):  # files copied in Nautilus: the page would only get their path as text
            cb.read_value_async(Gdk.FileList, GLib.PRIORITY_DEFAULT, None, self._on_file_list)
            return True
        if fm.contain_mime_type("text/plain") or fm.contain_mime_type("text/uri-list") \
                or not (fm.contain_gtype(Gdk.Texture) or any(m.startswith("image/") for m in fm.get_mime_types() or [])):
            return False
        cb.read_texture_async(None, self._on_texture)
        return True

    def _on_texture(self, cb, res):
        try:
            tex = cb.read_texture_finish(res)
        except GLib.Error:
            tex = None
        if tex is not None:
            self._inject_files([("image.png", "image/png", tex.save_to_png_bytes().get_data())])

    def _on_file_list(self, cb, res):
        try:
            files = cb.read_value_finish(res).get_files()
        except GLib.Error:
            return
        self._paste_gfiles(files)

    def _on_drop(self, _target, value, _x, _y):
        self._paste_gfiles(value.get_files())
        return True

    def _paste_gfiles(self, gfiles):
        out = []
        for gf in gfiles:
            path = gf.get_path()
            if not path or not os.path.isfile(path) or os.path.getsize(path) > MAX_FILE:
                continue
            mime = Gio.content_type_get_mime_type(Gio.content_type_guess(path, None)[0]) or "application/octet-stream"
            with open(path, "rb") as fh:
                out.append((os.path.basename(path), mime, fh.read()))
        if out:
            self._inject_files(out)

    def _inject_files(self, files):
        # nested arrays are not accepted as JS arguments – pass the list as one JSON string
        arg = GLib.Variant("a{sv}", {"j": GLib.Variant("s", json.dumps(
            [{"n": n, "t": t, "d": base64.b64encode(d).decode()} for n, t, d in files]))})
        self.web.call_async_javascript_function(INJECT_JS, -1, arg, None, None, None, None)

    def _on_permission(self, _web, req):
        # ClipboardPermissionRequest = the page reading the clipboard (pasting images); unhandled it is denied
        if isinstance(req, (WebKit.NotificationPermissionRequest, WebKit.ClipboardPermissionRequest)):
            req.allow()
            return True
        return False

    def _on_notification(self, _web, note):
        self.app.web_notification(note)
        return True

    def _on_title(self, *_):
        m = UNREAD.search(self.web.get_title() or "")
        self.unread = int(m.group(1)) if m else 0
        self.update_subtitle()
        self.app.set_unread(self.unread)

    def update_subtitle(self):
        parts = []
        if self.unread:
            parts.append(_("%d unread") % self.unread)
        if self.app.dnd:
            parts.append(_("Do Not Disturb"))
        self.title_w.set_subtitle(" · ".join(parts))

    # ---------------------------------------------------------------- powiększenie
    def zoom(self, step):
        cur = self.web.get_zoom_level()
        if step == 0:
            z = 1.0
        else:
            bigger = [s for s in ZOOM_STEPS if s > cur + 0.001]
            smaller = [s for s in ZOOM_STEPS if s < cur - 0.001]
            z = (bigger[0] if bigger else cur) if step > 0 else (smaller[-1] if smaller else cur)
        self.web.set_zoom_level(z)
        save_settings(zoom=z)
        self.toast(f"{_('Zoom')}: {round(z * 100)}%")

    # ---------------------------------------------------------------- reszta
    def toast(self, text, open_path=None):
        t = Adw.Toast(title=text, timeout=4)
        if open_path:
            t.set_button_label(_("Open"))
            t.connect("button-clicked", lambda *_: Gio.AppInfo.launch_default_for_uri(
                Gio.File.new_for_path(open_path).get_uri(), None))
        self.toasts.add_toast(t)

    def _on_close(self, *_):
        return self.app.on_window_close()
