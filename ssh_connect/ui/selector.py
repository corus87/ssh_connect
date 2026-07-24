import shutil

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl

DEFAULT_ROWS = 15


class _Selector:
    def __init__(self, items, label, sublabel, title, style, initial, max_rows):
        self.max_rows = max(1, max_rows)
        self.items = items
        self.label = label
        self.sublabel = sublabel
        self.title = title
        self.style = style
        self.query = ""
        self.index = initial
        self.offset = 0
        self.result = None

    @property
    def rows(self) -> int:
        """Requested page size, capped so the menu always fits the terminal."""
        available = shutil.get_terminal_size(fallback=(80, 24)).lines - 4
        return max(1, min(self.max_rows, available))

    @property
    def visible(self) -> list:
        if not self.query:
            return self.items
        needle = self.query.lower()
        return [
            item
            for item in self.items
            if needle in self.label(item).lower() or needle in (self.sublabel(item) or "").lower()
        ]

    def _clamp(self) -> None:
        count = len(self.visible)
        self.index = max(0, min(self.index, count - 1)) if count else 0
        rows = min(self.rows, count)
        self.offset = max(0, min(self.offset, max(0, count - rows)))
        if self.index < self.offset:
            self.offset = self.index
        elif self.index >= self.offset + rows:
            self.offset = self.index - rows + 1

    def _fragments(self) -> list:
        self._clamp()
        visible = self.visible
        width = max((len(self.label(i)) for i in visible), default=0)

        lines = [("class:sc.title", self.title)]
        if self.query:
            lines.append(("class:sc.filter", f"  /{self.query}"))
        lines.append(("", "\n"))

        for position, item in enumerate(visible[self.offset : self.offset + self.rows], start=self.offset):
            selected = position == self.index
            lines.append(("class:sc.pointer", " ❯ " if selected else "   "))
            lines.append(
                ("class:sc.item.selected" if selected else "class:sc.item", self.label(item).ljust(width))
            )
            sub = self.sublabel(item)
            if sub:
                lines.append(("class:sc.sub.selected" if selected else "class:sc.sub", f"   {sub}"))
            lines.append(("", "\n"))

        if not visible:
            lines.append(("class:sc.hint", "   no match\n"))
        lines.append(("class:sc.hint", "   ↑/↓ select · type to filter · enter connect · esc cancel"))
        return lines

    def _height(self) -> int:
        return min(self.rows, max(1, len(self.visible))) + 2

    def build(self) -> Application:
        keys = KeyBindings()

        @keys.add("up")
        @keys.add("c-p")
        def _up(event):
            self.index = (self.index - 1) % max(1, len(self.visible))

        @keys.add("down")
        @keys.add("c-n")
        def _down(event):
            self.index = (self.index + 1) % max(1, len(self.visible))

        @keys.add("enter")
        def _accept(event):
            visible = self.visible
            if visible:
                self.result = visible[self.index]
            event.app.exit()

        @keys.add("escape", eager=True)
        @keys.add("c-c")
        @keys.add("c-d")
        def _cancel(event):
            event.app.exit()

        @keys.add("backspace")
        def _backspace(event):
            self.query = self.query[:-1]
            self.index = 0

        @keys.add("<any>")
        def _type(event):
            if event.data and event.data.isprintable():
                self.query += event.data
                self.index = 0

        window = Window(
            content=FormattedTextControl(self._fragments, focusable=True),
            height=self._height,
            dont_extend_height=True,
            always_hide_cursor=True,
            wrap_lines=False,
        )
        return Application(
            layout=Layout(HSplit([window, Window(height=1)])),
            key_bindings=keys,
            style=self.style,
            full_screen=False,
            erase_when_done=True,
        )


def select(
    items,
    style,
    title="Choose host to connect to:",
    label=str,
    sublabel=lambda _: "",
    initial=0,
    max_rows=DEFAULT_ROWS,
):
    if not items:
        return None
    if len(items) == 1:
        return items[0]
    selector = _Selector(items, label, sublabel, title, style, min(initial, len(items) - 1), max_rows)
    selector.build().run()
    return selector.result