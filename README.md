# Goal Mode

Generic `/goal` command implementation for Devin CLI and OpenCode. Provides persistent session-scoped objectives that persist across turns with automatic continuation hooks.

This repo provides the goal mode implementation that Devin CLI and OpenCode bundle. Other CLIs (like Pi) can also adopt this implementation.

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

| CLI | Status | Continuation Mechanism |
|-----|--------|----------------------|
| Devin CLI | ✅ Bundled | Stop lifecycle hook |
| OpenCode | ✅ Bundled | idle plugin |
| Pi | ⚠️ Can adopt | pi-yaml-hooks |
| Custom CLIs | ⚠️ Can adopt | Via GOAL_CLI override |

**Legend:**
- ✅ Bundled: Devin CLI and OpenCode include this goal mode implementation
- ⚠️ Can adopt: Other CLIs can use this implementation with manual setup

**To adopt for a CLI (e.g., Pi):**
```bash
# Use the install script
bash ~/.agents/skills/goal-mode/scripts/install.sh --all

# Or manually
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
