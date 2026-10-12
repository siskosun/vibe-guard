# Optional internal tool routing

This reference is internal. Never surface these tool names to a nontechnical user.

Use existing project capabilities first. Add another dependency only when it prevents a recurring failure that cannot be handled cheaply with the current project.

## Local save/return and disposable attempts

Use local Git through `workspace_guard.py` as the default implementation detail. GitHub or any remote service is optional and must never be a core requirement.

Do not require the user to create an account or connect a remote service for single-person local use.

## Browser-visible journeys

If the project already uses Playwright or equivalent browser automation, reuse it for repeatable main-flow checks and important user-facing states.

Do not add it merely for a one-off disposable visual attempt unless real interaction is the thing being learned.

## Component consistency

Use Storybook or an existing component preview system only when the project already has recurring component/state work that benefits from it.

## API or service boundaries

Use existing integration/contract checks first. Consider Schemathesis or Pact only when service boundaries are real and recurring.

## Structural drift

For JS/TS projects, dependency-cruiser may be useful when import/boundary drift repeatedly causes real problems.

## Cleanup

Use Knip for dead JS/TS files/exports/dependencies and jscpd for repeated code only during consolidation when those problems actually exist.

Do not optimize tool scores. Use findings to decide what can be deleted or simplified.

## Rich governance systems

Grove, OpenSpec, Spec Kit, Beads, adr-kit, and similar systems may be useful in large long-running efforts, but Vibe Guard v2 must not depend on them.

Adopt one only when its recurring value is clear and its additional vocabulary will remain hidden from the nontechnical user.
