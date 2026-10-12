# Vibe Guard v2 internal model

This file defines internal semantics. Never expose these names to a nontechnical user.

## Observation

A direct record of what happened: exact user feedback, observed behavior, or another concrete fact.

Never embed interpretation in the observation when it can be separated.

## Preference hypothesis

A falsifiable interpretation of observations.

Statuses:
- open
- supported
- weakened
- rejected
- defaulted

`defaulted` means the uncertainty was not resolved, but the workflow chose a reversible working assumption so progress could continue.

## Probe

A disposable attempt whose primary purpose is learning.

Fields should identify:
- question being tested;
- relevant hypotheses;
- variants;
- scope;
- whether the comparison is single-factor or compound;
- the baseline checkpoint;
- its isolated workspace when available.

Probe code has no inheritance right.

## Product intent

A stable or provisional product principle about user outcome, core loop, non-goals, and concrete acceptance examples.

Statuses:
- provisional
- stable
- superseded

Stable intent requires real evidence. Agent simulation cannot be the only evidence.

Never rewrite history when intent changes. Supersede the old intent.

## Decision

A durable, expensive-to-reverse implementation commitment made to serve active Product Intent.

An active Decision must cite active Intent and identify affected areas. If its Intent is superseded, the Decision becomes blocking until reviewed or superseded.

## Evidence

Evidence has both an actor and a mode.

Actors:
- builder
- target_user
- agent_simulation
- system

Modes:
- stated_preference
- observed_behavior
- task_completion
- automated_check
- calibration_example

Evidence strength depends on the claim. Do not use a lower-level signal to prove a higher-level experience claim.

## Scope maturity

Track maturity by area, not whole project.

- explore: change is still being learned;
- converging: intent is becoming stable and other work may begin depending on it;
- production: behavior is meant to persist and must be protected.

Automatic minimum maturity signals:
- retained data -> production
- another real user -> production
- public availability -> production
- access control -> production
- payment -> production
- shared boundary -> converging
- depended on by other areas -> converging
- intended long-term use -> converging

## Impact links

Stable Intent and active Decisions should map centrally to the paths and checks that embody them.

Use source comments only where central mapping cannot make the relationship discoverable.

## Cognition history

The learning history is append-only and stored outside ordinary returnable project files.

Code may move backward. Cognition history must not.

## Goal contract and route review

Task-level original goal stays immutable; active revisions require a direct user request, not an agent-created inference. Goal revisions live with the append-only learning history, not code snapshots.

Route reviews are separate from product intent and observation records. Review inputs do not carry execution progress narratives. Their workspace fingerprint and goal version prevent stale reviews from passing completion gates. A held verdict requires resolution plus fresh review. Review identity, source truthfulness, and user quotes are declared facts, not cryptographically verified.
