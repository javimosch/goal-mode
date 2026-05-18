# Goal Mode

Generic `/goal` command implementation for Devin CLI, OpenCode, and Pi. Provides persistent session-scoped objectives that persist across turns with automatic continuation hooks.

This repo bundles the goal mode implementation that Devin CLI, OpenCode, and Pi include.

**Note for Pi users:** Pi also has its own goal mode implementation available via `npm:@narumitw/pi-goal` (published May 16). If you install that package instead, do not install this repo for Pi to avoid conflicts.

## Installation

### Via npx skills (recommended)

```bash
npx skills add javimosch/goal-mode
```

### Manual installation

```bash
git clone https://github.com/javimosch/goal-mode.git ~/.agents/skills/goal-mode
```

## Quick Start

After installation, run the setup script for known CLIs:

```bash
bash ~/.agents/skills/goal-mode/scripts/install.sh --all
```

This will create symlinks for: devin, opencode, claude, codex, windsurf, pi

## Uninstall / Removal

To remove goal mode from all CLIs:

```bash
bash ~/.agents/skills/goal-mode/scripts/install.sh --uninstall
```

To remove from a specific CLI:

```bash
# Remove from specific CLI (e.g., just pi)
bash ~/.agents/skills/goal-mode/scripts/install.sh --uninstall --all
# Then manually clean up other CLIs as needed
```

**Note:** The uninstall script removes symlinks and databases, but you may also need to manually remove tool-specific configuration:
- **Devin:** Remove Stop hook from `~/.config/devin/config.json`
- **OpenCode:** Remove idle plugin from `~/.config/opencode/plugins/`
- **Pi:** If using npm package, run `npm uninstall -g @narumitw/pi-goal`

## Usage

Once installed for your CLI, use the `/goal` command:

```bash
/goal "Implement user authentication"          — set active goal
/goal status                                   — show goal + continuation instructions
/goal pause                                    — pause continuation
/goal resume                                   — resume continuation
/goal clear                                    — delete goal
/goal complete                                 — mark done (after audit)
/goal --tokens 250K "Refactor database"        — set with soft token budget
```

## Supported CLIs

This repo bundles the goal mode implementation for:

| CLI | Status | Continuation Mechanism |
|-----|--------|----------------------|
| Devin CLI | ✅ Bundled | Stop lifecycle hook |
| OpenCode | ✅ Bundled | idle plugin |
| Pi | ✅ Bundled (this repo) | pi-yaml-hooks |

**Alternative for Pi:** `npm:@narumitw/pi-goal` (available May 16) - if you install this package, do not install this repo for Pi to avoid conflicts.

**Legend:**
- ✅ Bundled: The CLI includes this repo's goal mode implementation by default

## Architecture

The system uses a single generic Python script (`goal.py`) that:
- Auto-detects the calling CLI via `GOAL_CLI` env var, invocation path, or session env vars
- Stores per-tool isolated state in SQLite databases
- Provides CLI-specific continuation hooks

See [REFERENCE.md](REFERENCE.md) for detailed architecture, setup instructions, and configuration options.

## License

MIT

## Author

Javier Leandro Arancibia
