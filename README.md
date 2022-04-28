# PEON - Orchestrator

![André Kent - Artstation](https://cdna.artstation.com/p/assets/images/images/023/913/316/large/andre-kent-peon-turntable.jpg)

## The Easy Game Server Manager

### [Peon Project](https://github.com/nox-noctua-consulting/peon)

An **OpenSource** project to assist gamers in self-deploying/managing game servers.\
Intended to be a one-stop-shop for game server deployment/management.\
If run on a public/paid cloud, it is architected to try to minimise costs (easy schedule/manage uptime vs downtime)

### Peon Orchestrator (peon.orc)

The [github](https://github.com/nox-noctua-consulting/peon-orc/) repo for developing the peon server orchestrator.

## State

> **EARLY DEVELOPMENT**

Basic start/stop/restart/deploy/delete server functionality working

## Version Info

Check [changelog](https://github.com/nox-noctua-consulting/peon-orc/blob/master/changelog.md) for more information

- Deployed with ``python:3.9-slim-bullseye`` as a base image
- Using ``flask-restful`` as a framework to handle the API.
- Using ``docker-py`` for container management

### Known Bugs

- Non existent recipies work unexpectedly!??!

### Architecture/Rules

Orchestrator (PeonOrc) built as a docker image for easy deployment.

### Feature Plan

#### *sprint 0.1.0*

- [x] RESTapi (v1)
- [x] Server deployment (v1)

#### *sprint 0.2.0*

- [x] RESTapi (v1) - custom configurations
- [x] Server deployment (v2) - custom configurations
- [x] Persistent server data - Keep server data for updates & future releases.

#### *sprint 0.3.0*

- [x] RESTapi (v1) - Plan/recipies
- [ ] Backups

#### *sprint 0.4.0* 

- [ ] RESTapi (v1) - Console

#### Notes

[HTML Response Codes](https://www.restapitutorial.com/httpstatuscodes.html)

#### API

RESTful API

This API expects a JSON payload in most cases.

```yaml
url: {{peon_orchestrator_url}}:{{api_port}}/api/1.0/
    servers:
        - [GET] List all servers registered to Orchestrator
        - [POST] Create a new game server on orchestrator
    server:
        - [GET] Get a specific game server from the Orchestrator
        - [DEL] Delete a game server from the Orchestrator
        - [PUT] Update description or Start/Stop/Restart a game server on the Orchestrator
    plans:
        - [GET] List all plans on orchestrator
        - [PUT] Get latest plans list from PEON project
```

#### API Examples

##### Create server

```url
http://peon.za.cloudlet.cloud:5000/api/1.0/servers [POST]
```

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
        },
        {
            "type": "json",
            "name": "config.json",
            "content": {
                "somekey": "somevalue"
            }
        },
        {
            "type": "txt",
            "name": "textfile.txt",
            "content": "Some random text. With a \ttabspace & and a \nnewline."
        }
    ]
}
```
