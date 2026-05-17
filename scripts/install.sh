#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GOAL_PY="$SCRIPT_DIR/goal.py"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ ! -f "$GOAL_PY" ]]; then
    echo "Error: goal.py not found in $SCRIPT_DIR" >&2
    exit 1
fi

install_for() {
    local cli_name="$1"
    local target_dir="$HOME/.config/$cli_name/skills/goal/scripts"
    local target="$target_dir/${cli_name}_goal.py"

    mkdir -p "$target_dir"

    if [[ -L "$target" ]]; then
        local current
        current="$(readlink -f "$target" 2>/dev/null || true)"
        if [[ "$current" == "$GOAL_PY" ]]; then
            echo "[$cli_name] already symlinked -> $GOAL_PY"
            return
        fi
        rm "$target"
    elif [[ -f "$target" ]]; then
        mv "$target" "$target.bak.$(date +%s)"
        echo "[$cli_name] backed up existing script"
    fi

    ln -s "$GOAL_PY" "$target"
    echo "[$cli_name] installed -> $target"
}

# Install for all known CLIs
for cli in devin opencode; do
    config_dir="$HOME/.config/$cli"
    if [[ -d "$config_dir" ]] || [[ "$*" == *"--all"* ]]; then
        install_for "$cli"
    else
        echo "[$cli] skipped (no ~/.config/$cli; use --all to force)"
    fi
done

echo ""
echo "Done. Ensure your tool's config (e.g., ~/.config/devin/config.json) references"
echo "the correct script path for Stop hooks."
