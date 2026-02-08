#!/usr/bin/env python3
import os
import sys
import textwrap
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VENV = SCRIPT_DIR / ".venv"
REQUIREMENTS = SCRIPT_DIR / "requirements.txt"


def ask(prompt, default=True):
    """
    Simple Y/n prompt with default=True/False.
    """
    suffix = "Y/n" if default else "y/N"
    ans = input(f"{prompt} ({suffix}) ").strip().lower()

    if ans == "" and default:
        return True
    if ans == "" and not default:
        return False
    return ans.startswith("y")


# ---------------------------------------------------------
# VIRTUAL ENVIRONMENT
# ---------------------------------------------------------
def ensure_venv():
    """Create venv + install dependencies if needed."""
    first_install = not VENV.exists()

    if first_install:
        print("Creating virtual environment…")
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)

    pip = VENV / "bin" / "pip"

    # No requirements.txt? → nothing to install
    if not REQUIREMENTS.exists():
        return

    # Check installed packages
    installed = subprocess.run(
        [str(pip), "freeze"],
        text=True,
        capture_output=True
    ).stdout.lower()

    with open(REQUIREMENTS, "r") as f:
        needed = [line.strip() for line in f.readlines() if line.strip()]

    # Install missing packages
    missing = [pkg for pkg in needed if pkg.lower() not in installed]

    if missing:
        print("Installing dependencies:", ", ".join(missing))
        subprocess.run([str(pip), "install"] + missing, check=True)
    else:
        # no output on repeated install
        pass


# ---------------------------------------------------------
# WRAPPER INSTALLATION
# ---------------------------------------------------------
def ensure_wrapper():
    """Install launcher + optional symlink interactively."""
    bin_dir = Path("~/.local/bin").expanduser()
    bin_dir.mkdir(parents=True, exist_ok=True)

    wrapper_path = bin_dir / "ssh_connect"

    desired = f"""#!/bin/bash
exec "{VENV}/bin/python" -m ssh_connect "$@"
"""

    print("\nWrapper installation\n---------------------")
    print(f"Wrapper target: {wrapper_path}")

    # Wrapper does not exist
    if not wrapper_path.exists():
        if ask("Install wrapper?", default=True):
            wrapper_path.write_text(desired)
            wrapper_path.chmod(0o755)
            print("Wrapper installed.")
        else:
            print("Skipping wrapper.")
            return
    else:
        # Exists → ask if update required
        current = wrapper_path.read_text()
        if current != desired:
            if ask("Wrapper exists. Update it?", default=True):
                wrapper_path.write_text(desired)
                wrapper_path.chmod(0o755)
                print("Wrapper updated.")
            else:
                print("Keeping existing wrapper.")
        else:
            print("Wrapper already correct. Nothing to do.")

    # Optional symlink
    print("\nShortcut command\n----------------")
    if ask("Create shortcut command (symlink)?", default=True):
        name = input("Symlink name (default: sc): ").strip()
        if not name:
            name = "sc"

        symlink_path = bin_dir / name

        if symlink_path.exists():
            if ask(f"'{name}' already exists. Overwrite?", default=False):
                symlink_path.unlink()
            else:
                print("Skipping symlink.")
                return

        symlink_path.symlink_to(wrapper_path)
        print(f"Shortcut installed: {symlink_path}")
    else:
        print("Skipping shortcut.")


# ---------------------------------------------------------
# MAIN INSTALLER
# ---------------------------------------------------------
def main():
    print("\nssh_connect installation\n========================")

    ensure_venv()
    ensure_wrapper()

    print("\nInstallation completed.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass