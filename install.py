#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VENV = SCRIPT_DIR / ".venv"
REQUIREMENTS = SCRIPT_DIR / "requirements.txt"


def ask(prompt, default=True):
    suffix = "Y/n" if default else "y/N"
    ans = input(f"{prompt} ({suffix}) ").strip().lower()
    if ans == "" and default:
        return True
    if ans == "" and not default:
        return False
    return ans.startswith("y")


def find_valid_bindir():
    path_entries = os.getenv("PATH", "").split(":")
    writable_dirs = []

    for p in path_entries:
        p = Path(p).expanduser()
        if p.is_dir() and os.access(p, os.W_OK):
            writable_dirs.append(p)

    if writable_dirs:
        return writable_dirs[0]

    fallback = Path("~/.local/bin").expanduser()

    print("\nNo writable directory found in $PATH.")
    print(f"Fallback option: {fallback}")

    if ask("Add ~/.local/bin to PATH and use it?", default=True):
        print("Add this to your ~/.bashrc:\n")
        print('    export PATH="$HOME/.local/bin:$PATH"\n')
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    print("Aborted: no usable installation directory.")
    sys.exit(1)


def ensure_venv():
    needs_create = False

    if VENV.exists():
        py = VENV / "bin" / "python"
        pip = VENV / "bin" / "pip"

        if not py.exists() or not pip.exists():
            print("Existing .venv is broken (missing python/pip). Recreating...")
            needs_create = True
            subprocess.run(["rm", "-rf", str(VENV)], check=True)
    else:
        needs_create = True

    if needs_create:
        print("Creating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
        except subprocess.CalledProcessError:
            print("\nERROR: Failed to create virtual environment.")
            print("Most likely python3-venv is missing.\n")
            print("Install it:")
            print("  Ubuntu/Debian: sudo apt install python3-venv")
            print("  Fedora:        sudo dnf install python3-virtualenv")
            print("  Arch:          sudo pacman -S python-virtualenv\n")
            sys.exit(1)

    pip = VENV / "bin" / "pip"

    if REQUIREMENTS.exists():
        installed = subprocess.run(
            [str(pip), "freeze"], text=True, capture_output=True
        ).stdout.lower()

        with open(REQUIREMENTS, "r") as f:
            needed = [line.strip() for line in f if line.strip()]

        missing = [pkg for pkg in needed if pkg.lower() not in installed]

        if missing:
            print("Installing dependencies:", ", ".join(missing))
            subprocess.run([str(pip), "install"] + missing, check=True)


def ensure_wrapper():
    bin_dir = find_valid_bindir()
    wrapper_path = bin_dir / "ssh_connect"

    project_dir = SCRIPT_DIR
    # Do NOT .resolve() here — that follows the venv symlink to the system Python,
    # bypassing the venv entirely. The symlink path is exactly what we want.
    venv_python = VENV / "bin" / "python"

    desired = f"""#!/bin/bash
# Auto-generated ssh_connect launcher

PROJECT_DIR="{project_dir}"
VENV_PYTHON="{venv_python}"

cd "$PROJECT_DIR" || {{
    echo "ERROR: Cannot cd into $PROJECT_DIR"
    exit 1
}}

exec "$VENV_PYTHON" -m ssh_connect "$@"
"""

    print("\nWrapper installation\n---------------------")
    print(f"Target: {wrapper_path}")

    if not wrapper_path.exists():
        if ask("Install wrapper?", default=True):
            wrapper_path.write_text(desired)
            wrapper_path.chmod(0o755)
            print("Wrapper installed.")
        else:
            print("Skipping wrapper.")
            return
    else:
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

    print("\nShortcut command\n----------------")
    if ask("Create shortcut (symlink)?", default=True):
        name = input("Symlink name (default: sc): ").strip() or "sc"
        symlink = bin_dir / name

        if symlink.exists():
            if ask(f"'{name}' exists. Overwrite?", default=False):
                symlink.unlink()
            else:
                print("Skipping shortcut.")
                return

        symlink.symlink_to(wrapper_path)
        print(f"Shortcut created: {symlink}")


def ensure_include():
    ssh_config = Path("~/.ssh/config").expanduser()
    include_line = "Include ~/.ssh/ssh_connect.conf"
    existing = ssh_config.read_text() if ssh_config.exists() else ""

    print("\nOpenSSH include\n---------------")
    if "ssh_connect.conf" in existing:
        print("Include already present. Nothing to do.")
        return

    print(f"ssh_connect stores its hosts in ~/.ssh/ssh_connect.conf.")
    print(f"Without '{include_line}' in {ssh_config}, ssh will not see them.")

    if not ask("Add the include line now?", default=True):
        print("Skipping. Add it manually at the top of your ssh config.")
        return

    ssh_config.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    ssh_config.write_text(f"{include_line}\n\n{existing}")
    ssh_config.chmod(0o600)
    print(f"Updated {ssh_config}")


def main():
    print("\nssh_connect installer\n=====================")
    ensure_venv()
    ensure_wrapper()
    ensure_include()
    print("\nInstallation completed.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.\n")
