import os
import shutil
import subprocess

from .ui.confirm import ask_confirm
from .ui.pubkey_selector import select_pubkey

def list_local_pubkeys():
    ssh_dir = os.path.expanduser("~/.ssh")
    if not os.path.isdir(ssh_dir):
        return []

    keys = [
        os.path.join(ssh_dir, f)
        for f in os.listdir(ssh_dir)
        if f.endswith(".pub")
    ]

    # ed25519 first, then alphabetical
    keys = sorted(keys, key=lambda k: (not k.endswith("ed25519.pub"), k))

    return keys


def start_session(con, index, style, save_pos_cb):
    user = con.get("user", os.getenv("LOGNAME"))
    host = con["resolved_ip"]
    port = str(con.get("port", 22))
    password = con.get("password")

    save_pos_cb(index)

    if password:
        if shutil.which("sshpass"):
            return subprocess.run(
                ["sshpass", "-p", password, "ssh", f"{user}@{host}", "-p", port]
            )
        return subprocess.run(["ssh", f"{user}@{host}", "-p", port])

    # Probe
    check = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=3",
         f"{user}@{host}", "-p", port, "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    stderr = check.stderr.lower()
    need_key = any(x in stderr for x in ["permission denied", "publickey", "password:"])
    unreachable = any(x in stderr for x in ["timed out", "connection refused", "no route"])

    if unreachable:
        print(f"Host {host} unreachable.")
        return

    if need_key and not con.get("skip_key_setup", False):

        if ask_confirm(f"No key on {host}. Upload one?", style):
            keys = list_local_pubkeys()
            key = select_pubkey(keys, style)

            if not key:
                return

            subprocess.run(["ssh-copy-id", "-i", key, "-p", port,
                            f"{user}@{host}"])

    return subprocess.run(["ssh", f"{user}@{host}", "-p", port])
