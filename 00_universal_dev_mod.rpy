# =========================================================
# MOD UNIVERSEL DEV - CHOICE DESCRIPTOR (v2)
# A placer dans game/ : affiche l'effet de chaque choix
# (vert = hausse, rouge = baisse) devant les options de menu.
# =========================================================

default persistent.dev_mod_enabled = True

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
    frame:
        align (0.99, 0.01)
        background "#000000aa"
        padding (8, 5)
        textbutton ("Dev Mod: " + ("ON" if persistent.dev_mod_enabled else "OFF")):
            action Function(toggle_dev_mod)
            text_size 14
            text_color ("#00FF00" if persistent.dev_mod_enabled else "#FF0000")
