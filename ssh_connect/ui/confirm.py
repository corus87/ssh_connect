from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML

def ask_confirm(message, style):
    """
    Ask:  "<message> (Y/n)"  and return True/False.
    Uses prompt_toolkit styling.
    """

    text = HTML(f"<question>{message}</question> <name>(Y/n)</name> ")

    while True:
        answer = prompt(text, style=style).strip().lower()

        if answer == "":
            return True  # default = Yes
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        # Otherwise repeat the question
