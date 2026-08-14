# Roadmap

## Done

- **v0.1.0** - Promotion to a standalone repository, on the model of morfBeacon:
  own identity (VERSION, README FR/EN, CHANGELOG, LICENSE) and the `morfdeploy`
  package frozen verbatim from `morfTools/lib/morfdeploy`. One orchestration core
  (install / update / uninstall / status / config), one backend per service
  manager (systemd, Windows, launchd accommodated), non-destructive config
  completion. Consumed by the morfSystem projects via `third_party/morf/morfdeploy`.

## Planned

- **Parc migration** - every project's `sync-morf` script sources morfdeploy from
  this repository (in progress); make morfTools a plain consumer; then retire the
  transitional `morfTools/lib/morfdeploy` fallback.
- **Tests** - a headless smoke test of the manifest reader and the config merge,
  runnable without touching a real service manager.

## Non-goals

- Becoming a general-purpose deployment framework. morfDeploy installs morfSystem
  services with native mechanisms; it is not a container orchestrator nor a
  configuration-management system.
