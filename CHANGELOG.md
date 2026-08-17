# Journal des versions - morfDeploy

Le format s'inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/)
et du [versionnage sémantique](https://semver.org/lang/fr/).

## [0.5.0] - 2026-08-17

### Ajouté

- **`from_config` sur une catégorie de purge `path`** : pour une donnée que
  l'administrateur peut relocaliser (le coffre `vault_root` / les données
  `storage_root` de morfCollector), la catégorie nomme une clé de la config
  **déployée** ; morfdeploy en lit la valeur pour cibler le vrai emplacement.
  Clé absente ou vide → le `base`/`paths` par défaut s'applique. morfdeploy ne
  devine jamais un chemin configurable : le projet dit où le lire, morfdeploy le
  lit dans la config du service (jamais dans le fichier partagé du parc).

## [0.4.0] - 2026-08-17

### Ajouté

- **Garde-fou « service actif » sur la purge réelle.** Effacer une donnée qu'un
  service tourne peut être en train d'écrire (sa base SQLite) la corromprait :
  `purge` refuse désormais tant que le service est **clairement en cours
  d'exécution**, avec un message clair (arrêter le service, ou `--force`).
  Nouvelle méthode backend `is_active` (systemd `is-active`, Windows `sc query`
  RUNNING / tâche `Running`) ; défaut `False` pour un backend qui ne sait pas
  trancher, afin de ne jamais bloquer sur un doute. Le dry-run signale que la
  purge réelle serait refusée. `--force` outrepasse.
- **`uninstall --dry-run`** : liste ce qui serait désinscrit et, avec `--purge`,
  ce qui serait supprimé (config, binaire, répertoire de config), sans rien
  toucher ni exiger de privilèges. Le dry-run traverse la chaîne (§10) au lieu de
  s'arrêter au bord de l'action.

## [0.3.0] - 2026-08-17

### Ajouté

- **`service.py purge --list` : découverte lisible par machine.** Émet en JSON les
  catégories déclarées (`id`, `label`, `destructive`, `type`) et sort, sans rien
  supprimer. Primitive destinée à un orchestrateur (morfTools) : il interroge
  chaque clone pour savoir ce qu'il sait effacer, sans jamais lire lui-même
  `service.json` (le projet annonce, l'orchestrateur consomme). Répond depuis le
  seul manifeste : ni backend, ni privilèges, ni support de plateforme requis, et
  une liste **vide** (rc 0) pour un service sans bloc `purge`, jamais une erreur.
  `--list` est une requête : le combiner à des `id`, `--all` ou `--dry-run` est refusé.

## [0.2.0] - 2026-08-17

### Ajouté

- **Action `purge` : effacement sélectif des données déclarées par le projet.**
  Un projet annonce dans `service.json` un bloc `purge` : une liste de catégories
  aux **identifiants libres** (pas d'énumération figée - `database`, `cache`,
  `history`, `thumbnails`, `sync-state`... au choix du projet), chacune avec un
  **label humain** et un drapeau **`destructive`**. Deux natures d'effacement :
  - `type: "path"` : morfdeploy supprime des fichiers/dossiers résolus sous une
    base (`state` / `config` / `app`). Un garde-fou refuse tout chemin qui
    s'échappe de sa base (`..`).
  - `type: "command"` : morfdeploy transmet l'intention au propre point d'entrée
    du projet (utile pour vider une partie d'une base partagée qu'un chemin ne
    peut pas exprimer). Jetons substitués : `__BINARY__`, `__STATE_DIR__`,
    `__CONFIG_DIR__`, `__APP_DIR__`.

  Usage : `service.py purge <id>... [--all] [--dry-run]`. morfdeploy exécute une
  intention déclarée ; il n'apprend jamais où un service range sa SQLite.

- **`--dry-run` sur `purge`, dès l'introduction de l'action.** Le mode simulation
  parcourt **exactement le même chemin de résolution** que l'exécution réelle
  (mêmes catégories, mêmes chemins/commandes) : seul l'acte final diffère. Une
  catégorie `command` n'est simulée que si le projet déclare que sa commande
  supporte `--dry-run` (`dry_run: true`) ; sinon la simulation ne lance **rien**
  et le dit, plutôt que de laisser croire qu'elle a agi.

### Validation stricte

- Chargement du manifeste : catégorie sans `id`, `id` dupliqué, `type` inconnu,
  `path` sans `paths`, `command` sans `command`, `base` hors
  `state`/`config`/`app` → erreur nette, projet nommé.
- CLI `purge` : `--all` combiné à une liste d'`id` est refusé, ni l'un ni l'autre
  est refusé, une catégorie inconnue liste les catégories valides. Les droits
  administrateur ne sont exigés que par l'exécution réelle, jamais par `--dry-run`.

### Rétrocompatibilité

- Un `service.json` sans bloc `purge` se charge comme avant : le projet n'expose
  simplement aucune catégorie purgeable. `uninstall --purge` (effacement
  monolithique config + binaire) reste inchangé, considéré comme raccourci legacy.

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
