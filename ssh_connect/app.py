import os
import argparse

from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import print_formatted_text

from .themes import get_style, THEMES
from .config import load_config, DEFAULT_CONFIG_PATH
from .ui.selector import select_host
from .session import start_session
from .utils import save_last_pos, load_last_pos


def print_themes():
    descriptions = {
        "material":       "Clean Material Design look (default)",
        "solarized-dark": "Warm Solarized Dark palette",
        "nord":           "Cool blue Nord colors",
        "dracula":        "High-contrast neon-gothic look",
        "gruvbox":        "Earthy warm Gruvbox scheme",
        "neon":           "Vibrant cyberpunk neon colors",
        "minimal":        "Subtle clean minimalistic theme",
    }

    print("\nAvailable themes for ssh_connect:\n")
    for name in THEMES.keys():
        print(f"  {name:<15} – {descriptions.get(name, '')}")

    print("\nSet via SSH_CONNECT_THEME env var or 'theme' in settings block of ~/.ssh_connect.yml\n")


def parse_args():
    parser = argparse.ArgumentParser(
        prog="ssh_connect",
        description="Interactive SSH connection helper using prompt_toolkit",
    )
    parser.add_argument("index", nargs="?", type=int)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--edit", action="store_true")
    parser.add_argument("--themes", action="store_true")
    return parser.parse_args()


class SSHConnect:
    def __init__(self):
        self.config_file = os.path.expanduser(
            os.getenv("SSH_CONNECT_HOSTS_FILE", DEFAULT_CONFIG_PATH)
        )
        self.settings, self.connections = load_config(self.config_file)

        # Env var overrides config-file theme
        theme = os.getenv("SSH_CONNECT_THEME", self.settings.theme)
        self.style = get_style(theme)

    def print_list(self):
        for i, c in enumerate(self.connections, 1):
            print(f"{i:<3} {c['resolved_name']:<25} {c['resolved_ip']}")

    def edit_file(self):
        editor = os.getenv("EDITOR", "nano")
        os.execvp(editor, [editor, self.config_file])

    def run(self):
        args = parse_args()

        if args.list:
            return self.print_list()

        if args.edit:
            return self.edit_file()

        if args.themes:
            print_themes()
            return

        if args.index is not None:
            idx = args.index - 1
            if 0 <= idx < len(self.connections):
                con = self.connections[idx]
                print_formatted_text(
                    HTML(f"<question>Connecting to:</question> <n>{con['resolved_name']}</n>"),
                    style=self.style,
                )
                return start_session(con, idx, self.style, save_last_pos, self.settings)

        last = load_last_pos()
        pos = select_host(self.connections, last, style=self.style)
        if pos is None:
            return

        con = self.connections[pos]
        print_formatted_text(
            HTML(f"<question>Connecting to:</question> <n>{con['resolved_name']}</n>"),
            style=self.style,
        )
        start_session(con, pos, self.style, save_last_pos, self.settings)
