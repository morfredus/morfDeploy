# Journal des versions - morfDeploy

Le format s'inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/)
et du [versionnage sémantique](https://semver.org/lang/fr/).

## [0.1.1] - 2026-08-16

### Ajouté

- **Émetteur d'événements de compilation** (`morfdeploy/activity.py`). `build_as_user`
  (backends systemd et Windows) signale désormais chaque compilation au domaine Monitor
  de morfAnalytics : projet, machine, début/fin, résultat (succès/échec), preset.
  morfDeploy sait ce qu'il compile — source exacte des événements, rien de deviné.
  **Best-effort et sans dépendance** : émis seulement si l'URL est connue, via la
  variable `MORFANALYTICS_ACTIVITY_URL` **ou** le fichier `/etc/morfsystem/monitor-activity-url`
  (robuste sous `sudo`, qui efface l'environnement). Jamais bloquant si morfAnalytics
  est injoignable.

## [0.1.0] - 2026-08-11

Première version en dépôt autonome. morfDeploy existait déjà et était utilisé par
tout le parc, mais sans identité propre : son code vivait dans `morfTools/lib/morfdeploy`
et était vendoré de là dans chaque projet. Il est désormais promu en bibliothèque
autonome, sur le modèle de morfBeacon.

### Ajouté

- **Dépôt dédié** avec son identité : `VERSION`, `README.md` / `README.fr.md`,
  `CHANGELOG.md`, `LICENSE` (GPL-3.0-only). Le paquet `morfdeploy/` est repris
  **à l'identique** de `morfTools/lib/morfdeploy` (aucune divergence introduite) :
  cette version 0.1.0 fige l'existant comme point de départ du cycle propre à
  morfDeploy.

### Contexte

- **Cœur d'orchestration multi-plateforme** : install / update / uninstall /
  status / config d'un service morfSystem, mêmes étapes partout, backend par
  système (systemd, service Windows, launchd accommodé).
- **Vendoré** dans `third_party/morf/morfdeploy` chez les consommateurs, resynchronisé
  avant compilation ; la source de vérité est ce dépôt.

### À suivre (hors périmètre de cette version)

- Bascule des scripts `sync-morf` des projets vers ce dépôt (au lieu de
  `morfTools/lib/morfdeploy`), et adoption de morfTools comme simple consommateur.
