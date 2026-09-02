# Journal des versions - morfDeploy

Le format s'inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/)
et du [versionnage sémantique](https://semver.org/lang/fr/). 

## [0.19.0] - 2026-09-03

### Added

- **Reproducible ARM64 cross-compilation from x86_64** (WSL/Linux), for the parc's
  `linux-arm64-cross` CMake preset. A single canonical toolchain file
  (`morfdeploy/cmake/linux-aarch64.cmake`, vendored into every project via
  `sync-morf`) targets Debian Trixie arm64 with unified env vars (`MORF_SYSROOT`,
  `MORF_CROSS_PREFIX`, `MORF_QT_HOST_PATH`) and separates host build tools from the
  target Qt6. Qt's `moc`/`rcc`/`uic` (arm64) run under qemu-user (`QEMU_LD_PREFIX`
  = the sysroot), so no version-matched host Qt is required.
- `scripts/build-arm64-sysroot.sh`: builds a Debian Trixie arm64 sysroot once
  (debootstrap + qemu-user-static + the parc's Qt6 packages), reproducible and
  usable offline afterwards. The Raspberry Pi is never required. The native
  `linux-arm64` build on the Pi stays the reference path; this is the cross path.
- Validated end to end on morfPhoto: `cmake --preset linux-arm64-cross` produces an
  `ELF 64-bit ARM aarch64` binary from x86_64 WSL.

## [0.18.0] - 2026-08-23

### Ajouté

- Contrat de permissions pour les fichiers de config sous `/etc` : mode
  déterministe posé au packaging, `0644 root:root` par défaut (plus le mode
  hérité du checkout git, qui variait selon la machine et l'umask). Un fichier
  `configs` du manifeste peut déclarer un `mode` restrictif (ex. `"0640"` pour un
  secret) ; le `postinst` le redonne alors au groupe du service (`chown
  root:<service>`) pour qu'il reste lisible par son compte non-root. Ce n'est pas
  une règle absolue 0644 : c'est un défaut sûr, surchargeable là où un secret
  l'exige.

## [0.17.8] - 2026-08-23

### Corrigé

- Empaquetage : `build-info.json` root dans un dossier user (cas `morf.py
  upgrade` puis `package-all` en user). Unlink puis réécriture, sinon tampon
  temporaire même si le dossier est inscriptible. Copie de `VERSION` sous
  `/opt/<service>/`.

## [0.17.7] - 2026-08-23

### Corrigé

- Empaquetage : si `build-info.json` n'est pas inscriptible (dossier de build
  resté `root` après un cmake en sudo), tamponnage dans un répertoire temporaire
  au lieu d'un `PermissionError` qui abandonne le `.deb`.

## [0.17.6] - 2026-08-23

### Corrigé

- `prerm` : à l'upgrade, `systemctl stop` seulement. `disable --now` est réservé
  à la désinstallation. Sinon un `enable --now` avalé par `|| true` laissait le
  service désactivé (morfMonitor mis à jour depuis sa propre page).

## [0.17.5] - 2026-08-23

### Corrigé

- `postinst` d'un `.deb` avec helper : le dossier `/usr/lib/morfsystem/<service>`
  est aussi `chown root:<compte>` et `chmod 750`. Sans ça, après `dpkg` le
  binaire 4750 existait mais le service ne pouvait pas le parcourir.

## [0.17.4] - 2026-08-21

### Corrigé

- Installation du helper privilégié : le dossier /usr/lib/morfsystem/<service> reçoit le groupe du compte de service (comme le fichier) pour rester traversable. Il restait en root:root 0750, rendant un helper pourtant bien installé « introuvable » à l'exécution par le service non privilégié.

## [0.17.3] - 2026-08-21

### Corrigé

- Sur MinGW, le packaging passe a CMake les chemins OpenSSL explicites
  (include + `libcrypto.dll.a` / `libssl.dll.a`) et ajoute le prefix MSYS2 a
  `CMAKE_PREFIX_PATH`. FindOpenSSL survit a un reset de cache.

## [0.17.2] - 2026-08-21

### Corrigé

- La durée envoyée à morfAnalytics mesure le vrai travail de compilation
  (premier compilateur jusqu'à la fin), plus un `cmake --build` déjà à jour
  d'une seconde. Les allers-retours sans fichier à recompiler ne sont plus
  signalés. `duration_s` est calculé sur des horodatages flottants.

## [0.17.1] - 2026-08-20

### Corrigé

- Une installation ou une mise à jour lancée depuis le clone installe aussi le
  `helper_binary` Linux déclaré par le service, avec les mêmes permissions
  restreintes que le paquet Debian. Un agent installé ainsi peut donc effectuer
  son action privilégiée sans étape manuelle supplémentaire.

## [0.17.0] - 2026-08-20

### Ajouté

- Un service peut déclarer un `helper_binary` Linux. Le paquet Debian le place
  hors du répertoire applicatif, root-owned et exécutable seulement par le
  compte de service : une API non privilégiée peut ainsi déléguer une action
  strictement définie sans devenir root.

## [0.16.0] - 2026-08-20

### Corrigé

- Le packaging Windows reconnaît les exécutables MinGW qui ne dépendent pas de
  Qt. Leur passage attendu dans `windeployqt` ne bloque plus la création de
  l'archive et les DLL de toolchain restent collectées.

## [0.15.0] - 2026-08-20

### Corrigé

- Le packaging Windows utilise maintenant la même détection portable de
  toolchain que les builds de service. La racine OpenSSL est déduite de
  `openssl` présent dans le PATH, sans chemin MSYS2 figé.

## [0.14.0] - 2026-08-19

### Ajouté

- **Action `package`** (Phase 2) : produit le(s) livrable(s) de la plateforme
  courante à partir d'un binaire **prouvé**. Piloté par `morfproject.json`
  (targets) + `service.json` (manifeste).
  - Ne package que les targets `morfdeploy` **natives** (os+arch) ; les autres
    sont signalées et ignorées (aucune compilation croisée supposée). `--target`
    force une target native ; `--no-build` réutilise le binaire existant.
  - **Barrière de provenance** (`build-info.json`) : refus si absent, si
    `dirty` != `false` (true **ou** null), si le commit ≠ `HEAD`, si la version ≠
    `VERSION`, ou si plateforme/arch ≠ cible. **Jamais** de repli sur un ancien
    binaire après échec de build.
  - **`.deb`** : arbo `/opt` `/etc` `/var/lib` `/lib/systemd/system/<svc>.service`
    (unité du projet, placeholders résolus) ; `Depends` = **union triée** de
    `dpkg-shlibdeps` (libs liées du binaire) et du **runtime explicite**, les deux
    origines **affichées séparément** avant fusion, jamais de paquet `-dev` ;
    configs en `conffiles` (préservées à l'upgrade) ; `postinst`/`prerm`
    (utilisateur dédié + `systemctl enable/disable`).
  - **`.zip`** (Windows) : bundle windeployqt + config + `install-service.ps1` /
    `uninstall-service.ps1` (tâche planifiée SYSTEM). **Vérifié** de bout en bout.
- **Build mutualisé** : plusieurs targets partageant le même preset ne compilent
  qu'une fois.

### Modifié

- **Architecture de provenance normalisée** : `detect_platform_arch` renvoie
  `x86_64` (et non `amd64`) sous Linux x64, pour coïncider avec `platform.arch`
  des targets ; le nom Debian (`amd64`) reste dans `package.architecture`.

## [0.13.1] - 2026-08-19

### Corrigé

- **Validation du format `{build, runtime}`** dans `_parse_system_deps` : la
  0.13.0 exposait les accesseurs build/runtime mais la validation au chargement
  rejetait encore une famille déclarée en objet (« lists no package »). Elle
  accepte désormais la liste plate héritée **et** `{build, runtime}` (l'un des
  deux non vide suffit - `exiftool` est runtime-only), en conservant la forme.

## [0.13.0] - 2026-08-19

### Ajouté

- **Séparation build/runtime des dépendances système** (préparation du `Depends`
  d'un `.deb`, Phase 2). `SystemDependency` accepte, par famille, soit la liste
  plate historique (interprétée comme **build**), soit `{ "build": [...],
  "runtime": [...] }`. Nouveaux accesseurs `build_packages(family)` /
  `runtime_packages(family)`. `sysdeps.resolve()` (vérification **avant**
  compilation) n'utilise que **build** ; le **runtime** alimentera le `Depends`
  du paquet, jamais déduit d'un nom `-dev`. Un besoin runtime doit être déclaré
  explicitement (la liste plate héritée n'en déclare aucun).

## [0.12.0] - 2026-08-19

### Ajouté

- **Lecteur `morfproject.json` autonome** (`morfdeploy/morfproject.py`, schéma
  v1) - fondation de la Phase 2 (`package`). morfdeploy lit lui-même ce dont il
  est consommateur (schéma, `project.id`/`type`, provider par défaut, targets avec
  `platform`, `build.preset`, `package.format` et override de provider), sans
  dépendre de morfTools. Rejette une `schema_version` inconnue, normalise les
  architectures (`x86_64`/`arm64`), erreurs explicites nommant le champ fautif.
  Même contrat observable que le lecteur de morfTools (copies vendorées séparées,
  contrat identique).

## [0.11.0] - 2026-08-19

### Ajouté

- **Action `build-info`** : écrit `build-info.json` à côté du binaire déjà
  compilé, **sans compiler**. Localise l'artefact par la convention autoritaire de
  morfdeploy (`locate_binary`) puis appelle le helper de provenance. C'est le
  point d'appui de `morf build` pour marquer un service après compilation :
  l'orchestrateur n'a **aucune heuristique de localisation** propre, la seule
  source de vérité du layout de build reste morfdeploy. Manifeste seul (aucun
  backend, aucun privilège) ; échoue clairement si aucun binaire n'est présent.

## [0.10.1] - 2026-08-19

### Modifié

- **`build-info.json` conserve le SHA Git complet.** `commit` porte désormais le
  SHA entier (l'identifiant de provenance et la clé de détection de conflit) ; le
  hash court reste disponible sous `commit_short`, pour l'affichage. Deux builds
  peuvent partager un préfixe court : la comparaison doit porter sur le SHA entier.

## [0.10.0] - 2026-08-19

### Ajouté

- **Provenance de build (`build-info.json`)** — première pierre du chantier de
  packaging. Un helper partagé `provenance.write_build_info(...)` écrit, **après
  un build réussi et à côté de l'artefact**, un `build-info.json` : projet,
  version (lue du `VERSION`), **commit** court, **dirty** (état réel des sources),
  plateforme et architecture **détectées** en noms de cibles canoniques
  (`windows-x86_64`, `linux-amd64`, `linux-arm64`), preset, nom d'artefact et date
  UTC. `Deployer.ensure_binary` l'appelle automatiquement, **uniquement dans la
  branche qui compile réellement** (jamais quand le binaire était déjà là).
  - La provenance concerne **ce binaire précis** : le fichier est déposé à côté
    de l'artefact, pas seulement dans le dossier de build.
  - `dirty` reste `null` si git n'a pas pu être interrogé — un état inconnu, jamais
    confondu avec « propre ».
  - Ce module **écrit** ; la future chaîne de distribution ne fera que **lire** et
    ne régénérera jamais ce fichier. Un binaire sans provenance, ou dont le commit
    diverge de `HEAD`, sera traité comme non prouvé par le packaging.

## [0.9.0] - 2026-08-18

### Ajouté

- **Contrat `build_dependencies` : les bibliothèques nécessaires à la
  COMPILATION**, distinct de `system_dependencies` (exécution). Un projet déclare
  un **besoin logique** (`{"id": "openssl", "required": true}`) ; morfDeploy le
  mappe au paquet selon la plateforme via un **registre central** (`builddeps.py`
  : openssl→libssl-dev, libssh2→libssh2-1-dev, nlohmann-json→nlohmann-json3-dev,
  zlib→zlib1g-dev…) et le résout **AVANT le build**. Nouvelle action
  `service.py build-deps` (`--list` JSON, `--dry-run`, `--yes`), et résolution
  intégrée à `install` avant `ensure_binary`.
  - Un OpenSSL manquant s'arrête avec un message clair, pas une erreur
    `find_package` en plein build.
  - **Sur une toolchain sans gestionnaire de paquets** (Qt officielle sous
    Windows) : morfDeploy **annonce** le besoin et laisse le `find_package` du
    build comme dernier mot, sans bloquer un build qui pourrait réussir (la lib
    peut être présente d'une façon qu'il ne détecte pas). Filet, pas mécanisme
    principal (§ « annoncer si aucune méthode fiable »).
  - Sur une plateforme avec gestionnaire (Debian) : détecte, présente, installe
    (avec validation / `--yes`), vérifie. Jamais silencieux, jamais de mise à
    niveau globale.

## [0.8.0] - 2026-08-18

### Corrigé

- **`build_as_user` (Windows) s'adapte à la toolchain réellement présente.** Le
  preset `mingw` fige les chemins MSYS2 d'une machine (`ninja`, `g++`, préfixe
  Qt) ; sur un autre poste (toolchain Qt officielle sous `C:/Qt`, MSYS2 absent)
  ces chemins n'existent pas et la compilation échoue (`ninja.exe … no such
  file`). Le backend détecte désormais ninja, le compilateur MinGW et le préfixe
  Qt sur le PATH/env et **surcharge** les valeurs figées par des `-D`, comme le
  fait déjà `morf build`. Passage en forme liste (plus de `shell=True`), donc
  aucun souci de quoting sur des chemins à espaces. Amélioration pure : si rien
  n'est détecté, la compilation retombe sur les valeurs du preset.

## [0.7.0] - 2026-08-18

### Ajouté

- **Gestion déclarative des dépendances système** (nouveau chantier). Un projet
  déclare `system_dependencies` dans `service.json` (id, label, `required_for`,
  `packages` par famille, `required`) comme des **besoins**, pas des commandes.
  morfDeploy détecte la plateforme et le gestionnaire (`apt`/`dnf`/`pacman`),
  résout le paquet, et suit le cycle **détecter → présenter → valider →
  installer → vérifier**. Nouveau module `sysdeps.py` + action `service.py deps`
  (`--list` découverte JSON, `--dry-run` plan, `--yes` autorisation).
  - **Jamais d'installation silencieuse** : interactif → demande ; non-interactif
    → `--yes` requis ; `--dry-run` → plan sans rien changer ; jamais de `apt
    upgrade` global (seuls les paquets déclarés).
  - **Obligatoire vs optionnel** : un `required` manquant interrompt proprement ;
    un optionnel manquant se contente d'un avis et n'empêche rien.
  - **`install`/`deploy`** résolvent les dépendances **avant le build** (un
    paquet obligatoire manquant s'arrête là, pas en erreur de build obscure).
  - **Portabilité** : le projet déclare le besoin, morfDeploy résout selon la
    plateforme. Une plateforme sans gestionnaire supporté, ou une dép. sans
    paquet pour elle, est signalée sans deviner. `install` gagne `--yes`.

## [0.6.0] - 2026-08-18

### Ajouté

- **`from_config_kind: "dir"` + `default_dir`** sur une catégorie de purge `path`.
  Quand la clé de config nomme un **dossier parent** (un cache contenant un
  fichier par historique) plutôt que la donnée elle-même, `dir` joint les `paths`
  à la valeur lue, et `default_dir` fournit le dossier de repli sous `base` si la
  clé est absente. `from_config_kind: "path"` (défaut) conserve le comportement
  « la valeur EST la cible ». Permet à morfAnalytics de déclarer proprement son
  historique SiteWatch (`sitewatch_cache_dir`, défaut app/cache).

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
