# morfDeploy

*Read in another language: **English** (this document) · [Français](README.fr.md).*

[![Version](https://img.shields.io/badge/version-0.1.0-blue)](CHANGELOG.md)
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
./service.py status            # what the system says about it
```

## Layout

```
morfdeploy/
├── cli.py            command-line entry point (install/update/uninstall/status/config)
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
