> **⚠️ DEPRECATED — moved to the `peon` monorepo.** This repo's content now lives at
> `peon/services/orc` (full history preserved via `git subtree`). See
> `/home/richard/development/peon/services/orc/CLAUDE.md` for the current guide. This repo is
> archived and read-only.

---

# PEON Orchestrator Guide

This repo owns the core PEON orchestration API. It is the control plane that other services depend on.

## Scope

- Flask API entrypoint: `app/main.py`
- API resources: `app/modules/api_v1.py`
- Server lifecycle logic: `app/modules/servers.py`
- Scheduler logic: `app/modules/scheduler.py`
- Plan ingestion and updates: `app/modules/plans.py`

## Runtime Map

- Language/runtime: Python + Flask + Flask-RESTful
- Main port: `5000`
- Main startup: `python3 app/main.py`
- Dependencies are defined in `requirements.txt`

## Working Rules

1. Start from the API resource or module that actually computes the behavior, not just the Flask registration.
2. Keep authorization checks intact when changing endpoints.
3. Treat Docker, filesystem, and scheduler interactions as operationally sensitive; prefer non-destructive validation.
4. If endpoint payloads change, review likely consumers in `peon-webui/`, `peon-bot-discord/`, and `peon-cli/`.
5. If server-management semantics change, update `peon-docs/` source docs.

## Commands

```bash
cd /home/richard/development/peon-orc
python3 -m pip install -r requirements.txt
python3 app/main.py
```

## Safe Validation

```bash
cd /home/richard/development/peon-orc
python3 -m py_compile app/main.py
```

Use targeted syntax checks or module-level verification around touched files when possible. There is no obvious committed narrow automated test suite in this repo.

## Important Files

- Startup: `app/main.py`
- API resources: `app/modules/api_v1.py`
- Shared helpers: `app/modules/shared.py`
- Security checks: `app/modules/security.py`
- Server operations: `app/modules/servers.py`
- Scheduler: `app/modules/scheduler.py`
- Plans integration: `app/modules/plans.py`
- Repo dependencies: `requirements.txt`

## Cross-Repo Dependencies

- `peon-webui` depends on this API for orchestrator and server control
- `peon-bot-discord` depends on this API for Discord command behavior
- `peon-cli` often mirrors operational actions against the PEON stack
- `peon-warplans` defines the recipes this repo consumes
- `peon-wartable` defines relevant runtime images used by plans

## Safety Notes

- Avoid broad live-container operations as a first validation step.
- Changes to create, destroy, update, or scheduler flows can mutate real server state.
- Prefer syntax checks, focused reads, and clearly scoped local validation before any runtime action.

## Default Workflow

1. Find the owning module under `app/modules/`.
2. Read the endpoint and the underlying helper that mutates state.
3. Make the smallest change that fixes the root cause.
4. Run a narrow syntax or startup validation.
5. Check whether downstream consumers or docs need updates.