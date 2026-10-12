---
name: vibe-guard
description: Help nontechnical users turn vague software or product ideas into something they actually want by trying small versions, reacting in ordinary language, learning from those reactions, safely returning to earlier versions, and gradually strengthening the parts that become important. Use when a user wants to build, change, prototype, or improve an app, game, website, automation, or other software without having clear requirements, or when repeated AI changes risk accumulating confusion, fragile behavior, abandoned experiments, or poor user experience. The user must never need technical knowledge or receive technical jargon during the workflow.
---

# Vibe Guard

## Non-negotiable user experience

The user must never need to understand software-development concepts, internal tool names, storage mechanisms, project history mechanisms, testing frameworks, file-structure concepts, or engineering vocabulary.

Never expose internal ids, command names, tool names, file paths, implementation labels, or technical error text unless another higher-priority instruction explicitly requires it.

All user-facing updates and final responses must use ordinary language. Describe only:
- what changed for the user;
- what was learned from their feedback;
- what was actually checked by trying it;
- what remains uncertain in terms they can judge;
- the next useful thing for them to look at or try.

When local execution is available, draft user-facing text and run `scripts/plain_feedback.py` before sending it. Rewrite until it passes. If local execution is unavailable, apply the same rule manually using `references/novice-ux.md`.

## Purpose

Let a user begin with a vague idea, see concrete attempts quickly, react with statements such as “this works,” “that does not,” “the earlier one was better,” or “I cannot explain it but this feels simpler,” and gradually discover the product they actually want.

The workflow must turn exploration into knowledge rather than permanent mess.

Optimize for:
1. learning cheaply before making expensive commitments;
2. keeping user feedback separate from agent interpretation;
3. preserving useful learning even when an attempted version is discarded;
4. making it easy to return to a previous version;
5. increasing protection automatically when a part becomes important;
6. periodically removing abandoned or unnecessary work;
7. rejecting apparently productive routes that no longer serve the original outcome.

## Preserve the original goal and independently challenge the route

Before the first meaningful implementation milestone, record one task-level goal contract with `scripts/goal_guard.py goal-set`: the outcome the user actually wants, at least one observable success example, meaningful non-goals, real constraints, and stop conditions. Keep the original contract immutable in learning history outside returnable product versions. Start from the user's actual request; treat missing details as reversible assumptions, not requirements the agent invented.

Product Intent may change with evidence, but implementation progress is **not** authorization to rewrite the task-level goal. Use `goal-amend` only for an actual user-directed change, preserving the original and recording the user's words. Never claim the script verified authorization.

At important milestones, and *before* scope expansion, expensive structural decisions, or repeating a failed approach, perform an event-triggered route review with `scripts/goal_guard.py review-open`. Prefer a separate reviewer or fresh context: give it the original goal, current artifact and measured checks, and the proposed next action; **do not preload the builder's progress story or sunk costs**. Ask whether a smaller existing solution, rollback, or stopping would better satisfy the outcome. A self-review must be recorded as self-review, not independent review.

A review may conclude `continue`, `simplify`, `redirect`, `rollback`, `stop`, or `escalate`. Record actual evidence, a concrete alternative, remaining cost, and next action via `review-close`. If it does not say `continue`, stop claiming milestone success. Correct the route, record how the hold was resolved, then perform a fresh review; do not silently resume the old path. Request user input only for a genuine goal change or a material irreversible trade-off.

Read `references/route-review.md` when performing any route review. The deterministic script protects against missing/stale reviews but cannot prove that the reviewer is independent, that a claimed test ran, or that the user's quoted approval is authentic. Do not substitute its success for real user validation.

## Bootstrap automatically

Before substantial work on a local project, run `scripts/workspace_guard.py doctor`.

If local save-and-return support is missing and the current environment permits local installation:
1. run `scripts/workspace_guard.py prepare --install`;
2. allow the operating system to request approval when required;
3. verify preparation succeeded;
4. initialize Vibe Guard state;
5. migrate v1 state with `scripts/migrate_v1.py` when present.

Do not ask the user to install or configure anything manually unless the environment prevents automatic preparation. Even then, explain only the plain consequence: “I need permission to prepare local save-and-return support before I can safely continue.”

Never change machine-wide settings when project-only settings are sufficient.

## Route each request by uncertainty and consequence

Use the smallest process that is safe.

### Simple, cheap, clear change

Examples: wording, obvious visual tweak, small local behavior.

Do it directly, try the affected flow, save the result, and report briefly. Do not start a discovery exercise.

### Unclear but cheap change

Make a disposable attempt quickly. Ask the user to react to something concrete instead of asking them to describe a complete specification.

### Clear but expensive-to-change choice

Record the intended user outcome and protect the important behavior before making the change.

### Unclear and expensive-to-change choice

Do not permanently bind the product to one interpretation. Create the smallest attempt that can teach something, keep it separate, gather feedback, then decide.

Typical expensive areas include long-lived saved information, important rules, access and payment behavior, shared behavior used by several parts of the product, and the main user journey.

## Discovery loop for vague requirements

Use this loop when the user does not yet know exactly what they want:

1. **Observe** — record what the user actually said or did, without interpreting it.
2. **Infer** — form one or more competing explanations of what might matter to them.
3. **Try** — create the cheapest concrete attempt that can distinguish those explanations.
4. **Let the user use it** — prefer doing a real task over asking for abstract opinions.
5. **Learn** — update, weaken, reject, or leave the explanations unresolved.
6. **Keep only the learning by default** — discard exploratory implementation unless it is already clean enough to belong in the lasting product.
7. Repeat until the desired experience becomes stable enough to protect.

Read `references/discovery-loop.md` for exact rules.

## Keep fact, interpretation, and stable intent separate

Internally maintain these distinct records with `scripts/guard_state.py`:

- Observation — what was actually said or observed.
- Preference hypothesis — a reversible interpretation of those observations.
- Probe — a disposable attempt designed to learn something.
- Product intent — a product principle supported by repeated evidence.
- Decision — an expensive implementation commitment made to serve stable intent.
- Evidence — concrete user behavior, user feedback, successful task completion, or an automated check.

Never turn one user comment directly into a permanent product rule.

Agent simulation may generate hypotheses. It may not, by itself, make product intent stable.

## Choose the next attempt for information, not polish

When several explanations fit the same feedback, do not simply choose the one the agent prefers.

Prefer the next attempt that:
- changes as little as practical;
- makes the competing explanations produce visibly different outcomes;
- is easy for the user to judge;
- requires little user attention;
- can be discarded cheaply.

Prefer two alternatives over many.

When alternatives necessarily change several things at once, mark the comparison internally as compound. The result may support “the user prefers this whole version,” but must not be treated as proof that one particular changed detail caused the preference.

Always allow the possibility that all current explanations are wrong.

If repeated attempts do not distinguish the explanations, choose the most reversible reasonable default, mark the question unresolved internally, and continue instead of exhausting the user.

## Save every version the user may compare

Before showing a meaningful new attempt to the user, save a named return point with `scripts/workspace_guard.py checkpoint` and attach a screenshot or other recognizable artifact when practical.

Use names the user can recognize, such as:
- “the version with one main action”;
- “the simpler home screen”;
- “before changing the project cards.”

If the user says “the earlier one was better,” restore the exact saved version with `scripts/workspace_guard.py restore`. Do not recreate it from memory.

Returning to earlier work must never erase newer learning from the user's later feedback.

## Isolate disposable attempts

Use `scripts/workspace_guard.py probe-start` for meaningful exploratory attempts when local execution is available.

Exploratory work has no automatic right to become lasting product work.

When an attempt ends:
- record what the user taught you;
- close it with `probe-finish`;
- remove the disposable workspace by default;
- keep only evidence, learning, and accepted product intent.

If the accepted experience can be rebuilt cleanly from stable intent and examples more easily than the exploratory implementation can be understood and cleaned, rebuild it cleanly.

## Increase protection by area, not by whole project

Different areas may mature at different speeds.

Internally track each relevant area as:
- explore;
- converging;
- production.

Raise protection automatically when an area begins to:
- preserve information the user cannot easily recreate;
- serve another real user;
- be made available outside the creator's own machine;
- control access;
- handle payment;
- provide behavior other parts now rely on;
- become intended for long-term use.

Use `scope-signal` for these events. Do not let an area remain permanently “experimental” merely to avoid stronger checks.

## Protect the user experience structure

Each stable product intent should state, in ordinary internal form:
- the user outcome;
- the core repeated action or journey when applicable;
- explicit non-goals;
- concrete examples of acceptable behavior.

Any lasting new feature must support an active product intent. If it does not, keep it as an experiment or omit it.

For important user-facing flows, explicitly cover every state that can actually occur, such as:
- nothing there yet;
- still waiting;
- something went wrong;
- only part of the action succeeded.

Do not require states that cannot occur.

Prefer one consistent set of visual patterns and interaction patterns over feature-by-feature invention.

## Keep cognition separate from returnable versions

Vibe Guard's learning history must live outside the part of the project that changes when returning to an earlier version.

Use the local project history area created by `workspace_guard.py`. Do not keep the authoritative learning history only in ordinary project files.

This guarantees:
- product versions can move backward;
- observations and learning continue forward;
- a discarded attempt can still teach the next attempt.

## Maintain impact links

When a product intent becomes stable or an expensive choice is recorded, map it to the parts of the project and checks that embody it using `mapping-set`.

Prefer central mappings. Add short source markers only when a local dependency would otherwise be difficult to discover.

When an intent is replaced, inspect every mapped area before continuing. Do not keep layering special cases on top of a product principle that is no longer true.

## Minimum protection exists from the first change

Exploration never means “anything goes.” From the first meaningful change:
- keep attempts recoverable;
- keep experiments separate when they may be discarded;
- preserve already-established important behavior;
- do not continue building on a rejected product principle;
- do not leave abandoned attempts mixed into lasting work;
- run deterministic guard checks with `scripts/check_gate.py` before calling an important step complete.

As an area matures, add stronger project-specific checks automatically.

Once an important user journey becomes something future attempts must preserve, add a repeatable way to walk that journey and check it after changes. Reuse the project's existing tools first.

## Consolidate instead of only adding

Trigger cleanup when any of these appear:
- the same rule is being implemented in several places;
- fixing one problem requires unrelated edits;
- special cases are accumulating to preserve old behavior;
- abandoned attempts remain;
- a rejected intent still has lasting implementation attached to it;
- the agent cannot explain the main user journey simply;
- changing one thing causes unpredictable changes elsewhere.

During cleanup:
1. add no optional new feature;
2. delete abandoned work first;
3. remove obsolete alternatives and special cases;
4. combine only concepts that are already truly the same;
5. simplify names and boundaries;
6. re-check the established user journeys afterward.

Do not optimize for a particular line count. Report growth/shrinkage internally only as a diagnostic signal.

## Use real evidence appropriately

Prefer evidence that directly answers the current question.

For experience questions, real user behavior while doing the task is stronger than an abstract preference statement when both are available.

Record whether evidence came from:
- the builder;
- an intended end user;
- directly observed behavior;
- an automated check;
- agent simulation.

Do not present agent simulation as user evidence.

## Context stays selective

Before working on an area, load only its relevant active intent, unresolved hypotheses, key observations, important examples, and lasting decisions using `guard_state.py context`.

Do not load the entire exploration history by default.

## Optional tools

Reuse what the project already has. Do not stack orchestration or governance products automatically.

Read `references/tool-routing.md` only when the existing project lacks a recurring capability that would materially improve safety or learning.

## Internal checks before user feedback

Before a meaningful completion or review request:
1. run the project's relevant checks;
2. open and finish a fresh route review at a meaningful milestone (`review-open --trigger milestone`), or before real-user release (`review-open --trigger release`);
3. run `scripts/check_gate.py ROOT --phase milestone` for meaningful milestone completion or `--phase release` before release; for low-risk routine edits use the default routine check;
4. save a recognizable return point when the user may compare versions;
5. prepare the user-facing message in plain language;
6. run `scripts/plain_feedback.py` on that message when local execution is available;
7. rewrite until no technical vocabulary is detected.

## User-facing message style

Use short ordinary statements. Good patterns:

- “我做了一个更简单的版本，你可以直接试。”
- “你刚才的反馈说明，我们之前可能把重点理解错了。我先不继续往那个方向加东西。”
- “我保留了你喜欢的那个版本，随时可以回去。”
- “这次尝试没有保留，但我已经记住了你不喜欢它的原因。”
- “我已经把主要流程实际走了一遍，没有发现刚才的问题。”
- “这里我还不确定你更在意哪一点，所以我做了两个只差一个关键地方的版本供你比较。”

Never say things like:
- “I created a branch/worktree.”
- “The commit passed CI.”
- “The API contract is stable.”
- “The schema migration succeeded.”
- “The dependency graph is clean.”

Read `references/novice-ux.md` for more examples and prohibited vocabulary.

## Resource map

- `scripts/workspace_guard.py` — automatically prepare local save/return support, save recognizable versions, restore exact earlier versions, and isolate disposable attempts.
- `scripts/goal_guard.py` — preserve original and revised goals, create fresh review inputs, and record route decisions against exact workspace states.
- `scripts/guard_state.py` — maintain observations, hypotheses, attempts, intent, decisions, evidence, area maturity, checkpoints, and impact links outside returnable project versions.
- `scripts/check_gate.py` — block contradictions, abandoned attempts, unsupported stable intent, missing protections in mature areas, and missing/stale route reviews.
- `scripts/migrate_v1.py` — preserve and import earlier Vibe Guard state without inventing missing meaning.
- `scripts/plain_feedback.py` — detect technical vocabulary before user-facing messages are sent.
- `references/discovery-loop.md` — detailed vague-requirement learning loop.
- `references/route-review.md` — event triggers, clean-context reviews, alternatives, holds, and evidence limits.
- `references/governance-model.md` — exact state semantics and escalation rules.
- `references/novice-ux.md` — strict user-language rules.
- `references/production-gates.md` — increasing protection as an area becomes important.
- `references/tool-routing.md` — optional reuse of existing project tools.
