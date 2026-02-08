import os

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML, to_formatted_text


def select_pubkey(keys, style):
    if not keys:
        return None

    selected = 0

    def menu():
        rows = []
        for i, key in enumerate(keys):
            name = os.path.basename(key)
            arrow = "❯" if i == selected else " "
            if i == selected:
                html = HTML(f"<sel_cursor>{arrow}</sel_cursor> <sel_name>{name}</sel_name>")
            else:
                html = HTML(f"<cursor>{arrow}</cursor> <name>{name}</name>")
            frags = list(to_formatted_text(html))
            frags.append(("", "\n"))
            rows.extend(frags)
        return rows

    body = FormattedTextControl(text=menu, focusable=True)

    root = HSplit([
        Window(FormattedTextControl(HTML("<question>Select SSH public key:</question>")),
               dont_extend_height=True),
        Window(height=1, char=" "),
        Window(body, always_hide_cursor=True),
    ])

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def _(event):
        nonlocal selected
        selected = max(0, selected - 1)

    @kb.add("down")
    @kb.add("j")
    def _(event):
        nonlocal selected
        selected = min(len(keys) - 1, selected + 1)

    @kb.add("enter")
    def _(event):
        event.app.exit(result=keys[selected])

    @kb.add("escape")
    @kb.add("c-c")
    def _(event):
        event.app.exit(result=None)

    app = Application(
        layout=Layout(root),
        key_bindings=kb,
        full_screen=False,
        style=style,
        erase_when_done=True,
    )

    return app.run()
