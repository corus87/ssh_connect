import os
import shutil
import subprocess
from pathlib import Path

from .paths import SSH_DIR
from .ui.confirm import ask_confirm
from .ui.selector import select

OK = "ok"
NEEDS_AUTH = "auth"
UNREACHABLE = "unreachable"


def list_local_pubkeys() -> list:
    if not SSH_DIR.is_dir():
        return []
    keys = [p for p in SSH_DIR.glob("*.pub") if p.is_file()]
    return sorted(keys, key=lambda k: (not k.name.endswith("ed25519.pub"), k.name))


def _fingerprint(path: Path) -> str:
    try:
        result = subprocess.run(
            ["ssh-keygen", "-l", "-f", str(path)], capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if result.returncode != 0:
        return ""
    parts = result.stdout.split()
    return f"{parts[1]} {parts[-1]}" if len(parts) > 2 else ""


def probe(alias: str, timeout: int = 5) -> str:
    """Check whether a non-interactive login works, without prompting."""
    command = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", f"ConnectTimeout={timeout}",
        "-o", "StrictHostKeyChecking=accept-new",
        alias,
        "true",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except OSError:
        return UNREACHABLE
    if result.returncode == 0:
        return OK
    stderr = result.stderr.lower()
    if "permission denied" in stderr or "no supported authentication" in stderr:
        return NEEDS_AUTH
    return UNREACHABLE


def copy_key(alias: str, pubkey: Path, password=None) -> bool:
    command = ["ssh-copy-id", "-i", str(pubkey), alias]
    env = os.environ.copy()
    if password:
        if not shutil.which("sshpass"):
            print("sshpass is not installed")
            return False
        env["SSHPASS"] = password
        command = ["sshpass", "-e"] + command
    return subprocess.run(command, env=env).returncode == 0


def setup_key(alias: str, settings, style) -> None:
    host_settings = settings.host(alias)
    if host_settings.skip_key_setup:
        return

    state = probe(alias)
    if state == UNREACHABLE:
        print(f"Host {alias} is not reachable, trying anyway.")
        return
    if state != NEEDS_AUTH:
        return

    if not ask_confirm(f"No key on {alias}. Upload one?", style):
        if ask_confirm("Stop asking for this host?", style, default=False):
            settings.set_skip_key_setup(alias)
        return

    keys = list_local_pubkeys()
    if not keys:
        print("No public keys found in ~/.ssh")
        return

    pubkey = select(
        keys,
        style,
        title="Select SSH public key:",
        label=lambda p: p.name,
        sublabel=_fingerprint,
        max_rows=settings.max_rows,
    )
    if pubkey and not copy_key(alias, pubkey, host_settings.password):
        print("Key upload failed, connecting anyway.")


def start_session(entry, settings, style) -> None:
    """Replace the current process with the ssh session."""
    password = settings.host(entry.alias).password
    if not password:
        setup_key(entry.alias, settings, style)
        os.execvp("ssh", ["ssh", entry.alias])

    if not shutil.which("sshpass"):
        raise SystemExit("sshpass is not installed but a password is configured")
    os.environ["SSHPASS"] = password
    os.execvp("sshpass", ["sshpass", "-e", "ssh", entry.alias])
