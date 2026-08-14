# morfDeploy

*Lire dans une autre langue : [English](README.md) · **Français** (ce document).*

[![Version](https://img.shields.io/badge/version-0.1.0-blue)](CHANGELOG.md)
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
./service.py status            # ce que le système en dit
```

## Organisation

```
morfdeploy/
├── cli.py            point d'entrée (install/update/uninstall/status/config)
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
