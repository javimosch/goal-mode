---
name: goal-mode
description: Generic /goal command for any agentic CLI. Auto-detects the calling tool (Devin, OpenCode, Pi, etc.) or accepts GOAL_CLI override. Set persistent goals that persist across turns with automatic continuation hooks.
triggers:
  - user
  - model
---

# Goal Mode

Generic `/goal` command for any agentic CLI. Provides persistent session-scoped objectives that persist across turns, with automatic continuation hooks.

## Quick Start

**For a new CLI (e.g., pi, claude):**
```bash
# Install the skill
npx skills add jarancibia/goal-mode

# Run the setup
bash ~/.agents/skills/goal-mode/scripts/install.sh --all
```

**Manual setup for a specific CLI:**
```bash
CLI_NAME="<cli-name>"  # e.g., pi, claude

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

- Devin CLI (Stop hook)
- OpenCode (idle plugin)
- Pi (pi-yaml-hooks)
- Any CLI (manual continuation)

## Continuation Configuration

See [REFERENCE.md](REFERENCE.md) for detailed setup instructions for each CLI's continuation mechanism.

## Architecture

The generic script auto-detects the calling CLI and stores per-tool isolated state in SQLite databases. See [REFERENCE.md](REFERENCE.md) for full architecture details.
