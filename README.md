# PEON - Orchestrator

## The Easy Game Server Manager

### [Peon Project](https://github.com/nox-noctua-consulting/peon)

An **OpenSource** project to assist gamers in self deploying/managing game servers.\
Intended to be a one-stop-shop for game server deployment/management.\
If run on a public/paid cloud, it is architected to try minimise costs (easy schedule/manage uptime vs downtime)

### Peon Orchestrator (peon.orc)

The [github](https://github.com/nox-noctua-consulting/peon-orc/) repo for developing the peon server orchestrator.

## State

> **EARLY DEVELOPMENT**

Basic start/stop/restart/deploy/delete server functionality working

## Version Info

Check [changelog](https://github.com/nox-noctua-consulting/peon-orc/blob/master/changelog.md) for more information

- Deployed with ``python:3.9-slim-bullseye`` as base image
- Using ``flask-restful`` as a framework to handle the API.
- Using ``docker-py`` for container management

### Known Bugs

-

### Architecture/Rules

Orchestrator (PeonOrc) built as a docker image for easy deployment.

### Feature Plan

#### *sprint 0.1.0*

- [x] RESTapi (v1)
- [x] Server deployment (v1)

#### *sprint 0.2.0*

- [ ] RESTapi (v2) - custom configurations
- [ ] Server deployment (v2) - custom configurations

#### *sprint 0.3.0*

- [ ] Persistent server data - Keep server data for updates & future releases.
- [ ] Backups

#### Notes

[HTML Response Codes](https://www.restapitutorial.com/httpstatuscodes.html)
