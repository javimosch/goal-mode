# Goal Mode

Add `/goal` persistent objective mode to CLIs that don't have it built-in (Pi, Windsurf, custom tools). Generic script that auto-detects the calling CLI and provides session-scoped objectives that persist across turns.

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

This repo adds goal mode to tools that **don't** have it built-in:

| CLI | Continuation Mechanism |
|-----|----------------------|
| Pi | pi-yaml-hooks |
| Windsurf | Manual (hooks TBD) |
| Custom CLIs | Manual (GOAL_CLI override) |

**Note:** Devin CLI, OpenCode, Claude, Codex, and Hermes already support `/goal` out of the box and don't need this repo.

**To configure a CLI:**
```bash
# Use the install script
bash ~/.agents/skills/goal-mode/scripts/install.sh --all

# Or manually for a specific CLI
CLI_NAME="pi"
mkdir -p ~/.config/$CLI_NAME/skills/goal/scripts
ln -s ~/.agents/skills/goal-mode/scripts/goal.py ~/.config/$CLI_NAME/skills/goal/scripts/${CLI_NAME}_goal.py
```

See [REFERENCE.md](REFERENCE.md) for detailed continuation configuration for each CLI.

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
