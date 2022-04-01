import json
import docker

# Server list
global servers
servers = []
# Docker client file
client = docker.from_env()
# Settings file
settings = json.load(open("./app/settings.json", 'r'))
# Container prefix
prefix = "peon.warcamp."