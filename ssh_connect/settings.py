from dataclasses import dataclass
from pathlib import Path

import yaml

from .paths import ensure_file
from .ui.selector import DEFAULT_ROWS

TEMPLATE = """\
# ssh_connect settings
# Hosts themselves live in ssh_connect.conf, this file only holds
# options that have no equivalent in the OpenSSH config format.

theme: material
max_rows: 15

hosts: {}
#  appliance:
#    password: secret          # login via sshpass
#  legacy-box:
#    skip_key_setup: true      # never offer to upload a public key
"""


@dataclass
class HostSettings:
    password: str = None
    skip_key_setup: bool = False


class Settings:
    def __init__(self, path: Path):
        self.path = Path(path).expanduser()
        self.data = {}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            self.data = yaml.safe_load(self.path.read_text()) or {}
        else:
            self.data = {}

    @property
    def theme(self) -> str:
        return self.data.get("theme", "material")

    @property
    def max_rows(self) -> int:
        """How many hosts the selector shows before it starts scrolling."""
        try:
            return max(1, int(self.data.get("max_rows", DEFAULT_ROWS)))
        except (TypeError, ValueError):
            return DEFAULT_ROWS

    def host(self, alias: str) -> HostSettings:
        entry = (self.data.get("hosts") or {}).get(alias) or {}
        return HostSettings(
            password=entry.get("password"),
            skip_key_setup=bool(entry.get("skip_key_setup", False)),
        )

    def set_skip_key_setup(self, alias: str, value: bool = True) -> None:
        hosts = self.data.setdefault("hosts", {}) or {}
        self.data["hosts"] = hosts
        hosts.setdefault(alias, {})["skip_key_setup"] = value
        self.save()

    def rename_host(self, old: str, new: str) -> bool:
        hosts = self.data.get("hosts") or {}
        if old not in hosts:
            return False
        hosts[new] = hosts.pop(old)
        self.data["hosts"] = hosts
        return True

    def save(self) -> None:
        ensure_file(self.path)
        self.path.write_text(yaml.safe_dump(self.data, sort_keys=False))

    def create_if_missing(self) -> None:
        if not self.path.exists():
            ensure_file(self.path)
            self.path.write_text(TEMPLATE)
            self.load()
