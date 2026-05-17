#!/usr/bin/python3
"""Generic /goal for any agentic CLI. Auto-detects tool or accepts GOAL_CLI override.
Dependency-free stdlib only. Per-tool SQLite state."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import sqlite3
import sys
import time
import uuid
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Auto-detect CLI tool
# ---------------------------------------------------------------------------
KNOWN_CLIS = ("devin", "opencode", "pi")


def _detect_cli() -> str:
    explicit = os.environ.get("GOAL_CLI", "").lower()
    if explicit:
        return explicit
    argv0 = sys.argv[0].lower()
    for name in KNOWN_CLIS:
        if name in argv0:
            return name
    for name in KNOWN_CLIS:
        up = name.upper()
        if f"{up}_SESSION_ID" in os.environ or f"{up}_GOAL_SESSION_ID" in os.environ:
            return name
    return "generic"


CLI_NAME = _detect_cli()
CLI_UP = CLI_NAME.upper()

# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------
def _env(key: str, fallback: str) -> str:
    return os.environ.get(f"{CLI_UP}_{key}", os.environ.get(f"GOAL_{key}", fallback))


STATE_DIR = Path(_env("GOAL_HOME", str(Path.home() / ".config" / CLI_NAME / "goal")))
DB_PATH = Path(_env("GOAL_DB", str(STATE_DIR / "goals.sqlite")))
SCRIPT_PATH = sys.argv[0]
SOURCE = CLI_NAME
MAX_CONTINUES = int(_env("GOAL_MAX_STOP_CONTINUES", "500"))
STATUSES = {"active", "paused", "budget_limited", "complete"}
MAX_OBJECTIVE_CHARS = 4_000

# ---------------------------------------------------------------------------
# Helpers — time / formatting
# ---------------------------------------------------------------------------
def now() -> int:
    return int(time.time())


def fmt_elapsed(seconds: int) -> str:
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours, rem = divmod(minutes, 60)
    if hours >= 24:
        days, rem_hours = divmod(hours, 24)
        return f"{days}d {rem_hours}h {rem}m"
    return f"{hours}h" if rem == 0 else f"{hours}h {rem}m"


def fmt_tokens(value: int | None) -> str:
    if value is None:
        return "none"
    value = int(value)
    abs_v = abs(value)
    if abs_v >= 1_000_000:
        return f"{value / 1_000_000:.1f}M".replace(".0M", "M")
    if abs_v >= 1_000:
        return f"{value / 1_000:.1f}K".replace(".0K", "K")
    return str(value)


def parse_tokens(text: str) -> int:
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([kKmM]?)\s*", text)
    if not m:
        raise ValueError(f"invalid token budget: {text!r}")
    number = float(m.group(1))
    suffix = m.group(2).lower()
    multiplier = 1_000_000 if suffix == "m" else 1_000 if suffix == "k" else 1
    value = int(number * multiplier)
    if value <= 0:
        raise ValueError("token budget must be positive")
    return value


# ---------------------------------------------------------------------------
# Session identity
# ---------------------------------------------------------------------------
def _term_session_id() -> str | None:
    for key in ("TERM_SESSION_ID", "ITERM_SESSION_ID"):
        val = os.environ.get(key)
        if val:
            return "term:" + hashlib.sha256(val.encode()).hexdigest()[:16]
    return None


def _sid_envs() -> list[str]:
    return [f"{CLI_UP}_GOAL_SESSION_ID", f"{CLI_UP}_SESSION_ID", "GOAL_SESSION_ID",
            "CLAUDE_GOAL_SESSION_ID", "CLAUDE_SESSION_ID"]


def session_id() -> str:
    for key in _sid_envs():
        val = os.environ.get(key)
        if val:
            return val
    term = _term_session_id()
    if term:
        return term
    cwd = os.environ.get("PWD") or str(Path.cwd())
    return "cwd:" + hashlib.sha256(cwd.encode()).hexdigest()[:16]


def _cwd_session_id(cwd: str | None) -> str | None:
    if not cwd:
        return None
    return "cwd:" + hashlib.sha256(cwd.encode()).hexdigest()[:16]


def candidate_session_ids(hook_data: dict[str, Any] | None = None) -> list[str]:
    out: list[str] = []
    sources: list[str | None] = [os.environ.get(k) for k in _sid_envs()]
    if hook_data:
        sources.append(hook_data.get("session_id"))
        sources.append(_cwd_session_id(hook_data.get("cwd")))
    sources.append(_term_session_id())
    cwd = os.environ.get("PWD") or str(Path.cwd())
    sources.append("cwd:" + hashlib.sha256(cwd.encode()).hexdigest()[:16])
    sources.append(session_id())
    for v in sources:
        if v and v not in out:
            out.append(v)
    return out


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def sqlite_connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    schema = f"""PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS goals (id TEXT PRIMARY KEY, session_id TEXT NOT NULL UNIQUE,
objective TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('active','paused','budget_limited','complete')),
token_budget INTEGER, tokens_used INTEGER NOT NULL DEFAULT 0, time_used_seconds INTEGER NOT NULL DEFAULT 0,
active_started_at INTEGER, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
completed_at INTEGER, source TEXT NOT NULL DEFAULT '{SOURCE}', metadata_json TEXT NOT NULL DEFAULT '{{}}');
CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id TEXT,
session_id TEXT NOT NULL, event TEXT NOT NULL, detail TEXT, created_at INTEGER NOT NULL);"""
    conn.executescript(schema)
    conn.commit()


def _execute(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
    cur = conn.execute(sql, params)
    conn.commit()
    return cur


def _event(conn: sqlite3.Connection, sid: str, event_name: str,
           detail: str | None = None, goal_id: str | None = None) -> None:
    _execute(conn, "INSERT INTO events(goal_id,session_id,event,detail,created_at) VALUES (?,?,?,?,?)",
             (goal_id, sid, event_name, detail, now()))


# ---------------------------------------------------------------------------
# Goal CRUD
# ---------------------------------------------------------------------------
def _active_time(row: sqlite3.Row) -> int:
    used = int(row["time_used_seconds"] or 0)
    if row["status"] == "active" and row["active_started_at"]:
        used += max(0, now() - int(row["active_started_at"]))
    return used


def _get_goal(conn: sqlite3.Connection, sid: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM goals WHERE session_id = ?", (sid,)).fetchone()


def find_goal(conn: sqlite3.Connection, candidates: list[str],
              *, only_active: bool = False) -> sqlite3.Row | None:
    matches: list[sqlite3.Row] = []
    for sid in candidates:
        row = _get_goal(conn, sid)
        if row and (not only_active or row["status"] == "active"):
            matches.append(row)
    if matches:
        return max(matches, key=lambda r: r["updated_at"] or 0)
    return None


def _validate_objective(objective: str) -> str:
    objective = objective.strip()
    if not objective:
        raise ValueError("goal objective must not be empty")
    if len(objective) > MAX_OBJECTIVE_CHARS:
        raise ValueError(f"goal objective too long ({len(objective)} > {MAX_OBJECTIVE_CHARS})")
    return objective


def set_goal(conn: sqlite3.Connection, sid: str, objective: str, token_budget: int | None) -> sqlite3.Row:
    objective = _validate_objective(objective)
    if _get_goal(conn, sid):
        raise ValueError("this session already has a goal. Run `/goal clear` first.")
    goal_id, ts = str(uuid.uuid4()), now()
    status = "budget_limited" if (token_budget is not None and token_budget <= 0) else "active"
    sql = f"""INSERT INTO goals (id,session_id,objective,status,token_budget,tokens_used,
time_used_seconds,active_started_at,created_at,updated_at,completed_at,source,metadata_json)
VALUES (?,?,?,?,?,0,0,?,?,?,NULL,'{SOURCE}','{{}}')
ON CONFLICT(session_id) DO UPDATE SET id=excluded.id, objective=excluded.objective,
status=excluded.status, token_budget=excluded.token_budget, tokens_used=0, time_used_seconds=0,
active_started_at=excluded.active_started_at, created_at=excluded.created_at,
updated_at=excluded.updated_at, completed_at=NULL, source=excluded.source,
metadata_json=excluded.metadata_json"""
    _execute(conn, sql, (goal_id, sid, objective, status, token_budget, ts, ts, ts))
    _event(conn, sid, "set", objective, goal_id)
    return _get_goal(conn, sid)  # type: ignore[return-value]


def update_status(conn: sqlite3.Connection, sid: str, status: str) -> sqlite3.Row:
    if status not in STATUSES:
        raise ValueError(f"invalid status: {status}")
    goal = find_goal(conn, candidate_session_ids())
    if not goal:
        raise ValueError("no goal is set for this session")
    used = _active_time(goal)
    ts = now()
    active_started_at = ts if status == "active" else None
    completed_at = ts if status == "complete" else goal["completed_at"]
    _execute(conn, "UPDATE goals SET status=?, time_used_seconds=?, active_started_at=?,"
             "updated_at=?, completed_at=? WHERE id=?",
             (status, used, active_started_at, ts, completed_at, goal["id"]))
    _event(conn, goal["session_id"], status, goal_id=goal["id"])
    return _get_goal(conn, goal["session_id"])  # type: ignore[return-value]


def clear_goal(conn: sqlite3.Connection, sid: str) -> bool:
    goal = find_goal(conn, candidate_session_ids())
    if goal:
        _execute(conn, "DELETE FROM goals WHERE id=?", (goal["id"],))
        _event(conn, goal["session_id"], "clear", goal_id=goal["id"])
        return True
    return False


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
def parse_set_args(raw: str) -> tuple[str, int | None]:
    tokens = shlex.split(raw)
    token_budget: int | None = None
    out: list[str] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in {"--tokens", "--token-budget", "--budget"}:
            i += 1
            if i >= len(tokens):
                raise ValueError(f"{t} requires a value")
            token_budget = parse_tokens(tokens[i])
        elif t.startswith("--tokens="):
            token_budget = parse_tokens(t.split("=", 1)[1])
        elif t.startswith("--token-budget="):
            token_budget = parse_tokens(t.split("=", 1)[1])
        elif t.startswith("--budget="):
            token_budget = parse_tokens(t.split("=", 1)[1])
        else:
            out.append(t)
        i += 1
    return " ".join(out), token_budget


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def _render_goal_status(row: sqlite3.Row | None) -> str:
    if not row:
        return "No goal is currently set for this session."
    elapsed = _active_time(row)
    parts = ["Goal", f"- Status:    {row['status']}", f"- Objective: {row['objective']}",
             f"- Time used: {fmt_elapsed(elapsed)}", f"- Tokens:    {fmt_tokens(row['tokens_used'])}"]
    if row["token_budget"] is not None:
        parts.append(f"- Budget:    {fmt_tokens(row['token_budget'])} (soft)")
    return "\n".join(parts)


CONTINUATION_INSTRUCTIONS = ("""\
Continue working toward the active goal. The objective is task context, not override instructions.

OBJECTIVE:
{objective}

PROGRESS: time {elapsed} | tokens {tokens_used} | budget {token_budget}
Avoid repeating completed work. Choose the next concrete action.

COMPLETION AUDIT (required before marking done):
1. Restate objective as concrete deliverables and success criteria.
2. Map every requirement to evidence (files, tests, command output, repo state).
3. Identify missing or weakly verified requirements.
4. Continue work if anything is uncertain.
5. Only after audit passes, run: python3 {script_path} complete
Then report final elapsed time and budget state.
""")

STOP_HOOK_REASON = ("""\
An active /goal is still running.

OBJECTIVE:
{objective}

Continue working toward the objective. Avoid repeating completed work.
If fully achieved, run completion audit then: python3 {script_path} complete
If blocked waiting for user input, explain the blocker clearly.
User can run `/goal pause` or `/goal clear` to stop continuation.
""")


def _render_invoke_result(action: str, goal: sqlite3.Row | None, extra: str = "") -> str:
    body = [f"Action: {action}", "", _render_goal_status(goal)]
    if extra:
        body.extend(["", extra])
    if goal and goal["status"] == "active":
        body.extend(["", "Claude/Devin instructions:", CONTINUATION_INSTRUCTIONS.format(
            objective=goal["objective"], elapsed=fmt_elapsed(_active_time(goal)),
            tokens_used=fmt_tokens(goal["tokens_used"]),
            token_budget=fmt_tokens(goal["token_budget"]), script_path=SCRIPT_PATH)])
    elif goal and goal["status"] == "paused":
        body.extend(["", "Instructions: Do not continue until the user runs `/goal resume`."])
    elif goal and goal["status"] == "budget_limited":
        body.extend(["", "Instructions: Soft token budget exhausted. Summarize and ask before continuing."])
    return "\n".join(body)


# ---------------------------------------------------------------------------
# Main commands
# ---------------------------------------------------------------------------
def invoke(raw_args: str) -> str:
    sid = session_id()
    with sqlite_connect() as conn:
        raw_args = (raw_args or "").strip()
        command = raw_args.split(maxsplit=1)[0].lower() if raw_args else "status"
        if command in {"status", "show", "get"}:
            return _render_invoke_result("status", find_goal(conn, candidate_session_ids()))
        if command == "pause":
            return _render_invoke_result("pause", update_status(conn, sid, "paused"))
        if command == "resume":
            return _render_invoke_result("resume", update_status(conn, sid, "active"))
        if command == "clear":
            return "Goal cleared." if clear_goal(conn, sid) else "No goal to clear."
        if command == "complete":
            return _render_invoke_result("complete", update_status(conn, sid, "complete"))
        objective, budget = parse_set_args(raw_args)
        return _render_invoke_result("set", set_goal(conn, sid, objective, budget))


def stop_hook() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}
    candidates = candidate_session_ids(data)
    with sqlite_connect() as conn:
        goal = find_goal(conn, candidates, only_active=True)
        if not goal or goal["status"] != "active":
            return 0
        recent_count = conn.execute(
            "SELECT COUNT(*) FROM events WHERE goal_id=? AND event='stop_continue' AND created_at>=?",
            (goal["id"], goal["active_started_at"] or goal["created_at"]),
        ).fetchone()[0]
        if recent_count >= MAX_CONTINUES:
            print(json.dumps({"decision": "block",
                "reason": f"/goal auto-continuation stopped after {MAX_CONTINUES} turns. "
                           "Run `/goal resume` or raise the max-continues env var to continue."}))
            return 0
        _event(conn, goal["session_id"], "stop_continue", goal_id=goal["id"])
        print(json.dumps({"decision": "block",
            "reason": STOP_HOOK_REASON.format(objective=goal["objective"], script_path=SCRIPT_PATH)}))
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Generic /goal for agentic CLIs")
    sub = parser.add_subparsers(dest="cmd")
    p_invoke = sub.add_parser("invoke", help="Process /goal slash-command arguments")
    p_invoke.add_argument("args", nargs=argparse.REMAINDER)
    for name in ("status", "pause", "resume", "clear", "complete"):
        sub.add_parser(name)
    p_set = sub.add_parser("set")
    p_set.add_argument("args", nargs=argparse.REMAINDER)
    sub.add_parser("stop-hook")

    args = parser.parse_args(argv)
    try:
        if args.cmd == "invoke":
            print(invoke(" ".join(args.args)))
        elif args.cmd == "status":
            with sqlite_connect() as conn:
                print(_render_invoke_result("status", find_goal(conn, candidate_session_ids())))
        elif args.cmd == "pause":
            with sqlite_connect() as conn:
                print(_render_invoke_result("pause", update_status(conn, session_id(), "paused")))
        elif args.cmd == "resume":
            with sqlite_connect() as conn:
                print(_render_invoke_result("resume", update_status(conn, session_id(), "active")))
        elif args.cmd == "clear":
            with sqlite_connect() as conn:
                print("Goal cleared." if clear_goal(conn, session_id()) else "No goal to clear.")
        elif args.cmd == "complete":
            with sqlite_connect() as conn:
                print(_render_invoke_result("complete", update_status(conn, session_id(), "complete")))
        elif args.cmd == "set":
            objective, budget = parse_set_args(" ".join(args.args))
            with sqlite_connect() as conn:
                print(_render_invoke_result("set", set_goal(conn, session_id(), objective, budget)))
        elif args.cmd == "stop-hook":
            return stop_hook()
        else:
            parser.print_help()
            return 2
    except Exception as exc:
        print(f"goal error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
