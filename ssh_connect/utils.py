import os

def save_last_pos(idx):
    path = os.path.expanduser("~/.cache/ssh_last_connection")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(str(idx))

def load_last_pos():
    try:
        path = os.path.expanduser("~/.cache/ssh_last_connection")
        return int(open(path).read().strip())
    except:
        return 0
