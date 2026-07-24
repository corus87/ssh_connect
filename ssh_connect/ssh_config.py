import re
from dataclasses import dataclass, field
from pathlib import Path

from .paths import ensure_file

_LINE = re.compile(r"^(\S+)[\s=]+(.*?)$")
_INVALID_ALIAS = re.compile(r"[^A-Za-z0-9._-]+")

_CANONICAL = {
    "host": "Host",
    "hostname": "HostName",
    "user": "User",
    "port": "Port",
    "identityfile": "IdentityFile",
    "proxyjump": "ProxyJump",
    "proxycommand": "ProxyCommand",
    "forwardagent": "ForwardAgent",
    "localforward": "LocalForward",
    "remoteforward": "RemoteForward",
    "serveraliveinterval": "ServerAliveInterval",
    "stricthostkeychecking": "StrictHostKeyChecking",
    "userknownhostsfile": "UserKnownHostsFile",
}


def _canonical(key: str) -> str:
    return _CANONICAL.get(key.lower(), key)


def valid_alias(value: str) -> bool:
    """Host takes whitespace separated patterns, so an alias must be a single token."""
    return bool(value) and not _INVALID_ALIAS.search(value)


def sanitize_alias(value: str) -> str:
    return _INVALID_ALIAS.sub("-", value.strip()).strip("-.")


@dataclass
class HostEntry:
    aliases: list
    options: dict = field(default_factory=dict)
    line: int = -1

    @property
    def alias(self) -> str:
        return self.aliases[0]

    @property
    def hostname(self) -> str:
        return self.options.get("HostName", self.alias)

    @property
    def user(self):
        return self.options.get("User")

    @property
    def port(self):
        return self.options.get("Port")

    def matches(self, host: str) -> bool:
        return host == self.hostname or host in self.aliases


class SSHConfig:
    def __init__(self, path: Path):
        self.path = Path(path).expanduser()
        self.entries = []
        self.load()

    def load(self) -> None:
        self.entries = []
        if not self.path.exists():
            return
        current = None
        for number, raw in enumerate(self.path.read_text().splitlines()):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            match = _LINE.match(line)
            if not match:
                continue
            key, value = _canonical(match.group(1)), match.group(2).strip()
            if key == "Host":
                current = HostEntry(aliases=value.split(), line=number)
                self.entries.append(current)
            elif current is not None:
                current.options[key] = value

    def sorted_entries(self) -> list:
        return sorted(self.entries, key=lambda e: e.alias.lower())

    def by_alias(self, alias: str):
        for entry in self.entries:
            if alias in entry.aliases:
                return entry
        return None

    def find(self, host: str, user=None) -> list:
        matches = [e for e in self.entries if e.matches(host)]
        if user is not None:
            matches = [e for e in matches if e.user == user]
        return matches

    def unique_alias(self, base: str) -> str:
        taken = {a for entry in self.entries for a in entry.aliases}
        if base not in taken:
            return base
        index = 2
        while f"{base}-{index}" in taken:
            index += 1
        return f"{base}-{index}"

    def rename_many(self, renames) -> None:
        """Apply (entry, new_alias) pairs in one pass, bottom up so line numbers hold."""
        lines = self.path.read_text().splitlines()
        for entry, new_alias in sorted(renames, key=lambda item: item[0].line, reverse=True):
            lines[entry.line] = f"Host {' '.join([new_alias] + entry.aliases[1:])}"
            if "HostName" not in entry.options:
                lines.insert(entry.line + 1, f"    HostName {entry.hostname}")
        self.path.write_text("\n".join(lines) + "\n")
        self.load()

    def add(self, entry: HostEntry) -> None:
        ensure_file(self.path)
        block = [f"Host {' '.join(entry.aliases)}"]
        block += [f"    {key} {value}" for key, value in entry.options.items()]
        prefix = "\n" if self.path.stat().st_size else ""
        with self.path.open("a") as handle:
            handle.write(prefix + "\n".join(block) + "\n")
        self.load()
