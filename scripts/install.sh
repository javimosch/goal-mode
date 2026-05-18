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

uninstall_for() {
    local cli_name="$1"
    local target_dir="$HOME/.config/$cli_name/skills/goal/scripts"
    local target="$target_dir/${cli_name}_goal.py"
    local goal_db="$HOME/.config/$cli_name/goal.db"

    # Remove symlink or script
    if [[ -L "$target" ]]; then
        rm "$target"
        echo "[$cli_name] removed symlink -> $target"
    elif [[ -f "$target" ]]; then
        rm "$target"
        echo "[$cli_name] removed script -> $target"
    else
        echo "[$cli_name] no script found at $target"
    fi

    # Remove goal database
    if [[ -f "$goal_db" ]]; then
        rm "$goal_db"
        echo "[$cli_name] removed database -> $goal_db"
    else
        echo "[$cli_name] no database found at $goal_db"
    fi

    # Clean up empty directories
    if [[ -d "$target_dir" ]]; then
        rmdir "$target_dir" 2>/dev/null || true
        local parent_dir="$HOME/.config/$cli_name/skills/goal"
        if [[ -d "$parent_dir" ]]; then
            rmdir "$parent_dir" 2>/dev/null || true
        fi
    fi
}

# Check for uninstall flag
if [[ "$*" == *"--uninstall"* ]] || [[ "$*" == *"--remove"* ]]; then
    echo "Uninstalling goal mode..."
    for cli in devin opencode pi; do
        config_dir="$HOME/.config/$cli"
        if [[ -d "$config_dir" ]] || [[ "$*" == *"--all"* ]]; then
            uninstall_for "$cli"
        else
            echo "[$cli] skipped (no ~/.config/$cli; use --all to force)"
        fi
    done
    echo ""
    echo "Uninstall complete. Note: You may also need to remove tool-specific config:"
    echo "  - Devin: Remove Stop hook from ~/.config/devin/config.json"
    echo "  - OpenCode: Remove idle plugin from ~/.config/opencode/plugins/"
    echo "  - Pi: If using npm package, run: npm uninstall -g @narumitw/pi-goal"
    exit 0
fi

# Install for all known CLIs
for cli in devin opencode pi; do
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
