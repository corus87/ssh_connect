# ssh_connect

`ssh_connect` is an interactive SSH host selector with DNS resolution, theming, key-handling support, and a clean prompt-toolkit interface.  
It provides a fast, keyboard-driven workflow for jumping between multiple SSH targets.

---

## Features

- Interactive TUI menu (non-fullscreen, blends naturally into the shell)
- DNS resolution (forward + reverse lookup)
- Configurable display names
- Sorting by IP or hostname
- Multiple color themes (Material, Nord, Dracula, Gruvbox, etc.)
- Automatic detection of missing authorized keys
- Interactive public-key selection menu
- Clean YAML-based host configuration

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/corus87/ssh_connect.git
   cd ssh_connect
   ```

2. Run the installer:
   ```bash
   ./install.py
   ```

This will:

- Create a local virtual environment (`.venv`)
- Install all Python dependencies
- Install the wrapper at `~/.local/bin/ssh_connect`
- Optionally install a short alias (`sc` → symlink)

After installation, simply run:

```bash
ssh_connect
```

or

```bash
sc
```

---

## Usage

### Interactive selector
```bash
ssh_connect
```

### Connect by index
```bash
ssh_connect 3
```

### List resolved hosts
```bash
ssh_connect --list
```

### Edit hosts file
```bash
ssh_connect --edit
```

### Show available themes
```bash
ssh_connect --themes
```

---

## Host Configuration

Hosts are defined in a YAML file:

**Default:** `~/.ssh_hosts.yml`  
Override via:

```bash
export SSH_CONNECT_HOSTS_FILE=/path/to/file.yml
```

### Example `~/.ssh_hosts.yml`

```yaml
- name: Webserver
  host: web01.internal.example.com
  user: admin

- host: 10.20.30.5
  port: 2222

- host: db01
  skip_key_setup: true
```

Each entry may contain:

| Key             | Description                                         |
|-----------------|-----------------------------------------------------|
| `name`          | Display name (optional)                             |
| `host`          | Hostname, FQDN, or IP (required)                    |
| `user`          | SSH username (default: current user)                |
| `port`          | SSH port (default: 22)                              |
| `password`      | Password for sshpass-based login (optional)         |
| `skip_key_setup`| Skip automatic `ssh-copy-id` (optional)             |

---

## Environment Variables

### `SSH_CONNECT_HOSTS_FILE`
Custom hosts file path.

### `SSH_CONNECT_SORT`
Sorting method:

```
ip     → numeric IP sort (default)  
name   → alphabetical by resolved_name
```

### `SSH_CONNECT_THEME`
Theme selection. Example:

```bash
export SSH_CONNECT_THEME=dracula
```

List available themes:

```bash
ssh_connect --themes
```

---

## Key Upload Workflow

If a host refuses login with:

- `Permission denied`
- `publickey`
- password prompt

ssh_connect can automatically upload a public key.

## License

MIT — feel free to modify or integrate into your workflow.

