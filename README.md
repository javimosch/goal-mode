# Goal Mode

Generic `/goal` command for any agentic CLI. Auto-detects the calling tool (Devin, OpenCode, Pi, etc.) and provides persistent session-scoped objectives that persist across turns.

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

The generic script auto-detects and supports these CLIs:

| CLI | Status | Continuation Mechanism |
|-----|--------|----------------------|
| Devin CLI | ✅ Configured | Stop lifecycle hook |
| OpenCode | ✅ Configured | idle plugin |
| Claude | ⚠️ Supported | Manual (hooks TBD) |
| Hermes | ⚠️ Supported | Manual (hooks TBD) |
| Codex | ⚠️ Supported | Manual (hooks TBD) |
| Pi | ⚠️ Supported | pi-yaml-hooks |
| Windsurf | ⚠️ Supported | Manual (hooks TBD) |

**Legend:**
- ✅ Configured: Symlinks and continuation hooks are set up
- ⚠️ Supported: The script knows about the CLI, but requires manual setup of symlinks/hooks

**To configure a supported CLI:**
```bash
# Use the install script
bash ~/.agents/skills/goal-mode/scripts/install.sh --all

# Or manually for a specific CLI
CLI_NAME="claude"
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
