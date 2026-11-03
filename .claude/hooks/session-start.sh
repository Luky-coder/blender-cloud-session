#!/usr/bin/env bash
# Hook SessionStart : s'assure que Blender est installé dans la VM cloud.
# Ne fait rien en local (CLAUDE_CODE_REMOTE n'est défini que dans les sessions cloud).
# Ce qui est écrit sur stdout est ajouté au contexte de Claude.
set -uo pipefail
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0

if ! bash scripts/setup_blender.sh; then
  echo "ATTENTION : l'installation de Blender a échoué (voir les logs [setup-blender])."
  echo "Cause la plus probable : download.blender.org n'est pas autorisé dans l'accès réseau de l'environnement (voir README.md, section Configuration)."
  exit 0
fi

# Installation sans root : rendre ~/.local/bin visible pour les commandes Bash suivantes.
if ! command -v blender >/dev/null 2>&1 && [ -x "$HOME/.local/bin/blender" ]; then
  [ -n "${CLAUDE_ENV_FILE:-}" ] && echo "export PATH=\"$HOME/.local/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "Blender prêt : $(blender --version 2>/dev/null | head -n 1). Workflow : voir CLAUDE.md."
