# Discovery loop for vague intent

Use this reference when the user cannot state a complete requirement and needs to discover it by reacting to concrete attempts.

## The loop

1. Record the user's actual words or observed behavior as an Observation.
2. Generate the smallest plausible set of competing preference hypotheses. Usually 1-3 is enough.
3. Include an implicit “none of these” possibility.
4. Decide whether the uncertainty matters now. If not, choose a reversible default and continue.
5. If it matters, design the cheapest Probe that makes the hypotheses predict different user reactions.
6. Prefer one controlled difference. If that is impossible, mark the Probe as compound and avoid single-factor causal claims.
7. Save the version before showing it to the user.
8. Let the user do a real task when possible. Observe hesitation, wrong turns, recovery, and completion rather than relying only on abstract preference.
9. Record the new Observation and Evidence.
10. Update hypotheses: supported, weakened, rejected, or unresolved/defaulted.
11. Promote a Product Intent only after evidence repeats or competing explanations are materially reduced.
12. Discard Probe implementation by default.

## Feedback interpretation

Treat statements literally first.

User: “Too much information.”

Observation:
- user said there is too much information on this screen.

Possible hypotheses:
- overall information quantity is too high;
- information hierarchy is weak;
- the next action is unclear, making all information feel equally demanding.

Do not silently select one.

## Choosing the next Probe

Prefer the Probe that maximizes practical information gained per unit of user attention.

A strong Probe:
- is quick to make;
- is quick to judge;
- changes only what is necessary;
- creates meaningfully different predictions;
- is easy to throw away.

Use two variants by default. More variants require a clear reason.

If the user cannot distinguish after repeated attempts, choose the most reversible reasonable option, mark the hypothesis defaulted/unresolved, and continue.

## Calibration examples

When the user explicitly likes a concrete version, screenshot, wording, or interaction, store it as Evidence with mode `calibration_example`.

Use calibration examples later to interpret fuzzy terms such as “simple,” “clean,” “clear,” or “like the earlier version.”

Do not turn a calibration example into a universal rule outside its relevant scope without further evidence.
