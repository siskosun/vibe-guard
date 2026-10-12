#!/usr/bin/env python3
"""Deterministic guard checks for Vibe Guard v2. Agent-facing only."""
from __future__ import annotations

import argparse
from pathlib import Path

from vg_common import json_print, load_state, repo_root, run
from goal_guard import route_gate_findings


def evidence_for(state, ident):
    return [e for e in state["evidence"].values() if ident in e.get("supports", [])]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("root")
    p.add_argument("--phase", choices=["routine", "milestone", "release"], default="routine")
    args = p.parse_args()
    state = load_state(args.root)
    rr = repo_root(args.root)
    blocks = []
    warnings = []

    route_blocks, route_warnings = route_gate_findings(state, args.root, args.phase)
    blocks.extend(route_blocks)
    warnings.extend(route_warnings)

    # Stable intent must have real evidence, not simulation alone.
    for intent in state["intents"].values():
        if intent.get("status") != "stable":
            continue
        ev = evidence_for(state, intent["id"])
        listed = [state["evidence"].get(eid) for eid in intent.get("evidence", [])]
        listed = [e for e in listed if e]
        real = [e for e in ev + listed if e.get("actor") != "agent_simulation"]
        if not real:
            blocks.append({"kind": "stable_intent_without_real_evidence", "id": intent["id"]})
        if intent["id"] not in state["mappings"]:
            warnings.append({"kind": "stable_intent_without_code_map", "id": intent["id"]})

    # Active durable choices may not depend on superseded intent.
    for dec in state["decisions"].values():
        if dec.get("status") != "active":
            continue
        bad = [iid for iid in dec.get("intents", []) if state["intents"].get(iid, {}).get("status") == "superseded"]
        if bad:
            blocks.append({"kind": "active_decision_uses_superseded_intent", "id": dec["id"], "intents": bad})
        if not dec.get("affected") and dec["id"] not in state["mappings"]:
            blocks.append({"kind": "decision_without_impact_map", "id": dec["id"]})

    # Mature scopes need active/stable intent and evidence for the main path.
    for name, scope in state["scopes"].items():
        maturity = scope.get("maturity", "explore")
        intent_ids = scope.get("intents", [])
        active_intents = [state["intents"].get(i) for i in intent_ids]
        active_intents = [i for i in active_intents if i and i.get("status") != "superseded"]
        if maturity in {"converging", "production"} and not active_intents:
            blocks.append({"kind": "mature_scope_without_intent", "scope": name})
        if maturity == "production":
            stable = [i for i in active_intents if i.get("status") == "stable"]
            if not stable:
                blocks.append({"kind": "production_scope_without_stable_intent", "scope": name})
            scope_evidence = [e for e in state["evidence"].values() if f"scope:{name}" in e.get("covers", []) and e.get("mode") in {"task_completion", "automated_check", "observed_behavior"}]
            if not scope_evidence:
                blocks.append({"kind": "production_scope_without_main_path_check", "scope": name})
            if scope.get("user_facing"):
                for ui_state in scope.get("required_states", []):
                    tag = f"state:{name}:{ui_state}"
                    if not any(tag in e.get("covers", []) for e in state["evidence"].values()):
                        blocks.append({"kind": "missing_user_state_check", "scope": name, "state": ui_state})
            for intent in stable:
                if intent["id"] not in state["mappings"]:
                    blocks.append({"kind": "production_intent_without_code_map", "scope": name, "intent": intent["id"]})

    # Disposable trials should not leave abandoned local work areas/branches behind.
    active_probe_ids = {p["id"] for p in state["probes"].values() if p.get("status") == "active"}
    for probe in state["probes"].values():
        workspace = probe.get("workspace")
        if probe.get("status") != "active" and probe.get("disposable") and workspace and Path(workspace).exists():
            blocks.append({"kind": "closed_probe_workspace_still_exists", "probe": probe["id"]})
        if probe.get("comparison") == "compound" and probe.get("status") == "accepted":
            warnings.append({"kind": "compound_probe_cannot_support_single_factor_claim", "probe": probe["id"]})

    branches = run(["git", "-C", str(rr), "for-each-ref", "--format=%(refname:short)", "refs/heads/vibe-guard/probe/"], check=False).stdout.splitlines()
    for branch in branches:
        pid = branch.rsplit("/", 1)[-1]
        if pid not in active_probe_ids:
            blocks.append({"kind": "stale_probe_branch", "probe": pid})

    # Legacy migrated choices remain visible until reviewed.
    for dec in state["decisions"].values():
        if dec.get("status") == "active" and dec.get("needs_review"):
            warnings.append({"kind": "legacy_decision_needs_review", "id": dec["id"]})

    json_print({
        "ok": not blocks,
        "blocks": blocks,
        "warnings": warnings,
        "counts": {
            "observations": len(state["observations"]),
            "open_hypotheses": sum(1 for h in state["hypotheses"].values() if h.get("status") in {"open", "weakened"}),
            "active_probes": len(active_probe_ids),
            "stable_intents": sum(1 for i in state["intents"].values() if i.get("status") == "stable"),
            "active_decisions": sum(1 for d in state["decisions"].values() if d.get("status") == "active"),
        },
    })
    if blocks:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
