import argparse
import os
import subprocess
import sys

from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit.shortcuts import print_formatted_text

from . import __version__
from .paths import CONFIG_FILE, INCLUDE_LINE, SETTINGS_FILE, ensure_file, include_present
from .resolve import is_ip, propose_alias, reverse_lookup, shorten
from .session import start_session
from .settings import Settings
from .ssh_config import HostEntry, SSHConfig, sanitize_alias, valid_alias
from .themes import get_style, print_themes
from .ui.confirm import ask_confirm, ask_text
from .ui.selector import select
from .utils import load_last, save_last


def parse_target(target: str):
    user = None
    port = None
    if "@" in target:
        user, target = target.rsplit("@", 1)
    if target.count(":") == 1:
        head, tail = target.rsplit(":", 1)
        if tail.isdigit():
            target, port = head, tail
    return user, target, port


def unique(base: str, taken) -> str:
    if base not in taken:
        return base
    index = 2
    while f"{base}-{index}" in taken:
        index += 1
    return f"{base}-{index}"


def prompt_alias(style, default: str, message: str = "Alias:"):
    """Ask for an alias until it is a single valid Host token, or the user backs out."""
    while True:
        answer = ask_text(message, style, default=default)
        if not answer:
            return answer
        if valid_alias(answer):
            return answer
        default = sanitize_alias(answer) or default
        print("An alias must be a single word without spaces or wildcards.")


def target_label(entry) -> str:
    target = f"{entry.user}@{entry.hostname}" if entry.user else entry.hostname
    return f"{target}:{entry.port}" if entry.port else target


def suggest_alias(config: SSHConfig, host: str, user) -> str:
    if is_ip(host):
        found = reverse_lookup([host], timeout=2.0).get(host)
        base = shorten(found) if found else host
    else:
        base = shorten(host)
    if user and user != (os.getenv("USER") or os.getenv("LOGNAME")):
        base = f"{base}-{user}"
    return config.unique_alias(sanitize_alias(base) or "host")


def add_host(config: SSHConfig, host: str, user, port, style):
    label = f"{user}@{host}" if user else host
    if not ask_confirm(f"{label} is not configured yet. Add it?", style):
        return None

    alias = prompt_alias(style, suggest_alias(config, host, user))
    if not alias:
        return None

    options = {"HostName": host}
    if user:
        options["User"] = user
    if port:
        options["Port"] = port

    entry = HostEntry([config.unique_alias(alias)], options)
    config.add(entry)
    print(f"Added '{entry.alias}' to {config.path}")
    return entry


def resolve(config: SSHConfig, target: str, style, max_rows):
    user, host, port = parse_target(target)

    if user is None and port is None:
        entry = config.by_alias(host)
        if entry:
            return entry

    matches = config.find(host, user)
    if len(matches) == 1:
        return matches[0]
    if matches:
        return select(
            matches,
            style,
            title=f"Multiple entries for {host}:",
            label=lambda e: e.alias,
            sublabel=target_label,
            max_rows=max_rows,
        )
    return add_host(config, host, user, port, style)


def resolve_targets(config: SSHConfig, only, everything: bool) -> list:
    entries = config.sorted_entries()
    if only is not None:
        return [e for e in entries if only in e.aliases]
    if everything:
        return entries
    return [e for e in entries if e.alias == e.hostname]


def resolve_aliases(config, settings, style, keep_fqdn, only=None, everything=False) -> None:
    entries = resolve_targets(config, only, everything)
    if not entries:
        print("Every host already has its own alias. Use --all to review them anyway.")
        return

    addresses = [e.hostname for e in entries if is_ip(e.hostname)]
    if addresses:
        print(f"Resolving {len(addresses)} address(es)...")
    resolved = reverse_lookup(addresses) if addresses else {}

    width = max(len(e.alias) for e in entries)
    taken = {alias for entry in config.entries for alias in entry.aliases}
    renames = []
    unresolved = []
    explained = False

    for entry in entries:
        found = resolved.get(entry.hostname)
        proposal = propose_alias(entry, found, keep_fqdn)
        if proposal is None:
            unresolved.append(entry.alias)
            continue
        if proposal == entry.alias:
            continue

        if not explained:
            print("\nEnter accepts, edit to change, clear the line to skip, Ctrl-C to stop.")
            explained = True

        print_formatted_text(
            FormattedText(
                [
                    ("", "\n"),
                    ("class:name", entry.alias.ljust(width)),
                    ("class:index", "  ->  "),
                    ("class:ip", found or entry.hostname),
                ]
            ),
            style=style,
        )

        answer = prompt_alias(style, proposal)
        if answer is None:
            print("\nStopped.")
            break
        if not answer or answer == entry.alias:
            continue

        answer = unique(answer, taken - set(entry.aliases))
        taken.discard(entry.alias)
        taken.add(answer)
        renames.append((entry, answer))

    if renames:
        config.rename_many(renames)
        if any(settings.rename_host(old.alias, new) for old, new in renames):
            settings.save()
        last = load_last()
        for old, new in renames:
            if old.alias == last:
                save_last(new)
        print(f"\nUpdated {len(renames)} host(s) in {config.path}")
    else:
        print("\nNothing to change.")

    if unresolved:
        print(f"No name found for: {', '.join(unresolved)}")


def print_list(config: SSHConfig) -> None:
    entries = config.sorted_entries()
    if not entries:
        print(f"No hosts configured in {config.path}")
        return
    width = max(len(e.alias) for e in entries)
    for entry in entries:
        print(f"{entry.alias.ljust(width)}   {target_label(entry)}")


def open_editor(path) -> None:
    ensure_file(path)
    editor = os.getenv("VISUAL") or os.getenv("EDITOR") or "nano"
    subprocess.call([editor, str(path)])


def parse_args():
    parser = argparse.ArgumentParser(
        prog="ssh_connect",
        description="Interactive SSH host selector backed by an OpenSSH config include.",
    )
    parser.add_argument("target", nargs="?", help="alias, host, ip or user@host[:port]")
    parser.add_argument("--list", action="store_true", help="list configured hosts")
    parser.add_argument("--edit", action="store_true", help="edit the host config")
    parser.add_argument("--settings", action="store_true", help="edit the settings file")
    parser.add_argument("--themes", action="store_true", help="list available themes")
    parser.add_argument("--resolve", action="store_true", help="rename hosts from reverse DNS")
    parser.add_argument("--fqdn", action="store_true", help="with --resolve, keep the full domain name")
    parser.add_argument("--all", action="store_true", help="with --resolve, review named hosts too")
    parser.add_argument("--version", action="version", version=f"ssh_connect {__version__}")
    return parser.parse_args()


class SSHConnect:
    def __init__(self):
        self.config = SSHConfig(CONFIG_FILE)
        self.settings = Settings(SETTINGS_FILE)
        self.style = get_style(self.settings.theme)

    def pick_host(self):
        entries = self.config.sorted_entries()
        if not entries:
            print(f"No hosts configured. Use 'ssh_connect --edit' or 'ssh_connect user@host'.")
            return None
        last = load_last()
        initial = next((i for i, e in enumerate(entries) if e.alias == last), 0)
        return select(
            entries,
            self.style,
            label=lambda e: e.alias,
            sublabel=lambda e: "" if e.alias == target_label(e) else target_label(e),
            initial=initial,
            max_rows=self.settings.max_rows,
        )

    def run(self, args) -> None:
        if args.edit:
            return open_editor(self.config.path)
        if args.settings:
            self.settings.create_if_missing()
            return open_editor(self.settings.path)
        if args.list:
            return print_list(self.config)
        if args.resolve:
            return resolve_aliases(
                self.config, self.settings, self.style, args.fqdn, args.target, args.all
            )

        if not include_present():
            print(f"Note: add '{INCLUDE_LINE}' to the top of ~/.ssh/config", file=sys.stderr)

        entry = (
            resolve(self.config, args.target, self.style, self.settings.max_rows)
            if args.target
            else self.pick_host()
        )
        if entry is None:
            return

        save_last(entry.alias)
        print_formatted_text(
            HTML(f"<question>Connecting to:</question> <name>{entry.alias}</name>"),
            style=self.style,
        )
        start_session(entry, self.settings, self.style)


def main() -> None:
    args = parse_args()
    if args.themes:
        return print_themes()
    try:
        SSHConnect().run(args)
    except KeyboardInterrupt:
        sys.exit(130)
