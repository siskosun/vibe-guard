# Protection as areas mature

Use the smallest protection needed for the current maturity and consequence.

## Always, including exploration

- keep meaningful attempts recoverable;
- isolate disposable attempts when they may be thrown away;
- preserve already-established important behavior;
- close and remove abandoned attempts;
- never continue lasting work from superseded Product Intent;
- run Vibe Guard deterministic checks before calling an important step complete;
- keep the original task outcome separate from changing implementation plans;
- require fresh route review at important milestones, before consequential changes, and before release.

## Converging areas

Add:
- explicit Product Intent and non-goals;
- central impact links from Intent/Decision to affected areas;
- a repeatable check for any user journey that future attempts must preserve;
- cleanup before exploratory shortcuts become permanent.

## Production areas

Require:
- stable Product Intent supported by real evidence;
- at least one repeatable check of the main user journey or output;
- all applicable user-facing states exercised when they can occur;
- important Decisions linked to affected areas;
- no abandoned disposable work left behind;
- any project-specific safety checks appropriate to stored information, access, payment, or public use.

## User-facing state coverage

For an important user-facing area, record only states that can actually occur.

Examples:
- empty
- waiting
- failure
- partial completion

Evidence should cover each required state before a production area is considered complete.

## Rebuild vs clean existing attempt

Prefer rebuilding when:
- stable Intent and acceptance examples are sufficient to reproduce the accepted experience;
- exploratory implementation contains many shortcuts or rejected assumptions;
- understanding and cleaning the old attempt costs more than rebuilding it cleanly.

Prefer cleaning in place when:
- the structure is already simple;
- shortcuts are isolated;
- existing checks strongly protect behavior;
- rebuilding would create greater risk than cleanup.
