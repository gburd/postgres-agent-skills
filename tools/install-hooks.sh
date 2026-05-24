#!/usr/bin/env bash
# One-shot installer for repo-tracked git hooks.
#
# After cloning, run this once:
#     ./tools/install-hooks.sh
#
# It runs `git config core.hooksPath .githooks` so the tracked hooks
# under .githooks/ become active. Idempotent.

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [ ! -d .githooks ]; then
    echo "no .githooks directory; nothing to install" >&2
    exit 0
fi

git config core.hooksPath .githooks
echo "installed: core.hooksPath = .githooks"

if ! command -v gitleaks >/dev/null 2>&1; then
    cat >&2 <<'MSG'

note: gitleaks is not in PATH. The pre-commit hook will skip scanning
until you install it. Recommended:
    nix-shell -p gitleaks      # one-shot
    nix profile install nixpkgs#gitleaks   # persistent
MSG
fi
