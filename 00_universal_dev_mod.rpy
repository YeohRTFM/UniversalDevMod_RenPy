# =========================================================
# MOD UNIVERSEL DEV - CHOICE DESCRIPTOR (v2)
# A placer dans game/ : affiche l'effet de chaque choix
# (vert = hausse, rouge = baisse) devant les options de menu.
# =========================================================

default persistent.dev_mod_enabled = True
default persistent.ucd_block_external = True
# Position de la pastille : bl (bas gauche), br, tl, tr
default persistent.ucd_pos = "bl"

init -1000 python:

    # ---------------- REGLAGES ----------------
    # Mettre False pour une version publique du jeu
    _UCD_FORCE_DEVELOPER = True
    # Variables pour lesquelles une hausse est MAUVAISE (affichee en rouge)
    _UCD_INVERTED = ("stress", "corruption", "suspicion")
    _UCD_UP = "#4c4"
    _UCD_DOWN = "#e44"
    _UCD_NEUTRAL = "#ee3"
    _UCD_MAX_DEPTH = 8
    _UCD_TAG = "{#UCD}"
    # -------------------------------------------

    import re as _ucd_re

    try:
        _ucd_str = basestring
    except NameError:
        _ucd_str = str

    _UCD_TRACKED = (bool, int, float, _ucd_str)
    _UCD_PATTERN = _ucd_re.compile(
        r"^\s*(\w+(?:\s*\.\s*\w+)*)\s*(\*\*|//|[+\-*/%])?=(?!=)\s*(.+)$")
    # Evite d'evaluer des expressions a effets de bord (aleatoire, saisie...)
    _UCD_DENY = _ucd_re.compile(r"\b(renpy|random|input)\b")

    def _ucd_eval(expr):
        try:
            return renpy.python.py_eval(expr)
        except Exception:
            return None

    def _ucd_esc(text):
        return text.replace("{", "{{").replace("[", "[[")

    def _ucd_fmt(name, old, new):
        """Retourne le texte colore d'une variable modifiee, ou None."""
        if new == old:
            return None

        new_bool = isinstance(new, bool)
        old_bool = isinstance(old, bool)
        both_num = (not new_bool and not old_bool
                    and isinstance(new, (int, float))
                    and isinstance(old, (int, float)))

        if both_num:
            diff = new - old
            if isinstance(diff, float):
                if abs(diff) < 0.005:
                    return None
                txt = ("%+.2f" % diff).rstrip("0").rstrip(".")
            else:
                txt = "%+d" % diff
            up = diff > 0
        elif new_bool and old_bool:
            txt = "%s" % new
            up = bool(new)
        else:
            value = _ucd_esc(u"%s" % (new,))[:40]
            return u"{color=%s}%s: %s{/color}" % (_UCD_NEUTRAL, name, value)

        if name in _UCD_INVERTED:
            up = not up
        color = _UCD_UP if up else _UCD_DOWN
        return u"{color=%s}%s: %s{/color}" % (color, name, txt)

    class _UcdSim(_object):
        """Simule un bloc de choix et memorise les variables touchees."""

        def __init__(self):
            self.start = _dict()   # valeurs initiales
            self.cur = _dict()     # valeurs simulees
            self.end = None        # None / "return" / "jump"

        def run(self, nodes, depth):
            for node in nodes:
                if self.end:
                    return
                kind = node.__class__
                if kind is renpy.ast.Python:
                    self.python(node)
                elif kind is renpy.ast.If:
                    self.cond(node, depth)
                elif kind is renpy.ast.Label:
                    self.run(node.block, depth)
                elif kind is renpy.ast.Call:
                    self.call(node, depth)
                elif kind is renpy.ast.Jump:
                    self.jump(node, depth)
                elif kind is renpy.ast.Return:
                    self.end = "return"

        def enter(self, name, depth):
            if not name or depth >= _UCD_MAX_DEPTH:
                return
            script = renpy.game.script
            if script.has_label(name):
                self.run(script.lookup(name).block, depth + 1)

        def call(self, node, depth):
            name = _ucd_eval(node.label) if node.expression else node.label
            self.enter(name, depth)
            if self.end == "return":   # fin du call : on reprend apres
                self.end = None

        def jump(self, node, depth):
            name = _ucd_eval(node.target) if node.expression else node.target
            self.enter(name, depth)
            self.end = "jump"

        def cond(self, node, depth):
            for condition, block in node.entries:
                if _ucd_eval(condition):
                    self.run(block, depth)
                    return

        def python(self, node):
            for line in node.code.source.splitlines():
                m = _UCD_PATTERN.match(line)
                if m:
                    self.assign(*m.group(1, 2, 3))

        def assign(self, name, op, expr):
            if _UCD_DENY.search(expr):
                return
            name = _ucd_re.sub(r"\s+", "", name)

            if name not in self.cur:
                value = _ucd_eval(name)
                if value is None or not isinstance(value, _UCD_TRACKED):
                    return
                self.start[name] = value
                self.cur[name] = value

            old = self.cur[name]
            if op:
                new = _ucd_eval("(%r) %s (%s\n)" % (old, op, expr))
            else:
                new = _ucd_eval("(%s\n)" % expr)

            if new is not None and isinstance(new, _UCD_TRACKED):
                self.cur[name] = new

    def _ucd_describe(block):
        sim = _UcdSim()
        sim.run(block, 0)
        parts = _list()
        for name, new in sim.cur.items():
            part = _ucd_fmt(name, sim.start[name], new)
            if part:
                parts.append(part)
        if not parts:
            return ""
        return _UCD_TAG + u" {size=-2}( " + u" | ".join(parts) + u" ){/size}"

    def _ucd_current_menu():
        node = renpy.game.script.namemap.get(renpy.game.context().current)
        if isinstance(node, renpy.ast.Menu):
            return node
        return None

    def _ucd_process_menu():
        menu = _ucd_current_menu()
        if menu is None:
            return

        enabled = bool(persistent.dev_mod_enabled)

        for i, item in enumerate(menu.items):
            label, condition, block = item[0], item[1], item[2]
            if block is None:          # simple legende, pas un choix
                continue

            clean = label.split(_UCD_TAG)[0]
            desc = ""
            if enabled and (condition is None or _ucd_eval(condition)):
                desc = _ucd_describe(block)

            menu.items[i] = (clean + desc,) + tuple(item[1:])

    def _ucd_statement_callback(name):
        try:
            if name and str(name).startswith("menu"):
                _ucd_process_menu()
        except Exception as e:
            renpy.write_log("UCD error: %r" % (e,))

# =========================================================
# BLOCAGE DES ACCES EXTERNES (navigateur + reseau)
# Meilleur effort au niveau Python : ce n'est PAS un bac a sable.
# Pour une isolation reelle, utilise aussi un pare-feu.
# =========================================================
init -1000 python:

    # ---------------- REGLAGES BLOCAGE ----------------
    # Coupe aussi les connexions sortantes (metriques, mises a jour...)
    _UCD_BLOCK_NETWORK = True
    # Hotes autorises malgre le blocage, ex : ("api.mon-jeu.com",)
    _UCD_ALLOWED_HOSTS = ()
    # --------------------------------------------------

    import re as _ucd_re
    import errno as _ucd_errno
    import socket as _ucd_socket
    import webbrowser as _ucd_webbrowser
    import subprocess as _ucd_subprocess
    import os as _ucd_os
    import threading as _ucd_threading

    _ucd_stats = _dict(urls=0, net=0)
    _UCD_URL_RE = _ucd_re.compile(r"(?i)\b(?:https?|ftp)://|\bwww\.")

    def _ucd_blocking():
        # Securise par defaut : en cas de doute, on bloque
        try:
            return renpy.game.persistent.ucd_block_external is not False
        except Exception:
            return True

    def _ucd_report(kind, target):
        _ucd_stats[kind] += 1
        try:
            renpy.write_log("UCD blocked %s: %r" % (kind, target))
        except Exception:
            pass
        if kind == "urls":
            try:
                if _ucd_threading.current_thread().name == "MainThread":
                    renpy.notify(u"Dev Mod : ouverture externe bloquee")
            except Exception:
                pass

    def _ucd_has_url(cmd):
        try:
            if isinstance(cmd, (list, tuple)):
                text = u" ".join([u"%s" % (c,) for c in cmd])
            else:
                text = u"%s" % (cmd,)
        except Exception:
            return False
        return bool(_UCD_URL_RE.search(text))

    def _ucd_host_ok(host):
        if isinstance(host, bytes) and not isinstance(host, str):
            host = host.decode("ascii", "ignore")
        try:
            host = host.lower()
        except Exception:
            return True
        if host in _UCD_ALLOWED_HOSTS:
            return True
        return (host in ("", "localhost", "::1", "0.0.0.0")
                or host.startswith("127."))

    def _ucd_addr_blocked(address):
        if not _UCD_BLOCK_NETWORK or not _ucd_blocking():
            return False
        if not isinstance(address, tuple) or not address:
            return False       # socket unix : local
        return not _ucd_host_ok(address[0])

    def _ucd_net_error(address):
        _ucd_report("net", address)
        return _ucd_socket.error(
            _ucd_errno.ECONNREFUSED,
            "Connexion bloquee par Universal Dev Mod")

    def _ucd_install_blockers():
        # Les originaux sont gardes en variables locales (closures) :
        # fonctionne aussi apres un rechargement Shift+R.
        if getattr(_ucd_socket, "_ucd_patched", False):
            return
        _ucd_socket._ucd_patched = True

        # ---- Navigateur ----
        def wrap_browser(orig):
            def wrapper(url, *args, **kwargs):
                if _ucd_blocking():
                    _ucd_report("urls", url)
                    return False
                return orig(url, *args, **kwargs)
            return wrapper

        for name in ("open", "open_new", "open_new_tab"):
            setattr(_ucd_webbrowser, name,
                    wrap_browser(getattr(_ucd_webbrowser, name)))

        orig_get = _ucd_webbrowser.get

        class BrowserProxy(_object):
            def __init__(self, real):
                self._real = real

            def open(self, url, *args, **kwargs):
                if _ucd_blocking():
                    _ucd_report("urls", url)
                    return False
                return self._real.open(url, *args, **kwargs)

            def open_new(self, url):
                return self.open(url)

            def open_new_tab(self, url):
                return self.open(url)

            def __getattr__(self, attr):
                return getattr(self._real, attr)

        def get(*args, **kwargs):
            return BrowserProxy(orig_get(*args, **kwargs))

        _ucd_webbrowser.get = get

        # ---- Commandes systeme contenant une URL ----
        orig_popen = _ucd_subprocess.Popen

        class BlockedPopen(orig_popen):
            def __init__(self, args, *a, **k):
                if _ucd_blocking() and _ucd_has_url(args):
                    _ucd_report("urls", args)
                    raise OSError(_ucd_errno.EACCES,
                                  "Ouverture bloquee par Universal Dev Mod")
                orig_popen.__init__(self, args, *a, **k)

        _ucd_subprocess.Popen = BlockedPopen

        orig_system = _ucd_os.system

        def system(command):
            if _ucd_blocking() and _ucd_has_url(command):
                _ucd_report("urls", command)
                return 1
            return orig_system(command)

        _ucd_os.system = system

        if hasattr(_ucd_os, "startfile"):
            orig_startfile = _ucd_os.startfile

            def startfile(path, *a, **k):
                if _ucd_blocking() and _ucd_has_url(path):
                    _ucd_report("urls", path)
                    return None
                return orig_startfile(path, *a, **k)

            _ucd_os.startfile = startfile

        # ---- Reseau ----
        orig_connect = _ucd_socket.socket.connect
        orig_connect_ex = _ucd_socket.socket.connect_ex
        orig_sendto = _ucd_socket.socket.sendto
        orig_getaddrinfo = _ucd_socket.getaddrinfo

        def connect(self, address):
            if _ucd_addr_blocked(address):
                raise _ucd_net_error(address)
            return orig_connect(self, address)

        def connect_ex(self, address):
            if _ucd_addr_blocked(address):
                _ucd_report("net", address)
                return _ucd_errno.ECONNREFUSED
            return orig_connect_ex(self, address)

        def sendto(self, *args):
            if args and _ucd_addr_blocked(args[-1]):
                raise _ucd_net_error(args[-1])
            return orig_sendto(self, *args)

        def getaddrinfo(host, *args, **kwargs):
            if (host is not None and _UCD_BLOCK_NETWORK
                    and _ucd_blocking() and not _ucd_host_ok(host)):
                _ucd_report("net", host)
                raise _ucd_socket.gaierror(
                    _ucd_socket.EAI_NONAME,
                    "Resolution bloquee par Universal Dev Mod")
            return orig_getaddrinfo(host, *args, **kwargs)

        _ucd_socket.socket.connect = connect
        _ucd_socket.socket.connect_ex = connect_ex
        _ucd_socket.socket.sendto = sendto
        _ucd_socket.getaddrinfo = getaddrinfo

    _ucd_install_blockers()

# =========================================================
# INTERFACE : pastille ronde + fenetre de reglages
# La pastille est generee en code (PNG cree en memoire) :
# aucun fichier image a ajouter au jeu.
# =========================================================
init -1000 python:

    # ---------------- REGLAGES INTERFACE ----------------
    _UCD_DOT_SIZE = 26          # diametre de la pastille (pixels)
    _UCD_MARGIN = 12            # marge par rapport au bord de l'ecran
    _UCD_DOT_IDLE_ALPHA = 110   # opacite au repos (0-255) : discret
    _UCD_FONT = "DejaVuSans.ttf"   # police fournie avec Ren'Py (accents OK)
    # ----------------------------------------------------

    import zlib as _ucd_zlib
    import struct as _ucd_struct

    def _ucd_circle_png(size, rgb, alpha):
        """PNG RGBA d'un disque anti-aliase avec un fin liseré clair."""
        r = size / 2.0
        rows = []
        for y in range(size):
            row = bytearray([0])
            for x in range(size):
                d = ((x + 0.5 - r) ** 2 + (y + 0.5 - r) ** 2) ** 0.5
                cover = max(0.0, min(1.0, r - d))
                col = (235, 235, 235) if d > r - 2.0 else rgb
                row.extend((col[0], col[1], col[2], int(alpha * cover)))
            rows.append(bytes(row))
        raw = b"".join(rows)

        def chunk(tag, data):
            body = tag + data
            return (_ucd_struct.pack(">I", len(data)) + body
                    + _ucd_struct.pack(">I", _ucd_zlib.crc32(body) & 0xffffffff))

        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", _ucd_struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", _ucd_zlib.compress(raw, 9))
                + chunk(b"IEND", b""))

    _UCD_DOT = _dict()
    for _state, _rgb in (("on", (60, 190, 90)), ("off", (150, 150, 150))):
        for _mode, _alpha in (("idle", _UCD_DOT_IDLE_ALPHA), ("hover", 255)):
            _UCD_DOT[_state + "_" + _mode] = renpy.display.im.Data(
                _ucd_circle_png(_UCD_DOT_SIZE, _rgb, _alpha),
                "ucd_dot_%s_%s.png" % (_state, _mode))

    # Etat de la fenetre (non sauvegarde : refermee a chaque lancement)
    _ucd_ui = _dict(open=False)

    def ucd_toggle_panel():
        _ucd_ui["open"] = not _ucd_ui["open"]
        renpy.restart_interaction()

    def ucd_set_pos(pos):
        persistent.ucd_pos = pos
        renpy.restart_interaction()

style ucd_text is default:
    font "DejaVuSans.ttf"
    size 15
    color "#ffffff"
    outlines []

style ucd_button is default:
    background None
    padding (4, 2)
    xminimum 0
    yminimum 0

style ucd_button_text is ucd_text:
    idle_color "#cccccc"
    hover_color "#ffffff"
    selected_idle_color "#ffffff"
    selected_hover_color "#ffffff"

init 999 python:
    # Apres options.rpy, pour ne pas etre ecrase par le jeu
    if _UCD_FORCE_DEVELOPER:
        config.developer = True
        config.console = True

init 1000 python:

    # Evite les doublons apres un rechargement (Shift+R)
    config.statement_callbacks[:] = [
        c for c in config.statement_callbacks
        if getattr(c, "__name__", "") != "_ucd_statement_callback"
    ]
    config.statement_callbacks.append(_ucd_statement_callback)

    if "dev_mod_toggle_button" not in config.overlay_screens:
        config.overlay_screens.append("dev_mod_toggle_button")

    # L'action d'ecran OpenURL est aussi neutralisee (couche supplementaire)
    if not getattr(OpenURL, "_ucd", False):
        _ucd_RealOpenURL = OpenURL

        class _UcdOpenURL(_ucd_RealOpenURL):
            _ucd = True

            def __call__(self):
                if _ucd_blocking():
                    _ucd_report("urls", getattr(self, "url", "?"))
                    return None
                return _ucd_RealOpenURL.__call__(self)

        OpenURL = _UcdOpenURL

    def toggle_block_external():
        persistent.ucd_block_external = not persistent.ucd_block_external
        renpy.restart_interaction()

    def toggle_dev_mod():
        persistent.dev_mod_enabled = not persistent.dev_mod_enabled
        try:
            # Nettoie / met a jour le menu courant (visible au prochain affichage)
            _ucd_process_menu()
        except Exception as e:
            renpy.write_log("UCD toggle error: %r" % (e,))
        renpy.restart_interaction()

screen dev_mod_toggle_button():
    zorder 1000

    $ ucd_pos = persistent.ucd_pos or "bl"
    $ is_left = ucd_pos in ("bl", "tl")
    $ is_top = ucd_pos in ("tl", "tr")

    vbox:
        xalign (0.0 if is_left else 1.0)
        yalign (0.0 if is_top else 1.0)
        xoffset (_UCD_MARGIN if is_left else -_UCD_MARGIN)
        yoffset (_UCD_MARGIN if is_top else -_UCD_MARGIN)
        spacing 6

        if is_top:
            use ucd_dot(is_left)
            if _ucd_ui["open"]:
                use ucd_panel(is_left)
        else:
            if _ucd_ui["open"]:
                use ucd_panel(is_left)
            use ucd_dot(is_left)

screen ucd_dot(is_left):
    $ state = "on" if persistent.dev_mod_enabled else "off"
    imagebutton:
        xalign (0.0 if is_left else 1.0)
        idle (_UCD_DOT[state + "_idle"])
        hover (_UCD_DOT[state + "_hover"])
        action Function(ucd_toggle_panel)

screen ucd_panel(is_left):
    $ ucd_pos = persistent.ucd_pos or "bl"
    $ block_on = persistent.ucd_block_external is not False
    $ blocked_count = _ucd_stats["urls"] + _ucd_stats["net"]

    frame:
        xalign (0.0 if is_left else 1.0)
        background "#000000e6"
        padding (14, 10)
        xminimum 0
        yminimum 0

        vbox:
            spacing 4

            text "Universal Dev Mod" style "ucd_text" size 17 bold True

            null height 4

            textbutton ("Annotations des choix : " + ("ON" if persistent.dev_mod_enabled else "OFF")):
                style "ucd_button"
                text_style "ucd_button_text"
                text_idle_color ("#77ee77" if persistent.dev_mod_enabled else "#ee7777")
                action Function(toggle_dev_mod)

            textbutton ("Accès externes : " + ("BLOQUÉS" if block_on else "LIBRES") + " (" + str(blocked_count) + ")"):
                style "ucd_button"
                text_style "ucd_button_text"
                text_idle_color ("#77ee77" if block_on else "#ee7777")
                action Function(toggle_block_external)

            null height 6

            text "Position de la pastille" style "ucd_text" size 13 color "#aaaaaa"

            grid 2 2:
                spacing 2
                textbutton (("> " if ucd_pos == "tl" else "   ") + "Haut gauche"):
                    style "ucd_button"
                    text_style "ucd_button_text"
                    selected (ucd_pos == "tl")
                    action Function(ucd_set_pos, "tl")
                textbutton (("> " if ucd_pos == "tr" else "   ") + "Haut droite"):
                    style "ucd_button"
                    text_style "ucd_button_text"
                    selected (ucd_pos == "tr")
                    action Function(ucd_set_pos, "tr")
                textbutton (("> " if ucd_pos == "bl" else "   ") + "Bas gauche"):
                    style "ucd_button"
                    text_style "ucd_button_text"
                    selected (ucd_pos == "bl")
                    action Function(ucd_set_pos, "bl")
                textbutton (("> " if ucd_pos == "br" else "   ") + "Bas droite"):
                    style "ucd_button"
                    text_style "ucd_button_text"
                    selected (ucd_pos == "br")
                    action Function(ucd_set_pos, "br")

            null height 4

            textbutton "Fermer":
                style "ucd_button"
                text_style "ucd_button_text"
                action Function(ucd_toggle_panel)
