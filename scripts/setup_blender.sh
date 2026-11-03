#!/usr/bin/env bash
# Installe Blender (build officiel Linux x64) pour un usage headless.
#
# Deux usages :
#   1. Coller ce fichier tel quel dans le "Setup script" de l'environnement cloud
#      (claude.ai/code) : installation faite une fois puis mise en cache.
#   2. Appelé automatiquement par le hook SessionStart (.claude/hooks/session-start.sh)
#      si Blender n'est pas encore installé.
#
# Idempotent : ne refait rien si la version demandée est déjà installée.
# Réseau requis : download.blender.org (+ archive.ubuntu.com pour apt).
set -euo pipefail

BLENDER_VERSION="${BLENDER_VERSION:-5.2.3}"
BLENDER_SERIES="${BLENDER_VERSION%.*}"   # 5.2.3 -> 5.2
URL="https://download.blender.org/release/Blender${BLENDER_SERIES}/blender-${BLENDER_VERSION}-linux-x64.tar.xz"

log() { echo "[setup-blender] $*" >&2; }

# --- root / sudo / utilisateur simple -------------------------------------
if [ "$(id -u)" -eq 0 ]; then
  MODE="root"
elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
  MODE="sudo"
else
  MODE="user"
fi
as_root() { if [ "$MODE" = "sudo" ]; then sudo "$@"; else "$@"; fi; }

if [ "$MODE" = "user" ]; then
  PREFIX="$HOME/.local/opt"; BIN_DIR="$HOME/.local/bin"
else
  PREFIX="/opt"; BIN_DIR="/usr/local/bin"
fi
INSTALL_DIR="$PREFIX/blender-${BLENDER_VERSION}"

# --- bibliothèques système dont Blender a besoin, même sans écran ----------
PKGS="xz-utils libx11-6 libxi6 libxxf86vm1 libxfixes3 libxrender1 libxext6 libxkbcommon0 libsm6 libice6 libgl1 libegl1 libvulkan1"
if [ "$MODE" != "user" ] && command -v apt-get >/dev/null 2>&1; then
  MISSING=""
  for p in $PKGS; do dpkg -s "$p" >/dev/null 2>&1 || MISSING="$MISSING $p"; done
  if [ -n "$MISSING" ]; then
    log "apt install:$MISSING"
    as_root apt-get update -qq >&2
    # shellcheck disable=SC2086
    as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends $MISSING >&2
  fi
else
  log "pas de droits root : bibliothèques système non vérifiées"
fi

# --- Blender -----------------------------------------------------------------
if [ -x "$INSTALL_DIR/blender" ]; then
  log "Blender $BLENDER_VERSION déjà présent dans $INSTALL_DIR"
else
  log "téléchargement de $URL (~400 Mo)…"
  as_root mkdir -p "$PREFIX"
  as_root rm -rf "$PREFIX/blender-${BLENDER_VERSION}-linux-x64" "$INSTALL_DIR"
  curl -fsSL --retry 3 "$URL" | as_root tar -xJ -C "$PREFIX"
  as_root mv "$PREFIX/blender-${BLENDER_VERSION}-linux-x64" "$INSTALL_DIR"
fi

as_root mkdir -p "$BIN_DIR"
as_root ln -sf "$INSTALL_DIR/blender" "$BIN_DIR/blender"

# --- vérification ------------------------------------------------------------
VERSION_OUT="$("$BIN_DIR/blender" --version 2>/dev/null)" || VERSION_OUT=""
VERSION_LINE="${VERSION_OUT%%$'\n'*}"
if [ -z "$VERSION_LINE" ]; then
  log "ERREUR : Blender ne démarre pas. Bibliothèques manquantes :"
  ldd "$INSTALL_DIR/blender" 2>/dev/null | grep "not found" >&2 || true
  exit 1
fi
log "OK : $VERSION_LINE -> $BIN_DIR/blender"
