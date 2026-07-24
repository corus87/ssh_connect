import ipaddress
import socket
import threading
import time


def is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _lookup(host: str, results: dict) -> None:
    try:
        results[host] = socket.gethostbyaddr(host)[0]
    except OSError:
        results[host] = None


def reverse_lookup(hosts, timeout: float = 3.0) -> dict:
    """Resolve all hosts in parallel, bounded by a single overall timeout."""
    results = {}
    threads = []
    for host in dict.fromkeys(hosts):
        thread = threading.Thread(target=_lookup, args=(host, results), daemon=True)
        thread.start()
        threads.append(thread)

    deadline = time.monotonic() + timeout
    for thread in threads:
        thread.join(max(0.0, deadline - time.monotonic()))
    return results


def shorten(name: str) -> str:
    label = name.rstrip(".").split(".")[0]
    return label[:1].upper() + label[1:]


def propose_alias(entry, resolved, keep_fqdn: bool):
    """Best guess for a readable alias, or None if there is nothing to work with."""
    if is_ip(entry.hostname):
        source = resolved
    else:
        source = resolved or entry.hostname
    if not source:
        return None
    return source.rstrip(".") if keep_fqdn else shorten(source)
