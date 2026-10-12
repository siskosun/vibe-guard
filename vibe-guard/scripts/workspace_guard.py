#!/usr/bin/env python3
"""Local project snapshots and disposable workspaces for Vibe Guard v2.

Agent-facing only. It uses local Git as an implementation detail but exposes only
structured results so the skill can describe outcomes without technical vocabulary.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from vg_common import (
    append_event,
    artifacts_dir,
    command_exists,
    events_path,
    git_available,
    git_common_dir,
    json_print,
    load_state,
    next_id,
    platform_name,
    repo_root,
    run,
    workspace_home,
)

LOCAL_NAME = "Vibe Guard Local"
LOCAL_EMAIL = "vibe-guard@local.invalid"
SECRET_PATTERNS = [
    ".vibe-guard/",
    ".env",
    ".env.local",
    ".env.*.local",
    "*.pem",
    "*.key",
    "*credentials*.json",
    "*secret*.json",
    "*secrets*.json",
]


def result(code: str, **kwargs: Any) -> None:
    json_print({"code": code, **kwargs})


def refresh_git_path() -> None:
    if git_available():
        return
    candidates = []
    if os.name == "nt":
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        candidates += [Path(pf) / "Git" / "cmd", Path(pf86) / "Git" / "cmd"]
    for p in candidates:
        if (p / ("git.exe" if os.name == "nt" else "git")).exists():
            os.environ["PATH"] = str(p) + os.pathsep + os.environ.get("PATH", "")
            break


def install_git() -> dict[str, Any]:
    system = platform_name()
    if git_available():
        return {"installed": True, "already_present": True}
    if system == "windows":
        if command_exists("winget"):
            p = run([
                "winget", "install", "--id", "Git.Git", "-e", "--source", "winget",
                "--accept-package-agreements", "--accept-source-agreements", "--silent",
            ], check=False)
            refresh_git_path()
            return {"installed": git_available(), "method": "winget", "returncode": p.returncode, "restart_needed": not git_available()}
        if command_exists("choco"):
            p = run(["choco", "install", "git", "-y"], check=False)
            refresh_git_path()
            return {"installed": git_available(), "method": "choco", "returncode": p.returncode, "restart_needed": not git_available()}
        if command_exists("scoop"):
            p = run(["scoop", "install", "git"], check=False)
            refresh_git_path()
            return {"installed": git_available(), "method": "scoop", "returncode": p.returncode, "restart_needed": not git_available()}
        return {"installed": False, "reason": "NO_SUPPORTED_INSTALLER"}
    if system == "macos":
        if command_exists("brew"):
            p = run(["brew", "install", "git"], check=False)
            return {"installed": git_available(), "method": "brew", "returncode": p.returncode}
        return {"installed": False, "reason": "USER_APPROVAL_REQUIRED"}
    if system == "linux":
        prefix: list[str] = []
        try:
            is_root = os.geteuid() == 0
        except AttributeError:
            is_root = False
        if not is_root and command_exists("sudo"):
            prefix = ["sudo"]
        choices = [
            ("apt-get", ["apt-get", "update"], ["apt-get", "install", "-y", "git"]),
            ("dnf", None, ["dnf", "install", "-y", "git"]),
            ("yum", None, ["yum", "install", "-y", "git"]),
            ("pacman", None, ["pacman", "-Sy", "--noconfirm", "git"]),
            ("zypper", None, ["zypper", "--non-interactive", "install", "git"]),
        ]
        for exe, pre, install in choices:
            if command_exists(exe):
                if pre:
                    run(prefix + pre, check=False)
                p = run(prefix + install, check=False)
                return {"installed": git_available(), "method": exe, "returncode": p.returncode}
        return {"installed": False, "reason": "NO_SUPPORTED_INSTALLER"}
    return {"installed": False, "reason": "UNSUPPORTED_SYSTEM", "system": system}


def local_config(root: Path) -> None:
    name = run(["git", "-C", str(root), "config", "--local", "--get", "user.name"], check=False)
    email = run(["git", "-C", str(root), "config", "--local", "--get", "user.email"], check=False)
    if name.returncode != 0 or not name.stdout.strip():
        run(["git", "-C", str(root), "config", "--local", "user.name", LOCAL_NAME])
    if email.returncode != 0 or not email.stdout.strip():
        run(["git", "-C", str(root), "config", "--local", "user.email", LOCAL_EMAIL])


def ensure_local_excludes(root: Path) -> None:
    common = git_common_dir(root)
    exclude = common / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    marker = "# vibe-guard local protection"
    if marker in existing:
        return
    block = marker + "\n" + "\n".join(SECRET_PATTERNS) + "\n"
    with exclude.open("a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write(block)


def prepare(root_arg: str, allow_install: bool) -> dict[str, Any]:
    root = Path(root_arg).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not git_available():
        if not allow_install:
            return {"ready": False, "reason": "LOCAL_HISTORY_TOOL_MISSING"}
        installed = install_git()
        if not installed.get("installed"):
            return {"ready": False, "reason": installed.get("reason", "INSTALL_DID_NOT_FINISH"), "install": installed}
    out = run(["git", "-C", str(root), "rev-parse", "--show-toplevel"], check=False)
    created = False
    if out.returncode != 0:
        init = run(["git", "init", "-b", "main", str(root)], check=False)
        if init.returncode != 0:
            run(["git", "init", str(root)])
        created = True
    rr = repo_root(root)
    local_config(rr)
    ensure_local_excludes(rr)
    if not events_path(rr).exists():
        append_event(rr, "init", {"version": 2, "note": "vibe-guard-v2"})
    head = run(["git", "-C", str(rr), "rev-parse", "HEAD"], check=False)
    if head.returncode != 0:
        run(["git", "-C", str(rr), "commit", "--allow-empty", "-m", "vibe-guard: starting point"])
    return {"ready": True, "created": created, "root": str(rr)}


def cmd_doctor(a: argparse.Namespace) -> None:
    root = Path(a.root).resolve()
    info: dict[str, Any] = {"system": platform_name(), "root": str(root), "local_history_ready": git_available()}
    if git_available():
        ver = run(["git", "--version"], check=False)
        info["version"] = ver.stdout.strip() if ver.returncode == 0 else ""
        repo = run(["git", "-C", str(root), "rev-parse", "--show-toplevel"], check=False)
        info["project_ready"] = repo.returncode == 0
        if repo.returncode == 0:
            info["project_root"] = repo.stdout.strip()
            try:
                info["state_ready"] = events_path(root).exists()
            except Exception:
                info["state_ready"] = False
    result("OK", **info)


def cmd_prepare(a: argparse.Namespace) -> None:
    payload = prepare(a.root, a.install)
    result("READY" if payload.get("ready") else "NEEDS_ACTION", **payload)


def protect_sensitive_untracked(rr: Path) -> list[str]:
    out = run(["git", "-C", str(rr), "ls-files", "--others", "--exclude-standard"], check=False)
    if out.returncode != 0:
        return []
    protected: list[str] = []
    suspicious_names = {".env", ".env.local"}
    for raw in out.stdout.splitlines():
        rel = raw.strip().replace("\\", "/")
        if not rel:
            continue
        name = Path(rel).name.lower()
        suspicious = (
            name in suspicious_names
            or name.endswith(".pem")
            or name.endswith(".key")
            or ("credential" in name and name.endswith(".json"))
            or ("secret" in name and name.endswith(".json"))
        )
        if suspicious:
            protected.append(rel)
    if protected:
        common = git_common_dir(rr)
        exclude = common / "info" / "exclude"
        with exclude.open("a", encoding="utf-8") as f:
            for rel in protected:
                f.write("/" + rel + "\n")
    return protected


def create_checkpoint(root: str, label: str, note: str = "", artifacts: list[str] | None = None, probe: str | None = None) -> dict[str, Any]:
    prep = prepare(root, allow_install=False)
    if not prep.get("ready"):
        raise RuntimeError(json.dumps(prep, ensure_ascii=False))
    rr = repo_root(root)
    protected = protect_sensitive_untracked(rr)
    run(["git", "-C", str(rr), "add", "-A"])
    changed = run(["git", "-C", str(rr), "status", "--porcelain"], check=False).stdout.strip()
    if changed:
        run(["git", "-C", str(rr), "commit", "-m", "vibe-guard: saved point"])
    head = run(["git", "-C", str(rr), "rev-parse", "HEAD"]).stdout.strip()
    state = load_state(rr)
    ident = next_id(state, "checkpoints", "C")
    run(["git", "-C", str(rr), "update-ref", f"refs/vibe-guard/checkpoints/{ident}", head])
    copied: list[str] = []
    for raw in artifacts or []:
        src = Path(raw).resolve()
        if src.exists() and src.is_file():
            dest_dir = artifacts_dir(rr) / ident
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name
            shutil.copy2(src, dest)
            copied.append(str(dest))
    append_event(rr, "checkpoint_added", {
        "id": ident,
        "label": label,
        "commit": head,
        "note": note,
        "artifacts": copied,
        "probe": probe,
    })
    return {"id": ident, "label": label, "commit": head, "protected_local_files": protected, "artifacts": copied}


def cmd_checkpoint(a: argparse.Namespace) -> None:
    result("SAVED", **create_checkpoint(a.root, a.label, a.note, a.artifact, a.probe or None))


def cmd_list(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    rows = []
    for item in state["checkpoints"].values():
        rows.append({"id": item["id"], "label": item["label"], "note": item.get("note", ""), "probe": item.get("probe"), "at": item.get("at")})
    result("OK", checkpoints=rows)


def cmd_restore(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    target = state["checkpoints"].get(a.id)
    if not target:
        result("NOT_FOUND", id=a.id)
        raise SystemExit(2)
    safety = create_checkpoint(a.root, "automatic safety copy before returning", "created automatically before returning to an earlier version")
    rr = repo_root(a.root)
    run(["git", "-C", str(rr), "reset", "--hard", target["commit"]])
    result("RETURNED", target=a.id, safety=safety["id"], label=target["label"])


def cmd_compare(a: argparse.Namespace) -> None:
    state = load_state(a.root)
    left = state["checkpoints"].get(a.left)
    right = state["checkpoints"].get(a.right)
    if not left or not right:
        result("NOT_FOUND", left=bool(left), right=bool(right))
        raise SystemExit(2)
    rr = repo_root(a.root)
    stat = run(["git", "-C", str(rr), "diff", "--stat", left["commit"], right["commit"]], check=False).stdout
    names = run(["git", "-C", str(rr), "diff", "--name-status", left["commit"], right["commit"]], check=False).stdout
    result("OK", left=a.left, right=a.right, stat=stat, files=names.splitlines())


def cmd_probe_start(a: argparse.Namespace) -> None:
    rr = repo_root(a.root)
    baseline = create_checkpoint(str(rr), "before trying " + a.label, a.question)
    state = load_state(rr)
    ident = next_id(state, "probes", "P")
    branch = f"vibe-guard/probe/{ident}"
    work = workspace_home(rr) / ident
    if work.exists():
        shutil.rmtree(work)
    run(["git", "-C", str(rr), "worktree", "add", "-b", branch, str(work), baseline["commit"]])
    append_event(rr, "probe_added", {
        "id": ident,
        "question": a.question,
        "scope": a.scope or None,
        "hypotheses": a.hypothesis,
        "variants": a.variant,
        "comparison": a.comparison,
        "status": "active",
        "disposable": True,
        "workspace": str(work),
        "branch": branch,
        "baseline_checkpoint": baseline["id"],
        "label": a.label,
    })
    result("TRY_READY", id=ident, workspace=str(work), baseline=baseline["id"], label=a.label)


def cmd_probe_finish(a: argparse.Namespace) -> None:
    rr = repo_root(a.root)
    state = load_state(rr)
    probe = state["probes"].get(a.id)
    if not probe:
        result("NOT_FOUND", id=a.id)
        raise SystemExit(2)
    append_event(rr, "probe_status", {"id": a.id, "status": a.status, "result": a.result or ""})
    removed = False
    if not a.keep_workspace and probe.get("workspace"):
        run(["git", "-C", str(rr), "worktree", "remove", "--force", probe["workspace"]], check=False)
        if probe.get("branch"):
            run(["git", "-C", str(rr), "branch", "-D", probe["branch"]], check=False)
        removed = True
    result("TRY_CLOSED", id=a.id, removed=removed, status=a.status)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Vibe Guard local workspace internals")
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("doctor"); s.add_argument("root"); s.set_defaults(func=cmd_doctor)
    s = sp.add_parser("prepare"); s.add_argument("root"); s.add_argument("--install", action="store_true"); s.set_defaults(func=cmd_prepare)
    s = sp.add_parser("checkpoint"); s.add_argument("root"); s.add_argument("--label", required=True); s.add_argument("--note", default=""); s.add_argument("--artifact", action="append", default=[]); s.add_argument("--probe", default=""); s.set_defaults(func=cmd_checkpoint)
    s = sp.add_parser("list"); s.add_argument("root"); s.set_defaults(func=cmd_list)
    s = sp.add_parser("restore"); s.add_argument("root"); s.add_argument("id"); s.set_defaults(func=cmd_restore)
    s = sp.add_parser("compare"); s.add_argument("root"); s.add_argument("left"); s.add_argument("right"); s.set_defaults(func=cmd_compare)
    s = sp.add_parser("probe-start"); s.add_argument("root"); s.add_argument("--label", required=True); s.add_argument("--question", required=True); s.add_argument("--scope", default=""); s.add_argument("--hypothesis", action="append", default=[]); s.add_argument("--variant", action="append", default=[]); s.add_argument("--comparison", choices=["single_factor", "compound"], default="single_factor"); s.set_defaults(func=cmd_probe_start)
    s = sp.add_parser("probe-finish"); s.add_argument("root"); s.add_argument("id"); s.add_argument("--status", choices=["accepted", "rejected", "closed"], required=True); s.add_argument("--result", default=""); s.add_argument("--keep-workspace", action="store_true"); s.set_defaults(func=cmd_probe_finish)
    return p


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except RuntimeError as exc:
        try:
            payload = json.loads(str(exc))
        except json.JSONDecodeError:
            payload = {"detail": str(exc)}
        result("FAILED", **payload)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
