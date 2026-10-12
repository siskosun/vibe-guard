# Goal anchoring and route review (internal)

Use this when a long-running agent may mistake completed work for user value, or when a route becomes costly to reverse. This procedure adds to, rather than replaces, product-intent discovery and area-level protection.

## Keep three things distinct

1. **Original goal**: the user's desired outcome and provisional success tests, recorded once. Do not infer authorization to change it from implementation progress.
2. **Active goal revision**: an explicitly user-authorized change. Keep the exact user request and reason with the revision. A model-generated explanation is not authorization.
3. **Working product intent**: per-area hypotheses and stable intent. These may evolve inside the original outcome without rewriting the goal.

For an initially vague request, use the smallest honest, reversible success example as a *provisional* interpretation. Mark uncertain items in ordinary language, then present a concrete probe; do not invent a permanent specification. Correct a mistaken contract via `goal-amend` only after the user actually confirms a changed outcome. The script records the claimed quote but cannot verify who said it.

## Triggers

Always perform a route review:
- before expanding the accepted scope or making a difficult-to-reverse structural commitment;
- when the current method repeatedly fails or keeps requiring unrelated fixes;
- at meaningful milestones, before claiming success;
- before release to real users or production;
- when user feedback contradicts the current interpretation, and that contradiction may change the route.

For cheap, unambiguous text or visual changes, use routine checks only. Do not create a review after every edit or based on arbitrary time intervals.

## Independent inputs, not an independent-sounding narrative

Start `scripts/goal_guard.py review-open ROOT --trigger TRIGGER [--proposal NEXT_CHANGE]`. The output contains the original and active goal, the proposed next decision, and the observable workspace fingerprint. It deliberately omits the builder's previous plan, effort invested, percentage complete, and rationalizations.

When the environment can delegate, ask a different reviewer or a separate clean-context pass to judge this material. The reviewer should inspect the actual artifact and run or independently inspect relevant checks. Do not give the reviewer the builder's progress report first. When no independent pass is available, use `--reviewer self` and explicitly treat the conclusion as lower-confidence; recording `--reviewer independent` is not proof of independent evaluation.

Ask four questions:
1. What specific user-observable result now satisfies (or fails) each success criterion? Distinguish tested fact from agent assertion.
2. Ignoring time already spent, would the same route still be chosen today?
3. Is a smaller existing component, platform-native feature, or deletion enough to reach the goal?
4. Should the next action be continue, simplify, redirect, rollback, stop, or escalate?

A review that merely explains why existing work was useful is incomplete. Require at least one concrete alternative, including stopping when relevant, and an honest remaining-cost estimate. A simulated user is not user evidence.

## Recording the result

Call `scripts/goal_guard.py review-close ROOT REVIEW_ID --verdict VERDICT --reviewer self|independent|user --evidence TESTED_FACT --alternative FEASIBLE_ROUTE --remaining-cost COST --rationale WHY [--next-action ACTION]` while the workspace snapshot is unchanged. This checks that the review is tied to the artifact that was inspected, not whatever appears later.

For `continue`, the completion gate may pass on the identical workspace snapshot. For other verdicts, the deterministic gate stops further completion claims until corrective action is recorded and a fresh `continue` review examines the resulting state.

Resolve a held review using `review-resolve` only after actual changes or a new explicit user instruction. `stop` or `escalate` needs explicit user input to override; do not use an invented quote. A resolution alone is never a passing review.

After a goal revision, earlier passes are not passes for the new goal. Re-review the actual artifact against the new target.

## Deterministic gate

- `scripts/check_gate.py ROOT`: existing routine protections; also blocks any open or unresolved current-goal review.
- `scripts/check_gate.py ROOT --phase milestone`: require a goal and a passing review for the current workspace and current goal revision.
- `scripts/check_gate.py ROOT --phase release`: additionally require a passing review whose trigger is `release`.

The check is a **workflow integrity check**, not a proof that the product is useful or the review correct. It cannot force an agent to invoke a trigger; enforce true independent reviewer identity; verify user identity from a pasted quote; inspect ignored files; or determine whether a text evidence claim is true. For safety-sensitive or irreversible actions, use real permissions, approvals, and external tests rather than trusting a self-reported gate.

## Failure examples

- Completed 12 components but the main task still fails: choose `simplify` or `redirect`; added code is not progress toward outcome.
- A new architectural framework is proposed to solve one simple screen: review the native/smaller alternative **before** adoption.
- The user says the earlier minimal version was better: favor `rollback`, preserve the feedback, then validate the restored artifact.
- The developer tests pass but no intended user can finish the journey: do not claim success. Escalate the missing experience evidence or run a small real-use probe.
