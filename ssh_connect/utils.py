from pathlib import Path

CACHE = Path("~/.cache/ssh_connect_last").expanduser()


def save_last(alias: str) -> None:
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(alias)
    except OSError:
        pass


def load_last() -> str:
    try:
        return CACHE.read_text().strip()
    except OSError:
        return ""
