# ssh_connect

`ssh_connect` is an interactive SSH host selector with DNS resolution, theming, key-handling support, and a clean prompt-toolkit interface.  
It provides a fast, keyboard-driven workflow for jumping between multiple SSH targets.

---

## Features

- Interactive TUI menu (non-fullscreen, blends naturally into the shell)
- DNS resolution (forward + reverse lookup, can be disabled)
- Configurable display names
- Sorting by IP or hostname
- Multiple color themes (Material, Nord, Dracula, Gruvbox, etc.)
- Automatic detection of missing authorized keys (globally or per-host skippable)
- Interactive public-key selection menu
- YAML-based configuration with global settings and per-host overrides

---

## Demo
<p align="left">
  <img src="assets/demo.gif" height="450">
</p>

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

### Edit config file
```bash
ssh_connect --edit
```

### Show available themes
```bash
ssh_connect --themes
```

---

## Configuration

All configuration lives in a single YAML file:

**Default:** `~/.ssh_connect.yml`  
Override via:

```bash
export SSH_CONNECT_HOSTS_FILE=/path/to/file.yml
```

The file has two top-level sections: `settings` (global options) and `hosts` (your SSH targets).

### Example `~/.ssh_connect.yml`

```yaml
settings:
  theme: material          # active color theme
  resolve_dns: true        # set to false to skip DNS lookups (faster startup)
  skip_key_setup: false    # set to true to disable the "upload SSH key?" prompt globally

hosts:
  - name: Webserver
    host: web01.internal.example.com
    user: admin

  - host: 10.20.30.5
    port: 2222

  - host: db01
    skip_key_setup: true   # per-host override, takes precedence over global setting
```

### `settings` reference

| Key               | Default      | Description                                              |
|-------------------|--------------|----------------------------------------------------------|
| `theme`           | `material`   | Color theme. See `ssh_connect --themes` for all options. |
| `resolve_dns`     | `true`       | Perform DNS lookups on startup. Disable if hosts are unreachable via DNS and startup is slow. |
| `skip_key_setup`  | `false`      | Globally disable the automatic `ssh-copy-id` prompt.     |

### `hosts` reference

| Key               | Description                                              |
|-------------------|----------------------------------------------------------|
| `host`            | Hostname, FQDN, or IP (required)                         |
| `name`            | Display name (optional, overrides DNS-resolved name)     |
| `user`            | SSH username (default: current user)                     |
| `port`            | SSH port (default: 22)                                   |
| `password`        | Password for sshpass-based login (optional)              |
| `skip_key_setup`  | Per-host override for key setup prompt (optional)        |

---

## Environment Variables

### `SSH_CONNECT_HOSTS_FILE`
Custom config file path.

### `SSH_CONNECT_SORT`
Sorting method:

```
ip     → numeric IP sort (default)
name   → alphabetical by resolved name
```

### `SSH_CONNECT_THEME`
Overrides the theme set in the config file. Example:

```bash
export SSH_CONNECT_THEME=dracula
```

List available themes:

```bash
ssh_connect --themes
```

---

## Key Upload Workflow

If a host refuses login with `Permission denied`, `publickey`, or a password prompt,
ssh_connect offers to upload a public key automatically via `ssh-copy-id`.

This can be disabled globally via `skip_key_setup: true` in the `settings` block,
or per-host by setting `skip_key_setup: true` on an individual host entry.

---

## Migrating from an older version

The config file was renamed from `~/.ssh_hosts.yml` to `~/.ssh_connect.yml`, and the
format changed from a plain host list to a structured document with `settings` and `hosts` keys.

```bash
mv ~/.ssh_hosts.yml ~/.ssh_connect.yml
```

Then wrap your existing entries under a `hosts:` key and add a `settings:` block:

```yaml
# before
- host: 10.0.0.1
  name: MyServer

# after
settings:
  theme: material
  resolve_dns: true
  skip_key_setup: false

hosts:
  - host: 10.0.0.1
    name: MyServer
```

The old plain-list format still works but prints a warning on startup.

---

## License

MIT — feel free to modify or integrate into your workflow.
