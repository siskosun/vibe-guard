# Vibe Guard

A small, local-first skill for safely discovering and building software with nontechnical users. Version 2.2 adds original-goal anchoring and evidence-linked route review to the prior experiment/version protection rules.

## Why this exists

An agent can complete many subtasks while drifting away from the original user outcome. Vibe Guard records an original task-level goal separately from changing product hypotheses and asks a reviewer to judge actual artifacts against that goal. The deterministic gate requires a fresh review before milestone claims and release. It does not prove that a reviewer is independent or that a claimed test ran.

## Install

Use the standalone `skill.zip` artifact supplied with the release in ChatGPT's skill installation flow, or copy the `vibe-guard/` directory into the skill directory of a compatible agent environment. The skill is local-first and has no required remote service.

For project work, Python 3.10+ and Git are required for automatic save/restore and goal review. If the platform cannot run local scripts, follow the skill's manual procedure; do not pretend that automatic gates ran.

## Key behavior

- Save and restore exact versions while retaining learning records.
- Keep exploratory attempts disposable and separate from durable product code.
- Escalate protection per area as impact grows.
- Maintain the immutable original goal and explicit revisions.
- Open event-triggered route reviews without the builder's progress story.
- Block unfinished or stale reviews at milestone and release gates.
- Translate user-facing updates into everyday language.

## Agent-side command examples

These are internal commands for the developer/agent, not instructions a nontechnical user must execute.

```sh
python vibe-guard/scripts/workspace_guard.py doctor PROJECT
python vibe-guard/scripts/goal_guard.py goal-set PROJECT --outcome "Finish one useful main task" --success "An actual user finishes it" --non-goal "Do not build an account system"
python vibe-guard/scripts/goal_guard.py review-open PROJECT --trigger milestone --proposal "Ship main journey"
# Let a fresh reviewer inspect the artifact and gather real evidence.
python vibe-guard/scripts/goal_guard.py review-close PROJECT R-001 --verdict continue --reviewer self --evidence "Executed the main user flow" --alternative "Reuse the existing native widget" --remaining-cost "One manual check" --rationale "Observed end-to-end success"
python vibe-guard/scripts/check_gate.py PROJECT --phase milestone
```

At real-user release, open a new `--trigger release` review and run `--phase release`. `self` means a self-check and never counts as proof of independence.

See [route review procedure](vibe-guard/references/route-review.md) for triggers, stop conditions, and limitations.

## Test

```sh
python -m unittest discover -s tests -v
```

## Privacy and trust boundaries

Learning state is stored in the local Git common directory, outside checked-out project files. A local state log is not immutable against a malicious process with write access. Reviews and user-authorization quotes are self-reported; the gate binds them to the current Git workspace state but cannot attest the evidence. Use external permissions and independent tests for security-critical or irreversible operations.

## Changes in 2.2

- Added append-only original goal and user-directed revision events.
- Added proposed-route review inputs deliberately excluding the progress narrative.
- Added hold verdicts requiring documented correction and fresh re-review.
- Added milestone/release gates bound to current workspace and goal revision.
- Preserved existing v2 project-event replay and routine gate behavior.
