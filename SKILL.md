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

## Architecture

The generic script auto-detects the calling CLI and stores per-tool isolated state in SQLite databases. See [REFERENCE.md](REFERENCE.md) for full architecture details.
