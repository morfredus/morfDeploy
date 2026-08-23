# morfDeploy

*Read in another language: **English** (this document) · [Français](README.fr.md).*

[![Version](https://img.shields.io/badge/version-0.17.7-blue)](CHANGELOG.md)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-GPL--3.0--only-blue)

**One orchestration core, native mechanisms per operating system.** morfDeploy
installs, updates and uninstalls a morfSystem service the same way everywhere -
Windows, Linux x64 and Raspberry Pi (ARM64) - while delegating the one thing that
truly differs to a per-platform backend: the service manager.

It is the shared deployment foundation of morfSystem. Like morfBeacon, it lives in
its **own repository** (this one is the source of truth) and is **vendored** into
each consuming project under `third_party/morf/morfdeploy`, resynchronised before
build. No project depends on fetching anything external to install.

## What a consuming project does

Each project ships a thin `service.py` at its root that adds the vendored copy to
the path and hands over to morfDeploy:

```python
sys.path.insert(0, str(HERE / "third_party" / "morf"))
from morfdeploy.cli import main
sys.exit(main([*sys.argv[1:], "--repo", str(HERE)]))
```

What the service *is* - its name, directory and configurations - is declared in a
`service.json` next to `service.py`. The four steps are identical everywhere; only
the backend changes.

```sh
sudo ./service.py install      # build if needed, install, start
sudo ./service.py update       # rebuild, replace the binary, restart
sudo ./service.py uninstall    # deregister, keeping the configuration
sudo ./service.py purge <id>…  # erase declared data categories (see below)
./service.py status            # what the system says about it
```

Compile duration sent to morfAnalytics (Monitor) is the real ninja wall time,
from the first compiled file to link. A no-op `cmake --build` is no longer
reported as a one-second compile.

## Purging data

A project may declare, in `service.json`, the categories of data it knows how to
erase. The identifiers are free - a project announces `database`, `cache`,
`history`, `thumbnails` or anything else without morfdeploy changing - and each
carries a human label and a `destructive` flag.

```jsonc
"purge": [
  { "id": "cache",    "label": "Thumbnails and cache",
    "type": "path", "base": "state", "paths": ["cache"] },
  { "id": "database", "label": "Photo index (irreversible)", "destructive": true,
    "type": "path", "base": "state", "paths": ["morfphoto.db"] },
  { "id": "history",  "label": "Analytics history", "destructive": true,
    "type": "command", "command": ["__BINARY__", "purge", "history"],
    "dry_run": true }
]
```

Two kinds of category:

- **`path`** - morfdeploy removes files or directories, resolved under a base
  (`state` / `config` / `app`). A path that escapes its base (`..`) is refused.
- **`command`** - morfdeploy hands the erasure to the project's own entry point,
  for data a path cannot express (part of a shared database, say). Placeholders
  `__BINARY__`, `__STATE_DIR__`, `__CONFIG_DIR__`, `__APP_DIR__` are substituted.

A `path` category may add **`from_config`** for data the admin can relocate: it
names a key in the deployed config whose value, when set, becomes the target;
when the key is absent or empty, the default `base`/`paths` applies. morfdeploy
reads the real location from the service's own config rather than guessing it.

```jsonc
{ "id": "vault", "label": "Encrypted vault", "destructive": true, "type": "path",
  "from_config": "vault_root", "base": "state", "paths": ["vault"] }
```

By default the config value IS the target (`from_config_kind: "path"`). When the
key names a *parent directory* holding named files (a cache dir with one file per
history), set `from_config_kind: "dir"`: `paths` are joined onto the value, and
`default_dir` gives the fallback directory under `base` when the key is unset.

```jsonc
{ "id": "sitewatch-history", "label": "SiteWatch history", "destructive": true,
  "type": "path", "from_config": "sitewatch_cache_dir", "from_config_kind": "dir",
  "base": "app", "default_dir": "cache", "paths": ["sitewatch-history.sqlite"] }
```

```sh
sudo ./service.py purge cache database   # named categories
sudo ./service.py purge --all            # every declared category
./service.py purge --all --dry-run       # show what would go, remove nothing
```

`--dry-run` walks the same resolution path as the real run; only the final act
differs. A `command` category is simulated only if the project says its command
honours `--dry-run` (`dry_run: true`); otherwise the dry run reports that the
category cannot be simulated rather than pretending it ran. Administrator rights
are required by the real purge, never by a dry run.

A real purge is **refused while the service is running** -- erasing a database it
may be mid-write to would corrupt it. Stop the service first, or pass `--force`
to override the guard. `uninstall` also takes `--dry-run`, listing what it would
deregister and (with `--purge`) remove, without touching anything.

## System dependencies

A project declares the system packages it needs as **needs**, not as install
commands. morfDeploy detects the platform's package manager and resolves the
right package; nothing global is ever touched -- only the declared packages.

```jsonc
"system_dependencies": [
  { "id": "qt-serialport", "label": "Qt SerialPort", "required_for": ["ld2410c"],
    "packages": { "debian": ["qt6-serialport-dev"] }, "required": false }
]
```

`required: false` is an **optional** capability: its absence disables that
capability (morfSensor's radar driver, morfPhoto's exiftool) but never blocks the
rest. `required: true` stops the operation until it is satisfied.

The cycle is **detect → present → validate → install → verify**, and it never
installs silently:

```sh
./service.py deps --list        # JSON: declared deps + present/missing (discovery)
./service.py deps --dry-run     # show what would be installed, change nothing
sudo ./service.py deps --yes    # install the missing declared packages, then verify
```

`install` (and `deploy`) runs the same resolution before the build: a missing
required package stops there with a clear message rather than as a cryptic build
error; a missing optional one only warns. On a terminal it asks; non-interactive,
`--yes` authorises it (never silent without it). `--dry-run` shows the plan. A
platform with no supported package manager, or a dependency with no package
declared for it, is reported honestly rather than guessed.

## Build dependencies

Distinct from system dependencies (which a service needs to *run*), these are the
libraries a project needs to *compile* -- what a `find_package` looks for. A
project declares a **logical id**; morfDeploy maps it to the package per platform
(a central registry: `openssl` -> `libssl-dev`, `libssh2` -> `libssh2-1-dev`, …)
and resolves it **before** the build, so a missing OpenSSL is a clear stop rather
than a `find_package` failure fifteen projects deep.

```jsonc
"build_dependencies": [
  { "id": "openssl", "required": true },
  { "id": "libssh2", "required": true }
]
```

```sh
./service.py build-deps --list      # JSON: declared build deps + present/missing
./service.py build-deps --dry-run   # show what would be installed, change nothing
sudo ./service.py build-deps --yes  # install the missing build libraries, verify
```

`install` runs this before compiling. On a platform with a package manager
(Debian) it detects, presents and installs (with confirmation, never silently).
On a toolchain with **no** package manager (the official Qt MinGW on Windows) it
**announces** the needs and lets the build's own `find_package` be the last word,
never blocking a build that might succeed with a library present in a way it
cannot detect.

## Layout

```
morfdeploy/
├── cli.py            command-line entry point (install/update/uninstall/purge/deps/build-deps/status/config)
├── core.py           the Deployer: the four steps, platform-agnostic
├── manifest.py       reads and validates service.json
├── configmerge.py    non-destructive config completion (adds missing keys, never edits values)
└── backends/
    ├── systemd.py    Linux (systemd units, StateDirectory...)
    ├── windows.py    Windows service
    └── launchd.py    macOS (accommodated, not supported)
```

Officially supported: Windows x64, Linux x64, Linux ARM64 (Raspberry Pi). macOS is
architecturally accommodated but not supported.

## Consuming and updating

Do not edit vendored copies. The source of truth is this repository. Projects
resynchronise their `third_party/morf/morfdeploy` with their `scripts/sync-morf`
script (set `MORF_SRC_BASE` if the repositories live elsewhere). `morf doctor`
reports any drift between a vendored copy and this source.

## License

GPL-3.0-only - © 2026 morfredus (Frédéric Biron).
