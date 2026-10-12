#!/usr/bin/env python3
"""Migrate Vibe Guard v1 local state into v2 append-only cognition state."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from vg_common import append_event, events_path, load_state, next_id


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("root")
    args = p.parse_args()
    root = Path(args.root).resolve()
    legacy = root / ".vibe-guard" / "state.json"
    if not legacy.exists():
        print(json.dumps({"code": "NO_LEGACY_STATE"}))
        return
    state = load_state(root)
    if any(m.get("source") == str(legacy) for m in state.get("migrations", [])):
        print(json.dumps({"code": "ALREADY_MIGRATED"}))
        return
    old = json.loads(legacy.read_text(encoding="utf-8"))

    # Preserve raw legacy snapshot in the event stream for auditability.
    append_event(root, "migration", {"source": str(legacy), "legacy_version": old.get("version", 1), "snapshot": old})
    state = load_state(root)

    for item in old.get("friction", []):
        ident = next_id(state, "observations", "O")
        append_event(root, "observation_added", {"id": ident, "summary": item.get("summary", ""), "source": "builder", "scope": None, "probe": None, "checkpoint": None, "legacy": item.get("id")})
        state = load_state(root)
    for item in old.get("learnings", []):
        ident = next_id(state, "observations", "O")
        append_event(root, "observation_added", {"id": ident, "summary": item.get("summary", ""), "source": "other", "scope": None, "probe": None, "checkpoint": None, "legacy": item.get("id")})
        state = load_state(root)
    for item in old.get("assumptions", []):
        ident = next_id(state, "hypotheses", "H")
        status = {"open": "open", "validated": "supported", "invalidated": "rejected"}.get(item.get("status"), "open")
        append_event(root, "hypothesis_added", {"id": ident, "statement": item.get("statement", ""), "status": status, "based_on": [], "scope": None, "alternatives": [], "legacy": item.get("id"), "legacy_kind": "assumption"})
        state = load_state(root)
    for item in old.get("evidence", []):
        ident = next_id(state, "evidence", "E")
        append_event(root, "evidence_added", {"id": ident, "summary": item.get("summary", ""), "actor": "system", "mode": "automated_check", "supports": [], "covers": [], "artifact": None, "probe": None, "checkpoint": None, "legacy": item.get("id")})
        state = load_state(root)
    for item in old.get("decisions", []):
        ident = next_id(state, "decisions", "D")
        append_event(root, "decision_added", {"id": ident, "statement": item.get("statement", ""), "scope": "legacy", "reason": item.get("reason", "migrated from v1"), "status": item.get("status", "active"), "intents": [], "affected": [], "superseded_by": item.get("superseded_by"), "legacy": item.get("id"), "needs_review": True})
        state = load_state(root)
    print(json.dumps({"code": "MIGRATED", "source": str(legacy)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
