# Changelog

## 2.0.0

Hosts are now stored in a real OpenSSH config file instead of a private YAML list.
`~/.ssh/ssh_connect.conf` is pulled into the normal SSH setup with an `Include`
directive, which makes every host directly usable by `ssh`, `scp`, `rsync`, `git`
and VS Code Remote-SSH.

Run `python3 migrate_v1_to_v2.py` once to convert an existing 1.x setup.

### Added

- `sc user@host` connects to a known host or offers to add it, matching on
  hostname and user so `root@10.0.0.10` and `patrick@10.0.0.10` stay separate
- `--settings` opens the settings file in `$EDITOR`
- Type-to-filter in the host selector
- Public key selection shows fingerprints
- The selector starts on the host you connected to last
- `--resolve` renames hosts from reverse DNS interactively, with `--fqdn` and `--all`
- `max_rows` setting controls how many hosts the selector shows per page
- New hosts get an alias suggested from a reverse lookup, with the user appended
- Aliases are validated, so an entry can no longer define several `Host` patterns
- The host list shows `user@hostname` when an entry sets a user

### Changed

- Hosts live in `~/.ssh/ssh_connect.conf`, app settings in `~/.ssh/ssh_connect.yml`
- `--edit` opens the host config, not the old YAML file
- Connecting hands over to `ssh <alias>`, so `ProxyJump`, `IdentityFile` and every
  other OpenSSH option are resolved by ssh itself
- Key upload is offered for every host in the config, including hand-written ones
- Declining a key upload offers to silence the prompt for that host permanently
- Both config files are created with `0600`, `~/.ssh` with `0700`

### Removed

- Connecting by index (`ssh_connect 3`)
- Automatic DNS resolution on every start and the `resolve_dns` setting, replaced
  by the on-demand `--resolve` command
- The global `skip_key_setup` setting, it is per host only now
- All `SSH_CONNECT_*` environment variables (`SSH_CONNECT_HOSTS_FILE`,
  `SSH_CONNECT_SORT`, `SSH_CONNECT_THEME`), the settings file is the only source now
- Cursor movement with `j`/`k`, those keys type into the filter now

## 1.0.0

Initial release.
