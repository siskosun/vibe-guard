#!/usr/bin/env python3
"""Goal contract and route reappraisal for Vibe Guard.

The code can require a record and a matching workspace snapshot. It cannot
prove reviewer independence, test truthfulness, or real user authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path
from typing import Any

from vg_common import append_event, json_print, load_state, next_id, repo_root, run

HOLD_VERDICTS = {"simplify", "redirect", "rollback", "stop", "escalate"}
ALL_VERDICTS = ["continue", *sorted(HOLD_VERDICTS)]
TRIGGERS = ["milestone", "scope_expansion", "architecture", "repeated_failure", "release", "manual"]
MAX_UNTRACKED_BYTES = 128 * 1024 * 1024


def workspace_snapshot(root: str | Path) -> dict[str, Any]:
    """Fingerprint tracked diffs and small untracked files, not ignored paths."""
    rr = repo_root(root)

    def git_bytes(*args: str, check: bool = True) -> bytes:
        process = subprocess.run(["git", "-C", str(rr), *args], capture_output=True, check=False)
        if check and process.returncode:
            raise RuntimeError(f"git-command-failed:{args[0]}")
        return process.stdout

    head_result = run(["git", "-C", str(rr), "rev-parse", "HEAD"], check=False)
    head = head_result.stdout.strip() if head_result.returncode == 0 else "UNBORN"
    h = hashlib.sha256()
    h.update(head.encode("ascii"))
    if head != "UNBORN":
        h.update(git_bytes("diff", "--binary", "HEAD"))
    else:
        h.update(git_bytes("diff", "--binary"))
        h.update(git_bytes("diff", "--cached", "--binary"))
    untracked_names = [p for p in git_bytes("ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if p]
    used = 0
    for raw_name in sorted(untracked_names):
        # Decode filesystem paths without losing undecodable bytes.
        filename = raw_name.decode("utf-8", errors="surrogateescape")
        path = rr / filename
        h.update(raw_name + b"\0")
        if path.is_symlink():
            h.update(path.readlink().as_posix().encode("utf-8", errors="surrogateescape"))
            continue
        if not path.is_file():
            raise RuntimeError("unreadable-untracked-path")
        used += path.stat().st_size
        if used > MAX_UNTRACKED_BYTES:
            raise RuntimeError("untracked-files-too-large-for-review-snapshot")
        with path.open("rb") as fd:
            for block in iter(lambda: fd.read(1024 * 1024), b""):
                h.update(block)
    status = git_bytes("status", "--porcelain=v1", "--untracked-files=normal")
    return {
        "head": head,
        "fingerprint": h.hexdigest(),
        "changed_files": status.decode("utf-8", errors="replace").splitlines()[:80],
        "untracked_count": len(untracked_names),
        "note": "Git-tracked and non-ignored untracked files only; no ignored/generated files",
    }


def required_goal(state: dict[str, Any]) -> dict[str, Any]:
    goal = state.get("goal_active")
    if not goal:
        raise SystemExit("goal-not-set")
    return goal


def nonempty(value: str, field: str) -> str:
    value = value.strip()
    if not value:
        raise SystemExit(f"{field}-required")
    return value


def make_goal(a: argparse.Namespace, previous: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "version": 1 if previous is None else previous["version"] + 1,
        "outcome": nonempty(a.outcome, "outcome"),
        "success": [nonempty(x, "success") for x in a.success],
        "non_goals": a.non_goal if a.non_goal is not None else (previous or {}).get("non_goals", []),
        "constraints": a.constraint if a.constraint is not None else (previous or {}).get("constraints", []),
        "stop_conditions": a.stop_condition if a.stop_condition is not None else (previous or {}).get("stop_conditions", []),
        "scope": a.scope if a.scope is not None else (previous or {}).get("scope", ""),
    }


def goal_set(a: argparse.Namespace) -> None:
    if load_state(a.root)["goal_original"] is not None:
        raise SystemExit("goal-already-set-use-amend-with-user-authorization")
    ev = append_event(a.root, "goal_created", make_goal(a, None))
    json_print({"created": True, "version": ev["version"]})


def goal_amend(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    previous = required_goal(state)
    changed = make_goal(a, previous)
    if all(changed[k] == previous.get(k) for k in ["outcome", "success", "non_goals", "constraints", "stop_conditions", "scope"]):
        raise SystemExit("no-goal-change")
    changed["user_request_quote"] = nonempty(a.user_quote, "explicit-user-request-quote")
    changed["reason"] = nonempty(a.reason, "reason")
    append_event(a.root, "goal_amended", changed)
    json_print({"amended": True, "version": changed["version"], "original_retained": True})


def goal_show(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    json_print({"original": state["goal_original"], "active": state["goal_active"], "revisions": len(state["goal_history"])})


def review_open(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    goal = required_goal(state)
    if any(r.get("status") == "open" for r in state["route_reviews"].values()):
        raise SystemExit("an-open-review-must-be-closed-first")
    snapshot = workspace_snapshot(a.root)
    ident = next_id(state, "route_reviews", "R")
    append_event(a.root, "route_review_opened", {
        "id": ident,
        "status": "open",
        "trigger": a.trigger,
        "proposal": a.proposal or "",
        "snapshot": snapshot,
        "goal_version": goal["version"],
        "resolved": False,
    })
    # Deliberately do not include the agent's previous plan, time spent,
    # progress narrative, or a preferred verdict.
    json_print({
        "review_id": ident,
        "original_goal": state["goal_original"],
        "active_goal": goal,
        "trigger": a.trigger,
        "proposed_next_change": a.proposal or "",
        "observable_workspace": snapshot,
        "review_questions": [
            "Would you choose this route from scratch, ignoring sunk cost?",
            "What observable result proves a success condition, rather than activity?",
            "What is the simplest feasible alternative, including stopping?",
            "What should be removed or reversed before any further work?",
        ],
        "important": "Use fresh review context when available. Do not treat this generated prompt as proof of an independent reviewer.",
    })


def require_open(state: dict[str, Any], ident: str) -> dict[str, Any]:
    review = state["route_reviews"].get(ident)
    if review is None or review.get("status") != "open":
        raise SystemExit("review-missing-or-not-open")
    return review


def review_close(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    review = require_open(state, a.id)
    current_goal = required_goal(state)
    if review["goal_version"] != current_goal["version"]:
        raise SystemExit("goal-changed-reopen-review")
    if review["snapshot"]["fingerprint"] != workspace_snapshot(a.root)["fingerprint"]:
        raise SystemExit("workspace-changed-reopen-review")
    if a.verdict in HOLD_VERDICTS and not a.next_action.strip():
        raise SystemExit("hold-requires-next-action")
    append_event(a.root, "route_review_closed", {
        "id": a.id,
        "verdict": a.verdict,
        "reviewer": a.reviewer,
        "actual_evidence": [nonempty(x, "evidence") for x in a.evidence],
        "alternative": nonempty(a.alternative, "alternative"),
        "remaining_cost": nonempty(a.remaining_cost, "remaining-cost"),
        "rationale": nonempty(a.rationale, "rationale"),
        "next_action": a.next_action.strip(),
        "resolved": a.verdict == "continue",
    })
    json_print({"review_id": a.id, "verdict": a.verdict, "requires_action": a.verdict in HOLD_VERDICTS})


def review_resolve(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    review = state["route_reviews"].get(a.id)
    if not review or review.get("status") != "closed" or review.get("verdict") not in HOLD_VERDICTS:
        raise SystemExit("not-a-closed-hold-review")
    if review.get("resolved"):
        raise SystemExit("review-already-resolved")
    goal = required_goal(state)
    if review["goal_version"] != goal["version"]:
        raise SystemExit("goal-changed-no-resolution-needed")
    user_quote = (a.user_quote or "").strip()
    if review["verdict"] in {"stop", "escalate"} and not user_quote:
        raise SystemExit("stop-or-escalation-requires-explicit-user-request")
    if review["snapshot"]["fingerprint"] == workspace_snapshot(a.root)["fingerprint"] and not user_quote:
        raise SystemExit("no-observable-change-or-explicit-new-user-information")
    append_event(a.root, "route_review_resolved", {
        "id": a.id,
        "resolution": nonempty(a.resolution, "resolution"),
        "evidence": [nonempty(x, "evidence") for x in a.evidence],
        "user_request_quote": user_quote,
    })
    json_print({"resolved": a.id, "fresh-review-still-required": True})


def route_gate_findings(state: dict[str, Any], root: str, phase: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blocks: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    goal = state.get("goal_active")
    if goal is None:
        if phase in {"milestone", "release"}:
            blocks.append({"kind": "goal_contract_missing"})
        else:
            warnings.append({"kind": "goal_contract_not_initialized_legacy_compatible"})
        return blocks, warnings
    version = goal["version"]
    reviews = [r for r in state["route_reviews"].values() if r.get("goal_version") == version]
    for review in reviews:
        if review.get("status") == "open":
            blocks.append({"kind": "route_review_open", "id": review["id"]})
        elif review.get("verdict") in HOLD_VERDICTS and not review.get("resolved"):
            blocks.append({"kind": "route_review_requires_action", "id": review["id"], "verdict": review["verdict"]})
    if phase in {"milestone", "release"}:
        snapshot = workspace_snapshot(root)
        # Only the most recent review can authorize completion. A prior
        # "continue" must not be reused after a later hold, even if the hold
        # was resolved solely on the basis of a claimed user instruction.
        # Dict insertion order follows the append-only review-open event log.
        latest = reviews[-1] if reviews else None
        valid = bool(
            latest
            and latest.get("status") == "closed"
            and latest.get("verdict") == "continue"
            and latest.get("snapshot", {}).get("fingerprint") == snapshot["fingerprint"]
            and (phase != "release" or latest.get("trigger") == "release")
        )
        if not valid:
            blocks.append({"kind": "fresh_route_review_required", "phase": phase, "goal_version": version})
        elif latest.get("reviewer") == "self":
            warnings.append({"kind": "review_self_assessed_not_independent", "id": latest["id"]})
        else:
            warnings.append({"kind": "reviewer_independence_declared_not_technically_verified", "id": latest["id"]})
    return blocks, warnings


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Vibe Guard goal contract and route review")
    sp = p.add_subparsers(dest="command", required=True)
    s = sp.add_parser("goal-set")
    s.add_argument("root"); s.add_argument("--outcome", required=True)
    s.add_argument("--success", action="append", required=True)
    s.add_argument("--non-goal", action="append", default=[])
    s.add_argument("--constraint", action="append", default=[])
    s.add_argument("--stop-condition", action="append", default=[])
    s.add_argument("--scope", default="")
    s.set_defaults(func=goal_set)
    s = sp.add_parser("goal-amend")
    s.add_argument("root"); s.add_argument("--outcome", required=True)
    s.add_argument("--success", action="append", required=True)
    s.add_argument("--non-goal", action="append", default=None)
    s.add_argument("--constraint", action="append", default=None)
    s.add_argument("--stop-condition", action="append", default=None)
    s.add_argument("--scope", default=None)
    s.add_argument("--user-quote", required=True); s.add_argument("--reason", required=True)
    s.set_defaults(func=goal_amend)
    s = sp.add_parser("goal-show"); s.add_argument("root"); s.set_defaults(func=goal_show)
    s = sp.add_parser("review-open")
    s.add_argument("root"); s.add_argument("--trigger", choices=TRIGGERS, required=True)
    s.add_argument("--proposal", default="")
    s.set_defaults(func=review_open)
    s = sp.add_parser("review-close")
    s.add_argument("root"); s.add_argument("id"); s.add_argument("--verdict", choices=ALL_VERDICTS, required=True)
    s.add_argument("--reviewer", choices=["self", "independent", "user"], required=True)
    s.add_argument("--evidence", action="append", required=True)
    s.add_argument("--alternative", required=True); s.add_argument("--remaining-cost", required=True)
    s.add_argument("--rationale", required=True); s.add_argument("--next-action", default="")
    s.set_defaults(func=review_close)
    s = sp.add_parser("review-resolve")
    s.add_argument("root"); s.add_argument("id"); s.add_argument("--resolution", required=True)
    s.add_argument("--evidence", action="append", required=True)
    s.add_argument("--user-quote", default="")
    s.set_defaults(func=review_resolve)
    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
