# Agent Discovery Workflow

Use an exploratory subagent when available to reduce bias from built-in detectors and inspect unfamiliar repositories with fresh context.

## Goal

Ask the subagent to identify the project's observable contracts, technology stack, persistence/state mechanisms, architecture shape, and high-risk paths without assuming a specific framework or delivery style.

## Suggested Prompt

> Inspect this repository as an unfamiliar software project. Report the technology stack, observable contracts, entry points, persistence/state mechanisms, architecture shape, and any risky or unusual code paths with file-level evidence. Do not assume the project is an HTTP API or that the relevant layers are named model/view/controller. Return a concise inventory plus the top risks you observed.

## What To Ask For

- Stack and runtime candidates, including unknowns.
- External interfaces and contracts.
- Entry points and startup flow.
- Persistence/state mechanisms.
- Architecture and responsibility boundaries.
- Unusual dependencies, lifecycle issues, and likely risk areas.

## How To Use The Result

1. Treat the agent output as the primary discovery pass.
2. Cross-check it against manifests, imports, and representative files.
3. Use `scripts/project_inventory.py` only as a fallback or normalization helper when it adds value.
4. Keep the final analysis evidence-based; do not copy unverified assumptions from the agent.
