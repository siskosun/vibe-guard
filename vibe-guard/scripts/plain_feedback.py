#!/usr/bin/env python3
"""Detect technical vocabulary in text intended for a nontechnical end user."""
from __future__ import annotations

import argparse
import json
import re
import sys

# Intentionally conservative. Internal text may use these words; user-facing text may not.
TERMS = [
    "git", "github", "gitlab", "repo", "repository", "worktree", "branch", "commit", "checkout", "reset", "merge", "rebase", "stash", "sha", "diff", "patch", "pull request", "pr",
    "cli", "shell", "terminal", "command line", "json", "yaml", "api", "schema", "migration", "lint", "typecheck", "unit test", "integration test", "e2e", "playwright", "storybook", "mcp", "framework", "dependency", "endpoint", "database", "state machine", "feature flag",
    "代码", "仓库", "分支", "提交", "合并", "回滚", "命令行", "终端", "脚本", "接口", "依赖", "模块", "架构", "数据库", "状态机", "功能开关", "配置", "部署", "编译", "构建", "日志", "协议", "补丁", "类型检查", "单元测试", "集成测试", "端到端测试", "版本控制",
]


def scan(text: str):
    lower = text.lower()
    hits = []
    for term in TERMS:
        t = term.lower()
        if re.fullmatch(r"[a-z0-9 ]+", t):
            pattern = r"(?<![a-z0-9_])" + re.escape(t) + r"(?![a-z0-9_])"
            if re.search(pattern, lower):
                hits.append(term)
        elif t in lower:
            hits.append(term)
    return sorted(set(hits), key=str.lower)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file", nargs="?")
    args = p.parse_args()
    if args.file:
        text = open(args.file, "r", encoding="utf-8").read()
    else:
        text = sys.stdin.read()
    hits = scan(text)
    print(json.dumps({"ok": not hits, "terms": hits}, ensure_ascii=False))
    if hits:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
