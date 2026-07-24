#!/usr/bin/env python3
"""One-shot migration from the ssh_connect 1.x YAML file to the 2.x layout.

Usage: migrate_v1_to_v2.py [path-to-old-config]

Reads ~/.ssh_connect.yml (or the given path) and writes ~/.ssh/ssh_connect.conf
plus ~/.ssh/ssh_connect.yml. The old file is left untouched.
"""
import os
import re
import sys
from pathlib import Path

import yaml

NEW_CONFIG = Path("~/.ssh/ssh_connect.conf").expanduser()
NEW_SETTINGS = Path("~/.ssh/ssh_connect.yml").expanduser()


def make_alias(host: dict, taken: set) -> str:
    raw = host.get("name") or host["host"]
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", str(raw)).strip("-")
    if not base:
        base = "host"
    alias = base
    index = 2
    while alias in taken:
        alias = f"{base}-{index}"
        index += 1
    taken.add(alias)
    return alias


def main() -> None:
    old = Path(sys.argv[1] if len(sys.argv) > 1 else "~/.ssh_connect.yml").expanduser()
    if not old.exists():
        sys.exit(f"{old} not found, nothing to migrate")
    if NEW_CONFIG.exists():
        sys.exit(f"{NEW_CONFIG} already exists, aborting to avoid overwriting it")

    data = yaml.safe_load(old.read_text()) or {}
    old_settings = data.get("settings") or {}
    hosts = data.get("hosts") or []

    blocks = []
    overrides = {}
    taken = set()

    for host in hosts:
        if not host.get("host"):
            continue
        alias = make_alias(host, taken)
        lines = [f"Host {alias}", f"    HostName {host['host']}"]
        if host.get("user"):
            lines.append(f"    User {host['user']}")
        if host.get("port"):
            lines.append(f"    Port {host['port']}")
        if host.get("identity_file"):
            lines.append(f"    IdentityFile {host['identity_file']}")
        blocks.append("\n".join(lines))

        extra = {}
        if host.get("password"):
            extra["password"] = host["password"]
        if host.get("skip_key_setup"):
            extra["skip_key_setup"] = True
        if extra:
            overrides[alias] = extra

    NEW_CONFIG.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    NEW_CONFIG.write_text("\n\n".join(blocks) + "\n")
    os.chmod(NEW_CONFIG, 0o600)

    settings = {
        "theme": old_settings.get("theme", "material"),
        "max_rows": 15,
        "hosts": overrides,
    }
    NEW_SETTINGS.write_text(yaml.safe_dump(settings, sort_keys=False))
    os.chmod(NEW_SETTINGS, 0o600)

    print(f"Migrated {len(blocks)} hosts to {NEW_CONFIG}")
    print(f"Wrote settings to {NEW_SETTINGS}")
    if old_settings.get("skip_key_setup"):
        print("Note: the global skip_key_setup option is gone, set it per host instead.")
    print("Add 'Include ~/.ssh/ssh_connect.conf' to the top of ~/.ssh/config if not done yet.")


if __name__ == "__main__":
    main()
