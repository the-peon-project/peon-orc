import json
import docker

install_path = "/app"
schedule_file="/home/peon/servers/schedule.json"

# Settings file
settings = json.load(open(f"{install_path}/config.json", 'r'))
# Container prefix
prefix = "peon.warcamp."
# Server list
global servers
servers = []
# Docker client file
client = docker.from_env()