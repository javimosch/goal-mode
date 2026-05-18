---
name: goal-mode
description: Generic /goal implementation for Devin CLI and OpenCode.
triggers:
  - user
  - model
---

# Goal Mode

Generic `/goal` command implementation for Devin CLI, OpenCode, and Pi. Provides persistent session-scoped objectives that persist across turns with automatic continuation hooks.

**Primary users:** Devin CLI, OpenCode, Pi
**Note for Pi:** Pi has an alternative implementation via `npm:@narumitw/pi-goal` (available May 16) - if installed, do not use this repo to avoid conflicts.

## Quick Start

The goal mode is bundled with Devin CLI and OpenCode. No installation needed for those tools.

## Usage

```bash
/goal <objective>          — set active goal
/goal status               — show goal + continuation instructions
/goal pause / resume       — toggle continuation
/goal clear                — delete goal
/goal complete             — mark done (after audit)
/goal --tokens 250K <obj>  — set with soft token budget
```

## Continuation Configuration

See [REFERENCE.md](REFERENCE.md) for detailed setup instructions for Devin CLI (Stop hook) and OpenCode (idle plugin).

## Removal / Cleanup

### Remove Goal Mode from Devin CLI

Remove the Stop lifecycle hook from `~/.config/devin/config.json`:

```bash
# Remove the "stop" hook from config.json
# Edit the file and remove the stop lifecycle hook section
```

Delete goal database and state:

```bash
rm -f ~/.config/devin/goal.db
```

### Remove Goal Mode from OpenCode

Remove the idle plugin:

```bash
rm -f ~/.config/opencode/plugins/goal-continue.js
```

Delete goal database and state:

```bash
rm -f ~/.config/opencode/goal.db
```

### Remove Goal Mode from Pi

Remove the goal skill directory:

```bash
rm -rf ~/.config/pi/skills/goal
```

Delete goal database and state:

```bash
rm -f ~/.config/pi/goal.db
```

**Note:** If using Pi's npm package (`@narumitw/pi-goal`), uninstall it instead:

```bash
npm uninstall -g @narumitw/pi-goal
```

## Architecture

The generic script auto-detects the calling CLI and stores per-tool isolated state in SQLite databases. See [REFERENCE.md](REFERENCE.md) for full architecture details.
