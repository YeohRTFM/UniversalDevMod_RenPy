# =========================================================
# MOD UNIVERSEL DEV, CONSOLE & CHOICE DESCRIPTOR
# =========================================================

init -1000 python:

    # Variable globale de sauvegarde du mod
    if not hasattr(persistent, "dev_mod_enabled"):
        persistent.dev_mod_enabled = True

    config.developer = True
    config.console = True

    class _ZLZK_UCD(_object):

        class _mod(_object):
            def __init__(self):
                from collections import OrderedDict
                import sys
                import re
                self.OrderedDict = OrderedDict
                self.sys = sys
                self.re = re

        class _ref(_object):
            def __init__(self):
                self.py_eval = renpy.python.py_eval
                self.If = renpy.ast.If
                self.Call = renpy.ast.Call
                self.Jump = renpy.ast.Jump
                self.Label = renpy.ast.Label
                self.Python = renpy.ast.Python
                self.Return = renpy.ast.Return
                self.script = renpy.game.script
                self.context = renpy.game.context

        class _FlagExtractor(_object):
            def __init__(self, mod):
                self.OrderedDict = mod._mod.OrderedDict
                self.store_eval = mod._safe_store_eval
                self.pattern = mod._pattern
                self.re = mod._mod.re
                self.If = mod._ref.If
                self.Call = mod._ref.Call
                self.Jump = mod._ref.Jump
                self.Label = mod._ref.Label
                self.Python = mod._ref.Python
                self.Return = mod._ref.Return
                self.script = mod._ref.script

            def __call__(self, block):
                s_type = (bool,)
                try:
                    s_type += (basestring,)
                except NameError:
                    s_type += (str,)
                n_type = (int, float)

                self.s_type = s_type
                self.n_type = n_type
                self.flags = self.OrderedDict()
                self.fvals = _dict()
                self.ajump = False

                self.process_block(block)
                return self.process_flags()

            def process_flags(self):
                rv = _list()
                for k, v in self.flags.items():
                    if isinstance(v, self.s_type):
                        if v != self.fvals[k]:
                            rv.append((k, v))
                    elif isinstance(v, self.n_type):
                        if v:
                            rv.append((k, v))
                return rv

            def process_flag(self, varname, expre_value, store_value):
                if isinstance(expre_value, (self.s_type, type(None))):
                    self.flags[varname] = expre_value
                elif isinstance(expre_value, self.n_type):
                    if isinstance(store_value, self.n_type):
                        expre_value -= store_value
                    self.flags[varname] = expre_value

            def process_match(self, varnames, operator, valexpre):
                if "renpy.input" in valexpre:
                    return
                varnames = varnames.split(",")
                if len(varnames) == 1:
                    varname = varnames[0]
                    if varname in self.flags:
                        store_value = self.flags[varname]
                    else:
                        store_value = self.store_eval(varname)
                        self.flags[varname] = store_value
                        self.fvals[varname] = store_value

                    if operator == "=":
                        expre_value = self.store_eval(valexpre)
                    else:
                        eval_str = str(store_value) + " " + str(operator[0]) + " " + str(valexpre)
                        expre_value = self.store_eval(eval_str)
                    self.process_flag(varname, expre_value, store_value)

            def process_python(self, node):
                for line in node.code.source.splitlines():
                    match = self.re.match(self.pattern, line)
                    if match:
                        self.process_match(*match.group(1, 2, 3))

            def process_if(self, node):
                for condition, block in node.entries:
                    if self.store_eval(condition):
                        return self.process_block(block)

            def process_label(self, node):
                self.process_block(node.block)

            def process_label_name(self, label):
                if label and self.script.has_label(label):
                    self.process_label(self.script.lookup(label))

            def process_call(self, node):
                lbl = self.store_eval(node.label) if node.expression else node.label
                self.process_label_name(lbl)

            def process_jump(self, node):
                tgt = self.store_eval(node.target) if node.expression else node.target
                if not self.ajump:
                    self.ajump = True
                    self.process_label_name(tgt)

            def process_block(self, nodes):
                for node in nodes:
                    node_type = node.__class__
                    if node_type is self.Python:
                        self.process_python(node)
                    elif node_type is self.If:
                        self.process_if(node)
                    elif node_type is self.Label:
                        self.process_label(node)
                    elif node_type is self.Call:
                        self.process_call(node)
                    elif node_type is self.Jump:
                        self.process_jump(node)
                    elif node_type is self.Return:
                        return

        _mod = _mod()
        _ref = _ref()
        tag = "{#UCD}"
        _pattern = _mod.re.compile(r"^\s*(\w+(?:\s*\.\s*\w*)*(?:\s*,\s*\w+(?:\s*\.\s*\w*)*)*)\s*([+\-*/]?=)(?!=)\s*(.+)$")

        def __init__(self):
            self._FlagExtractor = self._FlagExtractor(self)

        def __call__(self, name):
            if name.startswith("menu"):
                self.process_menu()

        @classmethod
        def _safe_store_eval(cls, code, globals=None, locals=None):
            if globals is None:
                globals = cls._mod.sys._getframe(2).f_globals
            try:
                return cls._ref.py_eval(code, globals, locals)
            except:
                return None

        def process_menu(self):
            script, context = self._ref.script, self._ref.context
            menu = script.namemap.get(context().current)
            if not menu:
                return
            
            # Si le mod est DESACTIVE, on retire proprement les annotations
            if not persistent.dev_mod_enabled:
                for i, (label, condition, block) in enumerate(menu.items):
                    if block is None:
                        continue
                    clean_label = label.split(self.tag)[0]
                    menu.items[i] = (clean_label, condition, block)
                return

            # Si le mod est ACTIVE, on extrait et injecte les annotations
            data = _dict()
            for i, (label, condition, block) in enumerate(menu.items):
                if block and self._safe_store_eval(condition):
                    data[i] = self._FlagExtractor(block)

            for i, (label, condition, block) in enumerate(menu.items):
                if block is None:
                    continue
                flags = data.get(i, None)
                if flags:
                    str_flags = []
                    for var, val in flags:
                        sign = "+" if isinstance(val, (int, float)) and val > 0 else ""
                        str_flags.append(str(var) + ": " + sign + str(val))
                    
                    desc = self.tag + " {color=#ee3}{size=-2}( " + " | ".join(str_flags) + " ){/size}{/color}"
                else:
                    desc = ""
                
                clean_label = label.split(self.tag)[0]
                menu.items[i] = (clean_label + desc, condition, block)

    _ZLZK_UCD = _ZLZK_UCD()

init 1000 python:
    _config.statement_callbacks.append(_ZLZK_UCD)

    def toggle_dev_mod():
        persistent.dev_mod_enabled = not persistent.dev_mod_enabled
        config.developer = persistent.dev_mod_enabled
        config.console = persistent.dev_mod_enabled
        
        # Force le ré-affichage instantané du menu actuel
        _ZLZK_UCD.process_menu()
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

init python:
    config.overlay_screens.append("dev_mod_toggle_button")
