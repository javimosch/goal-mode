---
name: goal-mode
description: >
  Generic /goal command for any agentic CLI. Auto-detects the calling tool (Devin, OpenCode, etc.)
  or accepts GOAL_CLI override. Use to set up goal mode for any CLI (including Devin/OpenCode),
  verify existing configuration, deploy to new machines, or understand the architecture.
triggers:
  - user
  - model
---

# Goal Mode

Generic `/goal` command for any agentic CLI. Provides persistent session-scoped objectives
that persist across turns, with automatic continuation hooks.

**Use this skill to:**
- Set up goal mode for any CLI (Devin, OpenCode, pi, claude, codex, etc.)
- Verify/fix existing goal mode configuration
- Deploy to new machines
- Understand the goal system architecture

---

## Setup or Verify Goal Mode

When this skill is invoked, first determine the target CLI name (e.g., `devin`, `opencode`, `pi`, `claude`).

### Step 1: Check current configuration

```bash
CLI_NAME="<cli-name>"  # e.g., devin, opencode, pi

# Check components
ls -la ~/.config/$CLI_NAME/skills/goal/ 2>/dev/null || echo "No skill dir"
ls -la ~/.config/$CLI_NAME/skills/goal/scripts/${CLI_NAME}_goal.py 2>/dev/null || echo "No script"
[ -L ~/.config/$CLI_NAME/skills/goal/scripts/${CLI_NAME}_goal.py ] && readlink ~/.config/$CLI_NAME/skills/goal/scripts/${CLI_NAME}_goal.py
ls -la ~/.config/$CLI_NAME/goal/goals.sqlite 2>/dev/null || echo "No DB (created on first use)"

# Check continuation (CLI-specific)
grep -A 10 '"Stop"' ~/.config/$CLI_NAME/config.json 2>/dev/null || echo "No Stop hook (Devin)"
ls -la ~/.config/$CLI_NAME/plugins/goal-continue.js 2>/dev/null || echo "No plugin (OpenCode)"
ls -la ~/.pi/agent/hook/hooks.yaml 2>/dev/null || echo "No hooks.yaml (Pi)"
```

### Step 2: Fix missing components

**Skill directory & script:**
```bash
mkdir -p ~/.config/<cli>/skills/goal/scripts
ln -s ~/.agents/skills/goal-mode/scripts/goal.py ~/.config/<cli>/skills/goal/scripts/<cli>_goal.py
# Or: bash ~/.agents/skills/goal-mode/scripts/install.sh --all
```

**Skill registration (SKILL.md):**
```bash
cat > ~/.config/<cli>/skills/goal/SKILL.md << 'EOF'
---
name: goal
description: Persistent goal mode. Use /goal for objectives that persist across turns.
triggers: [user]
---
# Goal
/usr/bin/python3 ~/.config/<cli>/skills/goal/scripts/<cli>_goal.py invoke "$ARGUMENTS"
EOF
```

**Configure continuation** (see CLI-specific section below).

### Step 3: Test

```bash
<CLI>_GOAL_SESSION_ID=test /usr/bin/python3 ~/.config/<cli>/skills/goal/scripts/<cli>_goal.py invoke "test"
<CLI>_GOAL_SESSION_ID=test /usr/bin/python3 ~/.config/<cli>/skills/goal/scripts/<cli>_goal.py status
sqlite3 ~/.config/<cli>/goal/goals.sqlite "SELECT source, objective FROM goals;"
```

---

## CLI-Specific Continuation Configuration

**Devin (Stop hook in ~/.config/devin/config.json):**
```json
"hooks": {
  "Stop": [{
    "hooks": [{
      "type": "command",
      "command": "/usr/bin/python3 ~/.config/devin/skills/goal/scripts/devin_goal.py stop-hook",
      "timeout": 10
    }]
  }]
}
```

**OpenCode (plugin in ~/.config/opencode/plugins/goal-continue.js):**
```javascript
pi.on("shell.env", (e, ctx) => { e.output.env.GOAL_SESSION_ID = e.input.sessionID; });
pi.on("session.idle", (e, ctx) => {
  const { exec } = require("child_process");
  exec("/usr/bin/python3 ~/.config/opencode/skills/goal/scripts/opencode_goal.py stop-hook",
    { env: { ...process.env, GOAL_SESSION_ID: ctx.sessionID } },
    (err, out) => { if (!err) { const r = JSON.parse(out); if (r.decision === "block") ctx.pi.sendMessage(r.reason); }});
});
```

**Pi (pi-yaml-hooks):**
```bash
pi install npm:pi-yaml-hooks
mkdir -p ~/.pi/agent/hook
cat > ~/.pi/agent/hook/hooks.yaml <<'YAML'
hooks:
  - event: session.idle
    actions:
      - bash: |
          out=$(PI_GOAL_SESSION_ID=$PI_SESSION_ID /usr/bin/python3 ~/.config/pi/skills/goal/scripts/pi_goal.py stop-hook <<< '{"session_id":"'"$PI_SESSION_ID"'","cwd":"'"$PI_PROJECT_DIR"'"}')
          echo "$out" | grep -q '"decision":"block"' && echo "$out" | jq -r '.reason'
YAML
```

**Tools without hooks:** Goals work fully (set, pause, resume, status, clear, complete) but require manual continuation prompts.

---

## Architecture Overview

The `/goal` system gives AI agents a durable, session-scoped objective that persists across turns.
A single generic Python script auto-detects the calling tool (or accepts `GOAL_CLI` override)
and stores per-tool isolated state in separate SQLite databases.

```
/goal <objective>          — set active goal
/goal status               — show goal + continuation instructions
/goal pause / resume       — toggle continuation
/goal clear                — delete goal
/goal complete             — mark done (after audit)
/goal --tokens 250K <obj>  — set with soft token budget
```

Continuation mechanism differs by tool:

| Tool | Mechanism |
|------|-----------|
| Devin CLI | `Stop` lifecycle hook blocks agent exit; re-injection via hook reason |
| OpenCode | `session.idle` plugin event re-injects via `client.session.chat()` |
| Pi | `pi-yaml-hooks` package with `session.idle` event and bash action to call stop-hook |

---

## File Map

### Canonical source (rsync-friendly)

| Path | Purpose |
|------|---------|
| `~/.agents/skills/goal-mode/SKILL.md` | This documentation |
| `~/.agents/skills/goal-mode/scripts/goal.py` | **Generic state machine** (Python, stdlib only, auto-detects CLI) |
| `~/.agents/skills/goal-mode/scripts/install.sh` | Symlinks `goal.py` into tool-specific `~/.config/<cli>/skills/goal/scripts/` |

### Local machine (`jarancibia@local`)

| Path | Purpose |
|------|---------|
| `~/.config/devin/skills/goal/SKILL.md` | Devin skill registration |
| `~/.config/devin/skills/goal/scripts/devin_goal.py` | **symlink** -> `~/.agents/skills/goal-mode/scripts/goal.py` |
| `~/.config/devin/config.json` | Contains `hooks.Stop` entry |
| `~/.config/opencode/skills/goal/SKILL.md` | OpenCode skill registration |
| `~/.config/opencode/skills/goal/scripts/opencode_goal.py` | **symlink** -> `~/.agents/skills/goal-mode/scripts/goal.py` |
| `~/.config/opencode/plugins/goal-continue.js` | OpenCode plugin: `shell.env` + `session.idle` |

### dk2 (`jarancibia@92.113.145.16`)

| Path | Purpose |
|------|---------|
| `~/.config/devin/skills/goal/SKILL.md` | Devin skill registration |
| `~/.config/devin/skills/goal/scripts/devin_goal.py` | **symlink** -> `~/.agents/skills/goal-mode/scripts/goal.py` |
| `~/.config/devin/config.json` | Same Stop hook |

OpenCode is **not** installed on dk2 — only Devin.

### Pi (any machine)

| Path | Purpose |
|------|---------|
| `~/.config/pi/skills/goal/SKILL.md` | Pi skill registration |
| `~/.config/pi/skills/goal/scripts/pi_goal.py` | **symlink** -> `~/.agents/skills/goal-mode/scripts/goal.py` |
| `~/.pi/agent/hook/hooks.yaml` | pi-yaml-hooks config for `session.idle` event |

---

## Generic Script Design

### `goal.py` auto-detection

The generic script detects the calling CLI in this order:

1. `GOAL_CLI` env var (e.g., `GOAL_CLI=devin`)
2. Invocation path (e.g., path contains `devin` or `opencode`)
3. Tool-specific session env vars (`DEVIN_SESSION_ID`, `OPENCODE_SESSION_ID`, etc.)
4. Fallback to `generic` mode

### Per-tool DB isolation

Each tool has its own SQLite database derived from the detected CLI name:

| CLI | Default DB | Override env vars |
|-----|-----------|-------------------|
| devin | `~/.config/devin/goal/goals.sqlite` | `DEVIN_GOAL_HOME`, `DEVIN_GOAL_DB` |
| opencode | `~/.config/opencode/goal/goals.sqlite` | `OPENCODE_GOAL_HOME`, `OPENCODE_GOAL_DB` |
| pi | `~/.config/pi/goal/goals.sqlite` | `PI_GOAL_HOME`, `PI_GOAL_DB` |
| claude | `~/.config/claude/goal/goals.sqlite` | `CLAUDE_GOAL_HOME`, `CLAUDE_GOAL_DB` |
| codex | `~/.config/codex/goal/goals.sqlite` | `CODEX_GOAL_HOME`, `CODEX_GOAL_DB` |
| hermes | `~/.config/hermes/goal/goals.sqlite` | `HERMES_GOAL_HOME`, `HERMES_GOAL_DB` |
| windsurf | `~/.config/windsurf/goal/goals.sqlite` | `WINDSURF_GOAL_HOME`, `WINDSURF_GOAL_DB` |
| generic | `~/.config/generic/goal/goals.sqlite` | `GOAL_HOME`, `GOAL_DB` |

**Never share a single DB across tools** — session ID namespaces differ.

### Session ID resolution priority

For any detected CLI `{NAME}`:

1. `{NAME}_GOAL_SESSION_ID`
2. `{NAME}_SESSION_ID`
3. `GOAL_SESSION_ID`
4. `CLAUDE_GOAL_SESSION_ID`
5. `CLAUDE_SESSION_ID`
6. Terminal session (`TERM_SESSION_ID` / `ITERM_SESSION_ID`) → `term:<sha256[:16]>`
7. cwd fallback → `cwd:<sha256[:16]>`

### Python interpreter

Always use `/usr/bin/python3` (system Python) — **not** `/usr/local/bin/python3`.

- Local: `/usr/bin/python3` = 3.10 (has `sqlite3`)
- dk2: `/usr/bin/python3` = 3.12 (has `sqlite3`)
- `/usr/local/bin/python3` (3.11 on local) lacks `_sqlite3` — do NOT use.

---

## Devin Stop Hook

Registered in `~/.config/devin/config.json`:

```json
"hooks": {
  "Stop": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "/usr/bin/python3 ~/.config/devin/skills/goal/scripts/devin_goal.py stop-hook",
          "timeout": 10
        }
      ]
    }
  ]
}
```

The hook reads JSON from stdin (contains `session_id`, `cwd`), checks the DB, and prints:

```json
{ "decision": "block", "reason": "<continuation instructions>" }
```

or exits silently (decision: allow) when no active goal exists.

Runaway guard: `{CLI}_GOAL_MAX_STOP_CONTINUES` (default 500) — counts `stop_continue` events
in the `events` table since the goal's `active_started_at`. Falls back to generic `GOAL_MAX_STOP_CONTINUES`.

---

## OpenCode Plugin (`goal-continue.js`)

Located at `~/.config/opencode/plugins/goal-continue.js`.

Two hooks:

1. **`shell.env`** — fires before each bash tool call.
   Sets `output.env.GOAL_SESSION_ID = input.sessionID` so the Python script uses the real session anchor.

2. **`event` (session.idle)** — fires when the agent goes idle.
   Calls `opencode_goal.py stop-hook` with `GOAL_SESSION_ID` set.
   If response is `{ "decision": "block" }`, calls `client.session.chat()` to re-inject the prompt.

Dedup guard: `pendingContinuation` Set prevents double-firing within the same idle event.

---

## Database Schema

`goal.py` initializes this schema for any detected CLI:

```sql
CREATE TABLE IF NOT EXISTS goals (
    id                 TEXT PRIMARY KEY,
    session_id         TEXT NOT NULL UNIQUE,
    objective          TEXT NOT NULL,
    status             TEXT NOT NULL CHECK(status IN ('active','paused','budget_limited','complete')),
    token_budget       INTEGER,
    tokens_used        INTEGER NOT NULL DEFAULT 0,
    time_used_seconds  INTEGER NOT NULL DEFAULT 0,
    active_started_at  INTEGER,
    created_at         INTEGER NOT NULL,
    updated_at         INTEGER NOT NULL,
    completed_at       INTEGER,
    source             TEXT NOT NULL DEFAULT '<cli-name>',
    metadata_json      TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id     TEXT,
    session_id  TEXT NOT NULL,
    event       TEXT NOT NULL,
    detail      TEXT,
    created_at  INTEGER NOT NULL
);
```

WAL mode is enabled on every connection.

---

## Deploying to a New Machine

```bash
# 1. Sync the skill directory (includes scripts + SKILL.md)
rsync -av ~/.agents/skills/goal-mode/ <host>:~/.agents/skills/goal-mode/

# 2. On the remote host, run install.sh to create symlinks
ssh <host> "bash ~/.agents/skills/goal-mode/scripts/install.sh --all"

# 3. Sync config (Stop hook) — only needed for Devin
rsync -av ~/.config/devin/config.json <host>:~/.config/devin/config.json

# 4. Verify /usr/bin/python3 has sqlite3
ssh <host> "/usr/bin/python3 -c 'import sqlite3; print(sqlite3.sqlite_version)'"
```

### Deploying updates (single command)

```bash
rsync -av ~/.agents/skills/goal-mode/scripts/goal.py <host>:~/.agents/skills/goal-mode/scripts/goal.py
```

Because the tool-specific scripts are symlinks, they automatically pick up the new generic script.

---

## Common Maintenance Tasks

### Check goal state (local Devin)
```bash
/usr/bin/python3 ~/.config/devin/skills/goal/scripts/devin_goal.py status
```

### Inspect DB directly
```bash
sqlite3 ~/.config/devin/goal/goals.sqlite "SELECT session_id, status, objective, created_at FROM goals;"
sqlite3 ~/.config/opencode/goal/goals.sqlite "SELECT session_id, status, objective FROM goals;"
```

### Clear a stuck goal manually
```bash
sqlite3 ~/.config/devin/goal/goals.sqlite "DELETE FROM goals;"
```

### Force-clear via script
```bash
DEVIN_GOAL_SESSION_ID=<session_id> /usr/bin/python3 \
  ~/.config/devin/skills/goal/scripts/devin_goal.py clear
```

### Test Stop hook
```bash
echo '{"session_id":"test-123","cwd":"/tmp"}' | \
  DEVIN_GOAL_SESSION_ID=test-123 /usr/bin/python3 \
  ~/.config/devin/skills/goal/scripts/devin_goal.py stop-hook
```

---

## Adding a New Remote Host

1. SSH into the host and verify `/usr/bin/python3` has `sqlite3`.
2. Rsync `~/.agents/skills/goal-mode/` to the host.
3. Run `~/.agents/skills/goal-mode/scripts/install.sh --all` on the host.
4. Update `~/.config/devin/config.json` on that host to add the Stop hook.
5. Add the host to this skill's File Map section.

---

## Caveats & Pitfalls

### ⚠️ NEVER include daemon completion markers in the goal objective text

`goal.py invoke` echoes the **full objective text** back to the terminal as part of its
output (in the "Objective:" and "OBJECTIVE:" fields). Any keyword an external monitor watches
for will be detected immediately — before the agent does any real work.

**Real incident (2026-05-14):** The mika-daemon (agentic-javika-v1) monitors tmux panes for the
string `CHAUCHAU` to detect turn completion. Prompts were prefixed with:

```
/goal As CTO of agentic-javika: ... Do not stop until CHAUCHAU is written.
```

The goal script echoed `CHAUCHAU` in its output → daemon detected it in 2–3 seconds → turn
ended immediately. CTO turns consistently completed in 2.5–2.8s with zero actual tool calls.

**Fix:** Remove any monitored completion marker from the goal objective. Put the requirement
only in the main prompt body (not in `/goal`), where it will only appear when the agent writes
it intentionally:

```
# BAD (objective echoed by script, triggers false detection)
/goal ... Do not stop until CHAUCHAU is written.

# GOOD (completion marker only in main prompt body)
/goal ... Perform substantive work before ending the turn.
```

---

### ⚠️ Stop hook is bypassed when an external monitor kills the tmux session

The Stop hook prevents Devin from ending the session on its own. But if an **external process**
kills the tmux session (e.g., mika-daemon killing the session after detecting CHAUCHAU), the
hook never runs. This is safe — no conflict — but means the goal is left in `active` state in
the DB. The next session using the same session ID anchor would see a stale goal.

**Mitigation:** When using `/goal` inside externally-managed tmux turns, session IDs differ each
turn (timestamp-based names), so stale goals accumulate in the DB but don't interfere. Periodically
clear the goal DB on dk2 if it grows:

```bash
ssh dk2@92.113.145.16 "sqlite3 ~/.config/devin/goal/goals.sqlite 'DELETE FROM goals;'"
```

---

### `/goal` in `--prompt-file` mode works correctly

When a prompt file's **first line** is `/goal <objective>`, Devin treats it as a user-triggered
skill invocation. The goal is set and continuation instructions are injected before the agent
reads the rest of the prompt. No special configuration needed.

---

### CEO turns vs CTO turns may behave differently

In an orchestrator loop (e.g., mika-daemon alternating CEO/CTO), the Stop hook continuation
may only benefit turns that have substantive long-running work. Short-turn agents (who complete
quickly and write CHAUCHAU in one pass) won't see a difference from `/goal` vs no `/goal`.
The value of `/goal` is for turns where the agent might stop mid-task between tool calls.
