# ssh_connect

`ssh_connect` is an interactive SSH host selector that stores its hosts in a real
OpenSSH config file. Instead of keeping a private host list, it manages
`~/.ssh/ssh_connect.conf`, which is pulled into your normal SSH setup with a single
`Include` directive.

That means every host you add is immediately usable by `ssh`, `scp`, `rsync`, `git`
and VS Code Remote-SSH, and features like `ProxyJump` work without ssh_connect
knowing anything about them.

---

## Features

- Interactive TUI menu (non-fullscreen, blends naturally into the shell)
- Hosts live in a standard OpenSSH config file, shared with every other SSH tool
- `sc user@host` connects if the host is known, otherwise offers to add it
- Type-to-filter host selection, remembers the last connection
- On-demand reverse DNS to turn IP-named hosts into readable aliases
- Automatic detection of missing authorized keys, with interactive key upload
- `sshpass` support for appliances that only accept passwords
- Multiple color themes

---

## Installation

```
git clone https://github.com/corus87/ssh_connect.git
cd ssh_connect
./install.py
```

The installer creates a virtual environment, installs a wrapper into a writable
directory in your `$PATH`, optionally creates a shortcut (default `sc`), and offers
to add the include directive to `~/.ssh/config`.

If you skip the last step, add this line yourself at the **top** of `~/.ssh/config`:

```
Include ~/.ssh/ssh_connect.conf
```

It has to be at the top: OpenSSH keeps the first value it finds for each keyword.

---

## Usage

| Command                | Description                                              |
| ---------------------- | -------------------------------------------------------- |
| `sc`                   | interactive selector                                     |
| `sc web01`             | connect to a known alias                                 |
| `sc root@192.169.0.10`    | connect, or offer to add the host if it is unknown       |
| `sc 192.169.0.10:2222`    | same, with an explicit port                              |
| `sc --list`            | list configured hosts                                    |
| `sc --edit`            | open `~/.ssh/ssh_connect.conf` in `$EDITOR`              |
| `sc --settings`        | open `~/.ssh/ssh_connect.yml` in `$EDITOR`               |
| `sc --resolve`         | name unnamed hosts from reverse DNS (see below)           |
| `sc --themes`          | list available themes                                    |

In the selector: arrow keys or `Ctrl-N`/`Ctrl-P` to move, type to filter,
`Enter` to connect, `Esc` to cancel.

### Adding hosts

`sc deploy@192.169.0.99` looks for an entry with that hostname and user. If none exists,
it asks whether to add one, suggests an alias, and writes a normal `Host` block:

```
Host deploy-192.169.0.99
    HostName 192.169.0.99
    User deploy
```

User and hostname are matched together, so `root@192.169.0.10` and `username@192.169.0.10`
end up as two separate entries. If a hostname is given without a user and matches
several entries, the selector asks which one you mean.

### Naming hosts from DNS

After a migration your hosts are often named after their IP. `sc --resolve` does a
reverse lookup for all of them at once and walks you through the results:

```
$ sc --resolve
Resolving 12 address(es)...

Enter accepts, edit to change, clear the line to skip, Ctrl-C to stop.

192.169.0.10  ->  truenas.fritz.box
Alias: Truenas

192.169.0.11  ->  homeassistant.fritz.box
Alias: Homeassistant
```

The header shows the current alias and the name that was found, the prompt below is
pre-filled with the proposal and editable. Ctrl-C stops the run but keeps everything
you already confirmed. Only the `Host` line is rewritten, the rest of the block stays
as it is.

By default only hosts whose alias still equals their connection target are offered,
so entries you already named are left alone. Options:

| Flag / argument      | Effect                                                 |
| -------------------- | ------------------------------------------------------ |
| `--fqdn`             | propose the full name instead of the first label       |
| `--all`              | review every host, including already named ones        |
| `sc --resolve web01` | only this host                                         |

Lookups run in parallel with a 3 second overall timeout, so a slow or unreachable
DNS server costs you three seconds in total, not per host. Hosts that cannot be
resolved are listed at the end and left untouched.

### Key upload

Before connecting, ssh_connect checks with `BatchMode=yes` whether a key-based login
works. If the host wants a password instead, it offers to upload a public key from
`~/.ssh` via `ssh-copy-id`. Declining once offers to silence the prompt for that host
permanently.

This applies to every host in the config, including ones you added by hand.

---

## Configuration

### Hosts: `~/.ssh/ssh_connect.conf`

A plain OpenSSH config file. Edit it with `sc --edit` or any editor:

```
Host web01
    HostName web01.internal.example.com
    User admin

Host jump-target
    HostName 192.168.5.5
    Port 2222
    ProxyJump web01
```

### Settings: `~/.ssh/ssh_connect.yml`

Only holds options that have no equivalent in the OpenSSH config format:

```yaml
theme: material
max_rows: 15              # hosts per page in the selector

hosts:
  appliance:
    password: secret        # login via sshpass
  legacy-box:
    skip_key_setup: true    # never offer to upload a public key
```

Keys under `hosts` are the aliases from `ssh_connect.conf`.

`max_rows` is the number of hosts shown before the list starts scrolling. It is
capped to what the terminal can actually display, so a large value simply means
"as many as fit".

---

## Upgrading from 1.x

Version 2.0 changes the config format and location. Run the migration once:

```
python3 migrate_v1_to_v2.py            # reads ~/.ssh_connect.yml
python3 migrate_v1_to_v2.py other.yml  # or an explicit path
```

It converts `~/.ssh_connect.yml` into `~/.ssh/ssh_connect.conf` and
`~/.ssh/ssh_connect.yml`. The old file is left untouched.

What changed:

- Hosts are stored as OpenSSH `Host` blocks instead of a YAML list
- Connecting by index (`ssh_connect 3`) is gone, use the alias or `user@host`
- Automatic DNS resolution on every start is gone, the list shows aliases
  and hostnames only. Use `--resolve` on demand instead
- All `SSH_CONNECT_*` environment variables are gone, everything lives in the
  settings file now
- `skip_key_setup` is per host only, the global switch is gone
- `j`/`k` no longer move the cursor, those keys type into the filter now

---

## License

MIT — feel free to modify or integrate into your workflow.
