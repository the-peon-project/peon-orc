# PEON - Orchestrator

[![Docker Pulls](https://img.shields.io/docker/pulls/umlatt/peon.orc.svg)](https://hub.docker.com/r/umlatt/peon.orc)
[![Docker Stars](https://img.shields.io/docker/stars/umlatt/peon.orc.svg)](https://hub.docker.com/r/umlatt/peon.orc)

## The Easy Game Server Manager

### Installation

> Please find the installation instructions at [PEON](https://github.com/the-peon-project/peon/) master project, as there are several dependencies that are required for this module to work correctly.

### [Peon Project](https://github.com/the-peon-project/peon)

An **OpenSource** project to assist gamers in self-deploying/managing game servers.\
Intended to be a one-stop-shop for game server deployment/management.\
If run on a public/paid cloud, it is architected to try to minimise costs (easy schedule/manage uptime vs downtime)

### Peon Orchestrator (peon.orc)

The [github](https://github.com/the-peon-project/peon-orc/) repo for developing the peon server orchestrator.

## State

> **EARLY DEVELOPMENT**

Basic start/stop/restart/deploy/delete server functionality working

## Version Info

Check [changelog](https://github.com/the-peon-project/peon-orc/blob/master/changelog.md) for more information

- Deployed with ``python:3.9-slim-bullseye`` as a base image
- Using ``flask-restful`` as a framework to handle the API.
- Using ``docker-py`` for container management

### Known Bugs

- ?

## Architecture/Rules

Orchestrator (PeonOrc) built as a docker image for easy deployment.

## Feature Plan

### *sprint 0.1.0*

- [x] RESTapi (v1)
- [x] Server deployment (v1)

### *sprint 0.2.0*

- [x] RESTapi (v1) - custom configurations
- [x] Server deployment (v2) - custom configurations
- [x] Persistent server data - Keep server data for updates & future releases.

### *sprint 0.3.0*

- [x] RESTapi (v1) - Plan/recipies
- [x] Security - api-key integration
- [x] Start/Stop scheduler
- [ ] Backups
  
### *sprint 0.4.0*

- [ ] RESTapi (v1) - Console
- [ ] Security - Users & Audit Loggin

### Notes

[HTML Response Codes](https://www.restapitutorial.com/httpstatuscodes.html)

### API

RESTful API

Authorization - ``Api-Key``

API-KEY ``my-super-secret-api-key``
> Hard coded as user control is not yet implemented

This API expects a JSON payload in most cases.

[API Docs](http://api.peon.noxnoctua.com/)

```yaml
url: {{peon_orchestrator_url}}:{{api_port}}/api/1.0/
    servers:
        - [GET] List all servers registered to Orchestrator
        - [POST] Create a new game server on orchestrator
        
    server/get/GAME_UID.SERVERNAME:
        - [GET] Get details of a game server
    server/stats/GAME_UID.SERVERNAME:
        - [GET] Get details of a game server, with performance statistics
    server/start/GAME_UID.SERVERNAME:
        - [PUT] Start a specific game server from the Orchestrator
    server/stop/GAME_UID.SERVERNAME:
        - [PUT] Stop a specific game server from the Orchestrator
    server/restart/GAME_UID.SERVERNAME:
        - [PUT] Restart a specific game server from the Orchestrator
    server/description/GAME_UID.SERVERNAME:
        - [PUT] Update the description of a specific game server from the Orchestrator
    server/destroy/GAME_UID.SERVERNAME:
        - [DEL] Removes a game container leaving server and config files intact (optional flag to delete all files as well)
        body: { "eradicate" : "True" } *Optional (destructive data removal)
    server/eradicate/GAME_UID.SERVERNAME:
        - [DEL] Deletes all game data & config files
        body: { "eradicate" : "True" } *Required

    plans:
        - [GET] List all plans on orchestrator
        - [PUT] Get latest plans list from PEON project
```

#### API Examples

##### Create server

###### Example [Valhiem Server]

URL [REST] - ``POST``

```url
http://peon.za.cloudlet.cloud:5000/api/1.0/servers [POST]
```

HEADERS

```json
{ "X-Api-Key" : "my-super-secret-api-key" }
```

Payload [BODY] - ``JSON``

```json
{
    "game_uid": "valhiem",
    "servername": "server01",
    "description": "A valhiem PEON server",
    "settings": [{
            "type": "env",
            "name": "container environment",
            "content": {
                "SERVERNAME": "My-Valhiem-Server",
                "WORLDNAME": "awesomeworld",
                "PASSWORD": "password123"
            }
        }
    ]
}
```

## Support the Project

PEON is an open-source project that I am working on in my spare time (for fun).
However, if you still wish to say thanks, feel free to pick up a virtual coffee for me at Ko-fi.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/K3K567ILJ)
