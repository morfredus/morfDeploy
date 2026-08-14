# Contributing to morfDeploy

Thanks for your interest! morfDeploy is a small, shared library: it must stay
**tiny, portable and dependency-light**, because it is vendored into every
morfSystem project and drives their install/update/uninstall.

## 1. Philosophy

- **One orchestration core, native mechanisms per OS.** The four steps
  (install / update / uninstall / status) live once, platform-agnostic, in
  `core.py`. Only the *service manager* differs, and that is what a backend
  describes.
- **Python standard library only.** No third-party runtime dependency: the tool
  must run on a bare Windows, Linux x64 or Raspberry Pi (ARM64), including from
  `sudo`, without a package install step.
- **Portable by construction.** No assumption about the host beyond what the
  backend abstracts. The same commands behave identically everywhere.
- **Non-destructive by default.** Config completion adds missing keys, never
  edits existing values; a backup precedes any write; uninstall keeps the
  configuration.

## 2. Layout

- `core.py` - the `Deployer`: the four steps, platform-agnostic.
- `manifest.py` - reads and validates `service.json`.
- `configmerge.py` - non-destructive config completion.
- `backends/` - one module per service manager (`systemd`, `windows`, `launchd`).
- `cli.py` - the command-line entry point projects call from `service.py`.

## 3. Source of truth and vendoring

This repository is the **source of truth**. Consuming projects hold a vendored
copy under `third_party/morf/morfdeploy`, resynchronised by their
`scripts/sync-morf` script. **Never edit a vendored copy**: fix it here, then
resync. `morf doctor` reports drift.

## 4. Changes

- Keep the public surface small; resist adding options that a `service.json`
  field could express instead.
- Any behaviour change is documented in `CHANGELOG.md` and bumps `VERSION`.
- A change that alters a backend must be reasoned about for the other two.

## License

GPL-3.0-only - © 2026 morfredus (Frédéric Biron).
