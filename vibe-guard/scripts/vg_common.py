#!/usr/bin/env python3
"""Shared internals for Vibe Guard v2. Agent-facing only."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

STATE_VERSION = 2


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run(cmd: list[str], cwd: str | Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, encoding="utf-8", errors="replace", capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(json.dumps({
            "code": "COMMAND_FAILED",
            "command": cmd,
            "returncode": p.returncode,
            "stdout": p.stdout[-4000:],
            "stderr": p.stderr[-4000:],
        }, ensure_ascii=False))
    return p


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def git_available() -> bool:
    return command_exists("git")


def repo_root(path: str | Path) -> Path:
    p = Path(path).resolve()
    if not git_available():
        raise RuntimeError(json.dumps({"code": "LOCAL_HISTORY_TOOL_MISSING"}))
    out = run(["git", "-C", str(p), "rev-parse", "--show-toplevel"], check=False)
    if out.returncode != 0:
        raise RuntimeError(json.dumps({"code": "PROJECT_NOT_PREPARED", "path": str(p)}))
    return Path(out.stdout.strip()).resolve()


def git_common_dir(root: str | Path) -> Path:
    rr = repo_root(root)
    out = run(["git", "-C", str(rr), "rev-parse", "--git-common-dir"])
    common = Path(out.stdout.strip())
    if not common.is_absolute():
        common = (rr / common).resolve()
    return common


def state_dir(root: str | Path) -> Path:
    d = git_common_dir(root) / "vibe-guard"
    d.mkdir(parents=True, exist_ok=True)
    return d


def events_path(root: str | Path) -> Path:
    return state_dir(root) / "events.jsonl"


def artifacts_dir(root: str | Path) -> Path:
    d = state_dir(root) / "artifacts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def workspace_home(root: str | Path) -> Path:
    rr = repo_root(root)
    digest = hashlib.sha256(str(rr).encode("utf-8")).hexdigest()[:12]
    d = Path.home() / ".vibe-guard" / "workspaces" / digest
    d.mkdir(parents=True, exist_ok=True)
    return d


def append_event(root: str | Path, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    path = events_path(root)
    event = {
        "event_version": 1,
        "type": event_type,
        "at": utc_now(),
        **payload,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def read_events(root: str | Path) -> list[dict[str, Any]]:
    path = events_path(root)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise RuntimeError(json.dumps({"code": "STATE_DAMAGED", "line": lineno, "detail": str(exc)})) from exc
    return events


def next_id(state: dict[str, Any], key: str, prefix: str) -> str:
    values = state.get(key, {})
    nums: list[int] = []
    for ident in values:
        if ident.startswith(prefix + "-"):
            try:
                nums.append(int(ident.split("-", 1)[1]))
            except ValueError:
                pass
    return f"{prefix}-{max(nums, default=0) + 1:03d}"


def replay(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    state: dict[str, Any] = {
        "version": STATE_VERSION,
        "observations": {},
        "hypotheses": {},
        "probes": {},
        "intents": {},
        "decisions": {},
        "evidence": {},
        "scopes": {},
        "checkpoints": {},
        "mappings": {},
        "migrations": [],
        "goal_original": None,
        "goal_active": None,
        "goal_history": [],
        "route_reviews": {},
        "updated_at": None,
    }
    for ev in events:
        typ = ev.get("type")
        state["updated_at"] = ev.get("at")
        if typ == "observation_added":
            state["observations"][ev["id"]] = dict(ev)
        elif typ == "hypothesis_added":
            state["hypotheses"][ev["id"]] = dict(ev)
        elif typ == "hypothesis_status":
            if ev["id"] in state["hypotheses"]:
                state["hypotheses"][ev["id"]]["status"] = ev["status"]
                state["hypotheses"][ev["id"]]["status_reason"] = ev.get("reason", "")
                state["hypotheses"][ev["id"]]["updated_at"] = ev.get("at")
        elif typ == "probe_added":
            state["probes"][ev["id"]] = dict(ev)
        elif typ == "probe_status":
            if ev["id"] in state["probes"]:
                state["probes"][ev["id"]]["status"] = ev["status"]
                state["probes"][ev["id"]]["result"] = ev.get("result", "")
                state["probes"][ev["id"]]["updated_at"] = ev.get("at")
        elif typ == "intent_added":
            state["intents"][ev["id"]] = dict(ev)
        elif typ == "intent_status":
            if ev["id"] in state["intents"]:
                state["intents"][ev["id"]]["status"] = ev["status"]
                state["intents"][ev["id"]]["updated_at"] = ev.get("at")
        elif typ == "intent_superseded":
            if ev["id"] in state["intents"]:
                state["intents"][ev["id"]]["status"] = "superseded"
                state["intents"][ev["id"]]["superseded_by"] = ev["by"]
                state["intents"][ev["id"]]["updated_at"] = ev.get("at")
        elif typ == "decision_added":
            state["decisions"][ev["id"]] = dict(ev)
        elif typ == "decision_superseded":
            if ev["id"] in state["decisions"]:
                state["decisions"][ev["id"]]["status"] = "superseded"
                state["decisions"][ev["id"]]["superseded_by"] = ev["by"]
                state["decisions"][ev["id"]]["updated_at"] = ev.get("at")
        elif typ == "evidence_added":
            state["evidence"][ev["id"]] = dict(ev)
        elif typ == "scope_set":
            prev = state["scopes"].get(ev["name"], {})
            merged = dict(prev)
            merged.update(ev)
            state["scopes"][ev["name"]] = merged
        elif typ == "scope_signal":
            prev = state["scopes"].setdefault(ev["name"], {"name": ev["name"], "maturity": "explore", "intents": [], "required_states": []})
            prev["maturity"] = ev["maturity"]
            prev.setdefault("signals", []).append({"signal": ev["signal"], "at": ev.get("at")})
        elif typ == "checkpoint_added":
            state["checkpoints"][ev["id"]] = dict(ev)
        elif typ == "mapping_set":
            state["mappings"][ev["subject"]] = dict(ev)
        elif typ == "migration":
            state["migrations"].append(dict(ev))
        elif typ == "goal_created":
            if state["goal_original"] is None:
                state["goal_original"] = dict(ev)
                state["goal_active"] = dict(ev)
                state["goal_history"].append(dict(ev))
        elif typ == "goal_amended":
            if state["goal_original"] is not None:
                state["goal_active"] = dict(ev)
                state["goal_history"].append(dict(ev))
        elif typ == "route_review_opened":
            state["route_reviews"][ev["id"]] = dict(ev)
        elif typ == "route_review_closed":
            review = state["route_reviews"].get(ev["id"])
            if review is not None and review.get("status") == "open":
                review.update({key: value for key, value in ev.items() if key not in {"type", "event_version"}})
                review["status"] = "closed"
        elif typ == "route_review_resolved":
            review = state["route_reviews"].get(ev["id"])
            if review is not None:
                review["resolved"] = True
                review["resolution"] = ev.get("resolution", "")
                review["resolution_evidence"] = ev.get("evidence", [])
                review["resolution_at"] = ev.get("at")
    return state


def load_state(root: str | Path) -> dict[str, Any]:
    return replay(read_events(root))


def json_print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def platform_name() -> str:
    name = platform.system().lower()
    if name.startswith("windows"):
        return "windows"
    if name.startswith("darwin"):
        return "macos"
    if name.startswith("linux"):
        return "linux"
    return name


def maturity_rank(value: str) -> int:
    return {"explore": 0, "converging": 1, "production": 2}[value]


def max_maturity(a: str, b: str) -> str:
    return a if maturity_rank(a) >= maturity_rank(b) else b
