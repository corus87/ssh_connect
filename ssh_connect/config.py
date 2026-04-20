import re
import os
import sys
import yaml
import socket
from dataclasses import dataclass


DEFAULT_CONFIG_PATH = "~/.ssh_connect.yml"


@dataclass
class Settings:
    theme: str = "material"
    resolve_dns: bool = True
    skip_key_setup: bool = False


def load_config(path):
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        print(f"ERROR: Config file not found: {path}")
        sys.exit(1)

    try:
        with open(path, "r") as f:
            raw = f.read().strip()
    except Exception as e:
        print(f"ERROR: Cannot read {path}:\n{e}")
        sys.exit(1)

    if not raw:
        return Settings(), []

    try:
        data = yaml.safe_load(raw)
    except Exception as e:
        print(f"ERROR: Invalid YAML in {path}:\n{e}")
        sys.exit(1)

    if isinstance(data, list):
        print(f"WARNING: {path} uses the old format (plain host list).")
        print("Please migrate to the new format:")
        print("  settings:")
        print("    theme: material")
        print("    resolve_dns: true")
        print("    skip_key_setup: false")
        print("  hosts:")
        print("    - host: ...")
        settings = Settings()
        entries = data
    elif isinstance(data, dict):
        raw_settings = data.get("settings") or {}
        settings = Settings(
            theme=raw_settings.get("theme", "material"),
            resolve_dns=raw_settings.get("resolve_dns", True),
            skip_key_setup=raw_settings.get("skip_key_setup", False),
        )
        entries = data.get("hosts") or []
    else:
        print("ERROR: Config must be a mapping with 'settings' and 'hosts' keys.")
        sys.exit(1)

    return settings, _resolve_hosts(entries, settings.resolve_dns)


def _resolve_hosts(entries, resolve_dns):
    for entry in entries:
        host = entry["host"]
        pretty = entry.get("name")

        if pretty:
            entry["resolved_name"] = pretty
            entry["resolved_ip"] = _resolve_hostname(host) if resolve_dns else host
            continue

        if is_ip(host):
            entry["resolved_ip"] = host
            if resolve_dns:
                try:
                    rev = socket.gethostbyaddr(host)[0]
                    entry["resolved_name"] = rev.split(".")[0].capitalize()
                except Exception:
                    entry["resolved_name"] = "Unknown"
            else:
                entry["resolved_name"] = "Unknown"
            continue

        if "." in host:
            entry["resolved_ip"] = _resolve_hostname(host) if resolve_dns else host
            entry["resolved_name"] = host.split(".")[0].capitalize()
            continue

        # Simple hostname
        ip = _resolve_hostname(host) if resolve_dns else host
        entry["resolved_ip"] = ip

        if resolve_dns and is_ip(ip):
            try:
                rev = socket.gethostbyaddr(ip)[0]
                entry["resolved_name"] = rev.split(".")[0].capitalize()
            except Exception:
                entry["resolved_name"] = host.capitalize()
        else:
            entry["resolved_name"] = host.capitalize()

    mode = os.getenv("SSH_CONNECT_SORT", "ip").strip().lower()

    if mode == "name":
        return sorted(entries, key=lambda x: x["resolved_name"].lower())

    return sorted(entries, key=lambda x: ip_sort(x["resolved_ip"]))


def _resolve_hostname(host):
    if is_ip(host):
        return host
    try:
        return socket.gethostbyname(host)
    except Exception:
        return host


def is_ip(s: str):
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", s))


def ip_sort(ip: str):
    if is_ip(ip):
        return tuple(int(n) for n in ip.split("."))
    return (999, 999, 999, 999)
