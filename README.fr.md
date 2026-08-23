# morfDeploy

*Lire dans une autre langue : [English](README.md) · **Français** (ce document).*

[![Version](https://img.shields.io/badge/version-0.17.8-blue)](CHANGELOG.md)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-GPL--3.0--only-blue)

**Un seul cœur d'orchestration, des mécanismes natifs selon le système.**
morfDeploy installe, met à jour et désinstalle un service morfSystem de la même
façon partout - Windows, Linux x64 et Raspberry Pi (ARM64) - en déléguant la seule
chose qui diffère vraiment à un backend par plateforme : le gestionnaire de
services.

C'est la fondation de déploiement partagée de morfSystem. Comme morfBeacon, elle
vit dans son **propre dépôt** (celui-ci est la source de vérité) et est **vendorée**
dans chaque projet consommateur sous `third_party/morf/morfdeploy`, resynchronisée
avant compilation. Aucun projet ne dépend d'un téléchargement externe pour
s'installer.

## Ce que fait un projet consommateur

Chaque projet embarque à sa racine un mince `service.py` qui ajoute la copie
vendorée au path et passe la main à morfDeploy :

```python
sys.path.insert(0, str(HERE / "third_party" / "morf"))
from morfdeploy.cli import main
sys.exit(main([*sys.argv[1:], "--repo", str(HERE)]))
```

Ce qu'est le service - son nom, son dossier, ses configurations - est déclaré dans
un `service.json` à côté du `service.py`. Les quatre étapes sont identiques
partout ; seul le backend change.

```sh
sudo ./service.py install      # compile si besoin, installe, démarre
sudo ./service.py update       # recompile, remplace le binaire, redémarre
sudo ./service.py uninstall    # désinscrit, en conservant la configuration
sudo ./service.py purge <id>…  # efface des catégories de données (voir plus bas)
./service.py status            # ce que le système en dit
```

La durée signalée à morfAnalytics (domaine Monitor) est celle du vrai ninja :
du premier fichier compilé jusqu'à la fin. Un `cmake --build` déjà à jour n'est
plus annoncé comme une compile d'une seconde.

## Purge des données

Un projet peut déclarer, dans son `service.json`, les catégories de données qu'il
sait effacer. Les identifiants sont **libres** - un projet annonce `database`,
`cache`, `history`, `thumbnails` ou autre chose sans que morfdeploy change - et
chacune porte un **label humain** et un drapeau **`destructive`**.

```jsonc
"purge": [
  { "id": "cache",    "label": "Miniatures et cache",
    "type": "path", "base": "state", "paths": ["cache"] },
  { "id": "database", "label": "Base d'indexation photo (irréversible)", "destructive": true,
    "type": "path", "base": "state", "paths": ["morfphoto.db"] },
  { "id": "history",  "label": "Historique analytics", "destructive": true,
    "type": "command", "command": ["__BINARY__", "purge", "history"],
    "dry_run": true }
]
```

Deux natures de catégorie :

- **`path`** - morfdeploy supprime des fichiers ou dossiers, résolus sous une base
  (`state` / `config` / `app`). Un chemin qui s'échappe de sa base (`..`) est refusé.
- **`command`** - morfdeploy confie l'effacement au propre point d'entrée du
  projet, pour une donnée qu'un chemin ne peut pas exprimer (une partie d'une base
  partagée). Jetons substitués : `__BINARY__`, `__STATE_DIR__`, `__CONFIG_DIR__`,
  `__APP_DIR__`.

Une catégorie `path` peut ajouter **`from_config`** pour une donnée que l'admin
peut déplacer : elle nomme une clé de la config déployée dont la valeur, si elle
est définie, devient la cible ; si la clé est absente ou vide, le `base`/`paths`
par défaut s'applique. morfdeploy lit l'emplacement réel dans la config du service
au lieu de le deviner.

```jsonc
{ "id": "vault", "label": "Coffre chiffré", "destructive": true, "type": "path",
  "from_config": "vault_root", "base": "state", "paths": ["vault"] }
```

Par défaut la valeur de config EST la cible (`from_config_kind: "path"`). Quand la
clé nomme un *dossier parent* contenant des fichiers nommés (un dossier de cache
avec un fichier par historique), utiliser `from_config_kind: "dir"` : les `paths`
sont joints à la valeur, et `default_dir` donne le dossier de repli sous `base`
quand la clé est absente.

```jsonc
{ "id": "sitewatch-history", "label": "Historique SiteWatch", "destructive": true,
  "type": "path", "from_config": "sitewatch_cache_dir", "from_config_kind": "dir",
  "base": "app", "default_dir": "cache", "paths": ["sitewatch-history.sqlite"] }
```

```sh
sudo ./service.py purge cache database   # catégories nommées
sudo ./service.py purge --all            # toutes les catégories déclarées
./service.py purge --all --dry-run       # montre ce qui partirait, ne supprime rien
```

`--dry-run` parcourt le même chemin de résolution que l'exécution réelle ; seul
l'acte final diffère. Une catégorie `command` n'est simulée que si le projet
déclare que sa commande supporte `--dry-run` (`dry_run: true`) ; sinon la
simulation ne lance **rien** et le signale, plutôt que de laisser croire qu'elle a
agi. Les droits administrateur ne sont exigés que par la purge réelle, jamais par
une simulation.

Une purge réelle est **refusée tant que le service tourne** : effacer une base
qu'il est peut-être en train d'écrire la corromprait. Arrêter le service d'abord,
ou passer `--force` pour outrepasser le garde-fou. `uninstall` accepte aussi
`--dry-run`, qui liste ce qu'il désinscrirait et (avec `--purge`) supprimerait,
sans rien toucher.

## Dépendances système

Un projet déclare les paquets système dont il a besoin comme des **besoins**, pas
comme des commandes d'installation. morfDeploy détecte le gestionnaire de paquets
de la plateforme et résout le bon paquet ; rien de global n'est jamais touché,
uniquement les paquets déclarés.

```jsonc
"system_dependencies": [
  { "id": "qt-serialport", "label": "Qt SerialPort", "required_for": ["ld2410c"],
    "packages": { "debian": ["qt6-serialport-dev"] }, "required": false }
]
```

`required: false` = capacité **optionnelle** : son absence désactive cette
capacité (driver radar de morfSensor, exiftool de morfPhoto) sans bloquer le
reste. `required: true` interrompt l'opération tant qu'elle n'est pas satisfaite.

Le cycle est **détecter → présenter → valider → installer → vérifier**, jamais
d'installation silencieuse :

```sh
./service.py deps --list        # JSON : deps déclarées + présent/manquant (découverte)
./service.py deps --dry-run     # montre ce qui serait installé, ne change rien
sudo ./service.py deps --yes    # installe les paquets déclarés manquants, puis vérifie
```

`install` (et `deploy`) lance la même résolution avant le build : un paquet
obligatoire manquant s'arrête là avec un message clair plutôt qu'une erreur de
build obscure ; un optionnel manquant se contente d'un avertissement. Sur un
terminal il demande ; en non-interactif, `--yes` l'autorise (jamais en silence).
`--dry-run` affiche le plan. Une plateforme sans gestionnaire de paquets supporté,
ou une dépendance sans paquet déclaré pour elle, est signalée honnêtement plutôt
que devinée.

## Dépendances de build

Distinctes des dépendances système (nécessaires pour *exécuter* un service), ce
sont les bibliothèques nécessaires pour *compiler* un projet -- ce qu'un
`find_package` cherche. Le projet déclare un **id logique** ; morfDeploy le mappe
au paquet selon la plateforme (registre central : `openssl` → `libssl-dev`,
`libssh2` → `libssh2-1-dev`, …) et le résout **avant** le build : un OpenSSL
manquant devient un arrêt clair plutôt qu'une erreur `find_package` quinze projets
plus loin.

```jsonc
"build_dependencies": [
  { "id": "openssl", "required": true },
  { "id": "libssh2", "required": true }
]
```

```sh
./service.py build-deps --list      # JSON : deps de build déclarées + présent/manquant
./service.py build-deps --dry-run   # montre ce qui serait installé, ne change rien
sudo ./service.py build-deps --yes  # installe les libs de build manquantes, vérifie
```

`install` le lance avant de compiler. Sur une plateforme avec gestionnaire de
paquets (Debian), il détecte, présente et installe (avec confirmation, jamais en
silence). Sur une toolchain **sans** gestionnaire (Qt officielle sous Windows), il
**annonce** les besoins et laisse le `find_package` du build comme dernier mot,
sans bloquer un build qui pourrait réussir.

## Organisation

```
morfdeploy/
├── cli.py            point d'entrée (install/update/uninstall/purge/deps/build-deps/status/config)
├── core.py           le Deployer : les quatre étapes, indépendantes de la plateforme
├── manifest.py       lit et valide service.json
├── configmerge.py    complétion non destructive de la config (ajoute les clés manquantes, ne modifie jamais les valeurs)
└── backends/
    ├── systemd.py    Linux (unités systemd, StateDirectory...)
    ├── windows.py    service Windows
    └── launchd.py    macOS (accommodé, non supporté)
```

Officiellement supportés : Windows x64, Linux x64, Linux ARM64 (Raspberry Pi).
macOS est accommodé architecturalement mais non supporté.

## Consommation et mise à jour

Ne pas éditer les copies vendorées. La source de vérité est ce dépôt. Les projets
resynchronisent leur `third_party/morf/morfdeploy` avec leur script
`scripts/sync-morf` (définir `MORF_SRC_BASE` si les dépôts sont ailleurs).
`morf doctor` signale toute dérive entre une copie vendorée et cette source.

## Licence

GPL-3.0-only - © 2026 morfredus (Frédéric Biron).
