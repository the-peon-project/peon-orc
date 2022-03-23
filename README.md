# PEON - Orchestrator
## The Easy Game Server Manager

### [Peon Project](https://github.com/nox-noctua-consulting/peon)
An **OpenSource** project to assist gamers in self deploying/managing game servers.\
Intended to be a one-stop-shop for game server deployment/management.\
If run on a public/paid cloud, it is architected to try minimise costs (easy schedule/manage uptime vs downtime)\

### Peon Orchestrator (peon.orc)

This is the repo for developing the peon server orchestrator.

## State

> **EARLY DEVELOPMENT**

Completely useless at this point

## Version Info

### 0.1.3-dev
- Deployed with ``python:3.9-slim-bullseye`` as base image
- Using ``flask-restful`` as a framework to handle the API.
#### Known Bugs

### Architecture/Rules

Orchestrator (PeonOrc) built as a docker image for easy deployment.

### Feature Plan

#### *sprint 1.0.0*

- [ ] RESTapi
- [ ] Server deployment

#### *sprint 2.0.0*

- [ ] Persistent server data - Keep server data for updates & future releases.

#### *sprint 3.0.0*

- [ ] Backups

#### Notes
