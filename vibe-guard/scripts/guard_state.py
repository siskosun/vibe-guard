#!/usr/bin/env python3
"""Vibe Guard v2 cognition state. Agent-facing only.

All durable learning is stored outside the checked-out project tree under the local
project history directory, so returning to an older code snapshot never erases newer
observations or product learning.
"""
from __future__ import annotations

import argparse
from typing import Any

from vg_common import append_event, json_print, load_state, max_maturity, next_id, utc_now


def require(state: dict[str, Any], bucket: str, ident: str) -> dict[str, Any]:
    try:
        return state[bucket][ident]
    except KeyError as exc:
        raise SystemExit(f"missing:{bucket}:{ident}") from exc


def add_observation(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    ident = next_id(state, "observations", "O")
    append_event(a.root, "observation_added", {
        "id": ident,
        "summary": a.summary,
        "source": a.source,
        "probe": a.probe or None,
        "checkpoint": a.checkpoint or None,
        "scope": a.scope or None,
    })
    print(ident)


def add_hypothesis(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    for oid in a.based_on:
        require(state, "observations", oid)
    ident = next_id(state, "hypotheses", "H")
    append_event(a.root, "hypothesis_added", {
        "id": ident,
        "statement": a.statement,
        "status": "open",
        "based_on": a.based_on,
        "scope": a.scope or None,
        "alternatives": a.alternative,
    })
    print(ident)


def set_hypothesis_status(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    require(state, "hypotheses", a.id)
    append_event(a.root, "hypothesis_status", {
        "id": a.id,
        "status": a.status,
        "reason": a.reason or "",
    })
    print(a.id)


def add_probe(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    for hid in a.hypothesis:
        require(state, "hypotheses", hid)
    ident = next_id(state, "probes", "P")
    append_event(a.root, "probe_added", {
        "id": ident,
        "question": a.question,
        "scope": a.scope or None,
        "hypotheses": a.hypothesis,
        "variants": a.variant,
        "comparison": a.comparison,
        "status": "active",
        "disposable": not a.keep_by_default,
        "workspace": a.workspace or None,
        "baseline_checkpoint": a.baseline_checkpoint or None,
    })
    print(ident)


def set_probe_status(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    require(state, "probes", a.id)
    append_event(a.root, "probe_status", {
        "id": a.id,
        "status": a.status,
        "result": a.result or "",
    })
    print(a.id)


def add_intent(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    for eid in a.evidence:
        require(state, "evidence", eid)
    ident = next_id(state, "intents", "I")
    append_event(a.root, "intent_added", {
        "id": ident,
        "statement": a.statement,
        "scope": a.scope,
        "status": a.status,
        "core_loop": a.core_loop or "",
        "non_goals": a.non_goal,
        "acceptance_examples": a.acceptance,
        "evidence": a.evidence,
        "superseded_by": None,
    })
    print(ident)


def set_intent_status(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    require(state, "intents", a.id)
    append_event(a.root, "intent_status", {"id": a.id, "status": a.status})
    print(a.id)


def supersede_intent(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    require(state, "intents", a.id)
    require(state, "intents", a.by)
    append_event(a.root, "intent_superseded", {"id": a.id, "by": a.by})
    print(a.id)


def add_decision(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    for iid in a.intent:
        intent = require(state, "intents", iid)
        if intent.get("status") == "superseded":
            raise SystemExit(f"superseded-intent:{iid}")
    if not a.affected:
        raise SystemExit("affected-path-required")
    ident = next_id(state, "decisions", "D")
    append_event(a.root, "decision_added", {
        "id": ident,
        "statement": a.statement,
        "scope": a.scope,
        "reason": a.reason,
        "status": "active",
        "intents": a.intent,
        "affected": a.affected,
        "superseded_by": None,
    })
    print(ident)


def supersede_decision(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    require(state, "decisions", a.id)
    if a.by:
        require(state, "decisions", a.by)
    append_event(a.root, "decision_superseded", {"id": a.id, "by": a.by or None})
    print(a.id)


def add_evidence(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    for ident in a.supports:
        bucket = None
        if ident.startswith("H-"):
            bucket = "hypotheses"
        elif ident.startswith("I-"):
            bucket = "intents"
        elif ident.startswith("D-"):
            bucket = "decisions"
        elif ident.startswith("P-"):
            bucket = "probes"
        if bucket:
            require(state, bucket, ident)
    ident = next_id(state, "evidence", "E")
    append_event(a.root, "evidence_added", {
        "id": ident,
        "summary": a.summary,
        "actor": a.actor,
        "mode": a.mode,
        "supports": a.supports,
        "covers": a.covers,
        "artifact": a.artifact or None,
        "probe": a.probe or None,
        "checkpoint": a.checkpoint or None,
    })
    print(ident)


def set_scope(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    for iid in a.intent:
        require(state, "intents", iid)
    append_event(a.root, "scope_set", {
        "name": a.name,
        "maturity": a.maturity,
        "intents": a.intent,
        "required_states": a.required_state,
        "user_facing": bool(a.user_facing),
    })
    print(a.name)


SIGNAL_MINIMUM = {
    "retained_data": "production",
    "external_user": "production",
    "public_use": "production",
    "access_control": "production",
    "payment": "production",
    "shared_boundary": "converging",
    "depended_on": "converging",
    "long_lived": "converging",
}


def add_scope_signal(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    current = state["scopes"].get(a.name, {}).get("maturity", "explore")
    target = max_maturity(current, SIGNAL_MINIMUM[a.signal])
    append_event(a.root, "scope_signal", {"name": a.name, "signal": a.signal, "maturity": target})
    print(target)


def set_mapping(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    if a.subject.startswith("I-"):
        require(state, "intents", a.subject)
    elif a.subject.startswith("D-"):
        require(state, "decisions", a.subject)
    else:
        raise SystemExit("mapping-subject-must-be-intent-or-decision")
    append_event(a.root, "mapping_set", {
        "subject": a.subject,
        "paths": a.path,
        "checks": a.check,
    })
    print(a.subject)


def add_checkpoint_record(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    ident = a.id or next_id(state, "checkpoints", "C")
    append_event(a.root, "checkpoint_added", {
        "id": ident,
        "label": a.label,
        "commit": a.commit,
        "note": a.note or "",
        "artifacts": a.artifact,
        "probe": a.probe or None,
    })
    print(ident)


def show_status(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    if a.json:
        json_print(state)
        return
    out = {
        "open_hypotheses": [x["id"] for x in state["hypotheses"].values() if x.get("status") in {"open", "weakened"}],
        "active_probes": [x["id"] for x in state["probes"].values() if x.get("status") == "active"],
        "stable_intents": [x["id"] for x in state["intents"].values() if x.get("status") == "stable"],
        "active_decisions": [x["id"] for x in state["decisions"].values() if x.get("status") == "active"],
        "scopes": {k: v.get("maturity") for k, v in state["scopes"].items()},
        "latest_checkpoint": list(state["checkpoints"].keys())[-1] if state["checkpoints"] else None,
        "goal_version": state["goal_active"]["version"] if state["goal_active"] else None,
        "open_route_reviews": [r["id"] for r in state["route_reviews"].values() if r.get("status") == "open"],
        "unresolved_route_holds": [r["id"] for r in state["route_reviews"].values() if r.get("verdict") in {"simplify", "redirect", "rollback", "stop", "escalate"} and not r.get("resolved")],
    }
    json_print(out)


def show_context(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    scope = a.scope
    relevant_intents = [x for x in state["intents"].values() if x.get("scope") == scope and x.get("status") != "superseded"]
    intent_ids = {x["id"] for x in relevant_intents}
    relevant_h = [x for x in state["hypotheses"].values() if x.get("scope") == scope and x.get("status") in {"open", "supported", "weakened", "defaulted"}]
    h_obs = {oid for h in relevant_h for oid in h.get("based_on", [])}
    relevant_obs = [x for x in state["observations"].values() if x["id"] in h_obs or x.get("scope") == scope]
    relevant_decisions = [x for x in state["decisions"].values() if x.get("status") == "active" and (x.get("scope") == scope or intent_ids.intersection(x.get("intents", [])))]
    relevant_evidence = [x for x in state["evidence"].values() if intent_ids.intersection(x.get("supports", [])) or any(h["id"] in x.get("supports", []) for h in relevant_h)]
    json_print({
        "scope": scope,
        "original_goal": state["goal_original"],
        "active_goal": state["goal_active"],
        "intents": relevant_intents,
        "hypotheses": relevant_h,
        "observations": relevant_obs[-20:],
        "decisions": relevant_decisions,
        "evidence": relevant_evidence[-20:],
    })


def init_state(a: argparse.Namespace) -> None:
    append_event(a.root, "init", {"version": 2, "note": "vibe-guard-v2"})
    json_print({"ok": True, "at": utc_now()})


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Vibe Guard v2 internal cognition state")
    sp = p.add_subparsers(dest="cmd", required=True)

    s = sp.add_parser("init"); s.add_argument("root"); s.set_defaults(func=init_state)

    s = sp.add_parser("observation-add"); s.add_argument("root"); s.add_argument("summary"); s.add_argument("--source", choices=["builder", "target_user", "observed_behavior", "other"], default="builder"); s.add_argument("--scope", default=""); s.add_argument("--probe", default=""); s.add_argument("--checkpoint", default=""); s.set_defaults(func=add_observation)

    s = sp.add_parser("hypothesis-add"); s.add_argument("root"); s.add_argument("statement"); s.add_argument("--based-on", action="append", default=[], required=True); s.add_argument("--scope", default=""); s.add_argument("--alternative", action="append", default=[]); s.set_defaults(func=add_hypothesis)
    s = sp.add_parser("hypothesis-status"); s.add_argument("root"); s.add_argument("id"); s.add_argument("--status", choices=["open", "supported", "weakened", "rejected", "defaulted"], required=True); s.add_argument("--reason", default=""); s.set_defaults(func=set_hypothesis_status)

    s = sp.add_parser("probe-add"); s.add_argument("root"); s.add_argument("question"); s.add_argument("--scope", default=""); s.add_argument("--hypothesis", action="append", default=[]); s.add_argument("--variant", action="append", default=[]); s.add_argument("--comparison", choices=["single_factor", "compound"], default="single_factor"); s.add_argument("--workspace", default=""); s.add_argument("--baseline-checkpoint", default=""); s.add_argument("--keep-by-default", action="store_true"); s.set_defaults(func=add_probe)
    s = sp.add_parser("probe-status"); s.add_argument("root"); s.add_argument("id"); s.add_argument("--status", choices=["active", "accepted", "rejected", "closed"], required=True); s.add_argument("--result", default=""); s.set_defaults(func=set_probe_status)

    s = sp.add_parser("intent-add"); s.add_argument("root"); s.add_argument("statement"); s.add_argument("--scope", required=True); s.add_argument("--status", choices=["provisional", "stable"], default="provisional"); s.add_argument("--core-loop", default=""); s.add_argument("--non-goal", action="append", default=[]); s.add_argument("--acceptance", action="append", default=[]); s.add_argument("--evidence", action="append", default=[]); s.set_defaults(func=add_intent)
    s = sp.add_parser("intent-status"); s.add_argument("root"); s.add_argument("id"); s.add_argument("--status", choices=["provisional", "stable"], required=True); s.set_defaults(func=set_intent_status)
    s = sp.add_parser("intent-supersede"); s.add_argument("root"); s.add_argument("id"); s.add_argument("--by", required=True); s.set_defaults(func=supersede_intent)

    s = sp.add_parser("decision-add"); s.add_argument("root"); s.add_argument("statement"); s.add_argument("--scope", required=True); s.add_argument("--reason", required=True); s.add_argument("--intent", action="append", default=[], required=True); s.add_argument("--affected", action="append", default=[], required=True); s.set_defaults(func=add_decision)
    s = sp.add_parser("decision-supersede"); s.add_argument("root"); s.add_argument("id"); s.add_argument("--by", default=""); s.set_defaults(func=supersede_decision)

    s = sp.add_parser("evidence-add"); s.add_argument("root"); s.add_argument("summary"); s.add_argument("--actor", choices=["builder", "target_user", "agent_simulation", "system"], required=True); s.add_argument("--mode", choices=["stated_preference", "observed_behavior", "task_completion", "automated_check", "calibration_example"], required=True); s.add_argument("--supports", action="append", default=[]); s.add_argument("--covers", action="append", default=[]); s.add_argument("--artifact", default=""); s.add_argument("--probe", default=""); s.add_argument("--checkpoint", default=""); s.set_defaults(func=add_evidence)

    s = sp.add_parser("scope-set"); s.add_argument("root"); s.add_argument("name"); s.add_argument("--maturity", choices=["explore", "converging", "production"], default="explore"); s.add_argument("--intent", action="append", default=[]); s.add_argument("--required-state", action="append", default=[]); s.add_argument("--user-facing", action="store_true"); s.set_defaults(func=set_scope)
    s = sp.add_parser("scope-signal"); s.add_argument("root"); s.add_argument("name"); s.add_argument("--signal", choices=sorted(SIGNAL_MINIMUM), required=True); s.set_defaults(func=add_scope_signal)

    s = sp.add_parser("mapping-set"); s.add_argument("root"); s.add_argument("subject"); s.add_argument("--path", action="append", default=[]); s.add_argument("--check", action="append", default=[]); s.set_defaults(func=set_mapping)

    s = sp.add_parser("checkpoint-add"); s.add_argument("root"); s.add_argument("--id", default=""); s.add_argument("--label", required=True); s.add_argument("--commit", required=True); s.add_argument("--note", default=""); s.add_argument("--artifact", action="append", default=[]); s.add_argument("--probe", default=""); s.set_defaults(func=add_checkpoint_record)

    s = sp.add_parser("status"); s.add_argument("root"); s.add_argument("--json", action="store_true"); s.set_defaults(func=show_status)
    s = sp.add_parser("context"); s.add_argument("root"); s.add_argument("scope"); s.set_defaults(func=show_context)
    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
