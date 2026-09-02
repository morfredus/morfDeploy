#!/usr/bin/env bash
# =============================================================================
# build-arm64-sysroot.sh
#
# Construit UNE FOIS un SYSROOT Debian 13 (Trixie) ARM64, pour la cross-compilation
# reproductible des services morfSystem depuis un hote x86_64 (WSL Ubuntu ou Linux).
#
# Pourquoi : la cible est un Raspberry Pi sous Debian Trixie arm64. Pour qu'un binaire
# croise tourne reellement sur le Pi, il faut lier contre les MEMES versions (glibc,
# Qt6) que la cible. Ce script fabrique donc un sysroot Debian Trixie arm64 avec les
# memes paquets Qt6 que le Pi (voir le manuel, chapitre Raspberry Pi). Le build natif
# "linux-arm64" (sur le Pi) reste la voie de reference ; ce sysroot sert au preset
# "linux-arm64-cross".
#
# Reproductible et HORS-LIGNE apres coup : une fois construit, plus besoin ni du Pi
# ni du reseau. Le Pi n'est JAMAIS requis.
#
# Prerequis sur l'hote (Debian/Ubuntu) :
#   sudo apt install -y debootstrap qemu-user-static binfmt-support symlinks \
#        crossbuild-essential-arm64 qt6-base-dev
#   (crossbuild-essential-arm64 fournit aarch64-linux-gnu-gcc/g++ ; qt6-base-dev
#    amd64 fournit les outils HOTE moc/rcc/uic pointes par MORF_QT_HOST_PATH=/usr.)
#
# Usage :
#   morfDeploy/scripts/build-arm64-sysroot.sh [chemin_sysroot]
#   (defaut : ~/morf-sysroots/trixie-arm64)
#
# Ensuite, pour chaque projet :
#   export MORF_SYSROOT=~/morf-sysroots/trixie-arm64
#   cmake --preset linux-arm64-cross
#   cmake --build --preset linux-arm64-cross
# =============================================================================
set -euo pipefail

SUITE="trixie"
MIRROR="http://deb.debian.org/debian"
SYSROOT="${1:-$HOME/morf-sysroots/trixie-arm64}"

# Paquets installes DANS le sysroot cible (arm64). Alignes sur le manuel Pi
# (qt6-base/charts/tools + deps courantes du parc). Ajouter ici tout -dev arm64 dont
# un service a besoin (ex. libqt6serialport6-dev pour morfSensor).
PKGS="qt6-base-dev,qt6-charts-dev,qt6-tools-dev,qt6-tools-dev-tools,qt6-serialport-dev,\
libssl-dev,libssh2-1-dev,zlib1g-dev,nlohmann-json3-dev,pkg-config"

info()  { printf '\033[36m%s\033[0m\n' "$*"; }
warn()  { printf '\033[33m%s\033[0m\n' "$*" >&2; }
die()   { printf '\033[31mERREUR: %s\033[0m\n' "$*" >&2; exit 1; }

# --- Prerequis ---------------------------------------------------------------
command -v debootstrap  >/dev/null 2>&1 || die "debootstrap absent. sudo apt install debootstrap"
[ -x /usr/bin/qemu-aarch64-static ] || die "qemu-aarch64-static absent. sudo apt install qemu-user-static binfmt-support"
if [ "$(id -u)" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    warn "Le script a besoin de sudo (debootstrap + chroot). Il va le demander."
fi
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

if [ -e "$SYSROOT" ]; then
    die "Le sysroot existe deja : $SYSROOT
     Le supprimer pour le reconstruire (sudo rm -rf \"$SYSROOT\"), ou en choisir un autre."
fi

info "Construction du sysroot Debian $SUITE arm64 -> $SYSROOT"
$SUDO mkdir -p "$SYSROOT"

# --- 1) debootstrap premiere passe (foreign : cible d'une autre archi) -------
# --foreign depose les paquets sans les configurer (impossible sur l'hote x86_64) ;
# la seconde passe s'execute DANS le sysroot via qemu (emulation aarch64).
info "1/4  debootstrap (telechargement des paquets)..."
$SUDO debootstrap --arch=arm64 --foreign \
    --variant=minbase \
    --include="$PKGS" \
    "$SUITE" "$SYSROOT" "$MIRROR"

# --- 2) qemu + seconde passe (configuration dans le sysroot) -----------------
info "2/4  seconde passe (configuration via qemu-aarch64)..."
$SUDO cp /usr/bin/qemu-aarch64-static "$SYSROOT/usr/bin/"
$SUDO chroot "$SYSROOT" /debootstrap/debootstrap --second-stage

# --- 3) relativiser les liens symboliques absolus ----------------------------
# Debian cree des liens absolus (ex. libQt6Core.so -> /lib/aarch64-linux-gnu/...).
# Utilises comme SYSROOT (prefixe), ils pointeraient HORS du sysroot et casseraient
# find_package/le linker. On les rend relatifs.
info "3/4  relativisation des liens symboliques..."
if command -v symlinks >/dev/null 2>&1; then
    $SUDO symlinks -rc "$SYSROOT" >/dev/null || warn "symlinks a signale des liens ; sans gravite en general."
else
    warn "L'outil 'symlinks' est absent (sudo apt install symlinks). Certains find_package "
    warn "Qt6 pourraient echouer sur des liens absolus. Installer 'symlinks' et relancer, "
    warn "ou reparer a la main."
fi

# --- 4) recap ----------------------------------------------------------------
info "4/4  termine."
QT6_CMAKE="$SYSROOT/usr/lib/aarch64-linux-gnu/cmake/Qt6"
if [ -d "$QT6_CMAKE" ]; then
    info "Qt6 cible detecte : $QT6_CMAKE"
else
    warn "Qt6 cible introuvable sous $QT6_CMAKE : verifier que qt6-base-dev est bien installe."
fi

cat <<EOF

Sysroot pret : $SYSROOT

Pour cross-compiler un projet morfSystem :

    export MORF_SYSROOT="$SYSROOT"
    cmake --preset linux-arm64-cross
    cmake --build --preset linux-arm64-cross

Note : moc/rcc/uic (arm64) sont executes en emulation qemu ; le preset exporte
QEMU_LD_PREFIX=\$MORF_SYSROOT pour cela. Hors preset, l'exporter a la main :
    export QEMU_LD_PREFIX="\$MORF_SYSROOT"
Option avancee (build plus rapide, sans emulation) : fournir un Qt6 hote x86_64 de
MEME version que la cible via  export MORF_QT_HOST_PATH=<prefixe_qt6_hote>.

Verifier l'architecture du binaire produit :
    file build-arm64-cross/service/<binaire>    # -> ELF 64-bit ARM aarch64
EOF
