from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML, to_formatted_text


def make_line(idx, con, selected):
    name = con["resolved_name"]
    ip = con["resolved_ip"]
    arrow = "❯" if selected else " "

    if selected:
        html = HTML(
            f"<sel_cursor>{arrow}</sel_cursor> "
            f"<sel_index>{idx:>2}</sel_index> "
            f"<sel_name>{name:<20}</sel_name> "
            f"<sel_ip>{ip}</sel_ip>"
        )
    else:
        html = HTML(
            f"<cursor>{arrow}</cursor> "
            f"<index>{idx:>2}</index> "
            f"<name>{name:<20}</name> "
            f"<ip>{ip}</ip>"
        )

    frags = list(to_formatted_text(html))
    frags.append(("", "\n"))
    return frags


def build_menu(connections, selected):
    output = []
    for idx, c in enumerate(connections, 1):
        output.extend(make_line(idx, c, selected == idx - 1))
    return output


def select_host(connections, default, style):
    selected = default

    body = FormattedTextControl(
        text=lambda: build_menu(connections, selected),
        focusable=True,
    )

    root = HSplit([
        Window(FormattedTextControl(HTML("<question>Choose host to connect to:</question>")),
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
        selected = min(len(connections) - 1, selected + 1)

    @kb.add("enter")
    def _(event):
        event.app.exit(result=selected)

    @kb.add("escape")
    @kb.add("c-c")
    def _(event):
        event.app.exit(result=None)

    app = Application(
        layout=Layout(root, focused_element=body),
        key_bindings=kb,
        full_screen=False,
        erase_when_done=True,
        style=style,
    )

    return app.run()
