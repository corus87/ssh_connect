from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML


def ask_confirm(message, style, default=True):
    hint = "(Y/n)" if default else "(y/N)"
    text = HTML(f"<question>{message}</question> <name>{hint}</name> ")

    while True:
        try:
            answer = prompt(text, style=style).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        if answer == "":
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False


def ask_text(message, style, default=""):
    """Return the entered text, or None if the user aborted."""
    text = HTML(f"<question>{message}</question> ")
    try:
        return prompt(text, default=default, style=style).strip()
    except (EOFError, KeyboardInterrupt):
        return None
