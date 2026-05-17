---
name: goal-mode
description: Add /goal persistent objective mode to CLIs that don't have it built-in (Pi, Windsurf, custom tools). Auto-detects CLI or accepts GOAL_CLI override.
triggers:
  - user
  - model
---

# Goal Mode

Add `/goal` persistent objective mode to CLIs that don't have it built-in. Generic script that auto-detects the calling CLI and provides session-scoped objectives that persist across turns.

**Note:** Devin CLI, OpenCode, Claude, Codex, and Hermes already support `/goal` out of the box.

## Quick Start

**For Pi:**
```bash
# Install the skill
npx skills add javimosch/goal-mode

# Run the setup
bash ~/.agents/skills/goal-mode/scripts/install.sh --all
```

**For any custom CLI:**
```bash
CLI_NAME="<cli-name>"

# Create directories and symlink
mkdir -p ~/.config/$CLI_NAME/skills/goal/scripts
ln -s ~/.agents/skills/goal-mode/scripts/goal.py ~/.config/$CLI_NAME/skills/goal/scripts/${CLI_NAME}_goal.py

# Create skill registration
cat > ~/.config/$CLI_NAME/skills/goal/SKILL.md << 'EOF'
---
name: goal
description: Persistent goal mode for this CLI.
triggers: [user]
---
# Goal
/usr/bin/python3 ~/.config/$CLI_NAME/skills/goal/scripts/${CLI_NAME}_goal.py invoke "$ARGUMENTS"
EOF
```

## Usage

```bash
/goal <objective>          — set active goal
/goal status               — show goal + continuation instructions
/goal pause / resume       — toggle continuation
/goal clear                — delete goal
/goal complete             — mark done (after audit)
/goal --tokens 250K <obj>  — set with soft token budget
```

## Supported CLIs

- Pi (pi-yaml-hooks)
- Windsurf (manual continuation)
- Any custom CLI (via GOAL_CLI override)

## Continuation Configuration

See [REFERENCE.md](REFERENCE.md) for detailed setup instructions for each CLI's continuation mechanism.

## Architecture

The generic script auto-detects the calling CLI and stores per-tool isolated state in SQLite databases. See [REFERENCE.md](REFERENCE.md) for full architecture details.
