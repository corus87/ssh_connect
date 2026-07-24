import os
from pathlib import Path

SSH_DIR = Path("~/.ssh").expanduser()
CONFIG_FILE = SSH_DIR / "ssh_connect.conf"
SETTINGS_FILE = SSH_DIR / "ssh_connect.yml"
SSH_CONFIG = SSH_DIR / "config"

INCLUDE_LINE = f"Include ~/.ssh/{CONFIG_FILE.name}"


def ensure_file(path: Path) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not path.exists():
        path.touch(mode=0o600)
    os.chmod(path, 0o600)


def include_present() -> bool:
    if not SSH_CONFIG.exists():
        return False
    for line in SSH_CONFIG.read_text().splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("include") and CONFIG_FILE.name in stripped:
            return True
    return False
