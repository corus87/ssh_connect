import re
import os
import sys
import yaml
import socket


def load_hosts_file(path):
    """Load and resolve hosts exactly like the old ssh_connect script."""
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        print(f"ERROR: Hosts file not found: {path}")
        sys.exit(1)

    try:
        with open(path, "r") as f:
            raw = f.read().strip()
    except Exception as e:
        print(f"ERROR: Cannot read {path}:\n{e}")
        sys.exit(1)

    if not raw:
        return []

    try:
        entries = yaml.safe_load(raw)
    except Exception as e:
        print(f"ERROR: Invalid YAML in {path}:\n{e}")
        sys.exit(1)

    if not isinstance(entries, list):
        print("ERROR: hosts file must contain a YAML list")
        sys.exit(1)

    for entry in entries:
        host = entry["host"]
        pretty = entry.get("name")

        # PRETTY NAME
        if pretty:
            entry["resolved_name"] = pretty

            if is_ip(host):
                entry["resolved_ip"] = host
            else:
                entry["resolved_ip"] = socket.gethostbyname(host)
            continue

        # IP literal
        if is_ip(host):
            entry["resolved_ip"] = host
            try:
                rev = socket.gethostbyaddr(host)[0]
                entry["resolved_name"] = rev.split(".")[0].capitalize()
            except:
                entry["resolved_name"] = "Unknown"
            continue

        # FQDN
        if "." in host:
            try:
                entry["resolved_ip"] = socket.gethostbyname(host)
            except:
                entry["resolved_ip"] = host

            entry["resolved_name"] = host.split(".")[0].capitalize()
            continue

        # Simple hostname
        try:
            ip = socket.gethostbyname(host)
        except:
            ip = host

        entry["resolved_ip"] = ip

        try:
            rev = socket.gethostbyaddr(ip)[0]
            entry["resolved_name"] = rev.split(".")[0].capitalize()
        except:
            entry["resolved_name"] = host.capitalize()


    mode = os.getenv("SSH_CONNECT_SORT", "ip").strip().lower()

    if mode == "name":
        return sorted(entries, key=lambda x: x["resolved_name"].lower())

    return sorted(entries, key=lambda x: ip_sort(x["resolved_ip"]))


def is_ip(s: str):
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", s))


def ip_sort(ip: str):
    if is_ip(ip):
        return tuple(int(n) for n in ip.split("."))
    return (999, 999, 999, 999)
