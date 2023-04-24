import json
import os
import docker
import logging

project_path = "/".join(((os.path.dirname(__file__)).split("/"))[:-1])
install_path = "/root/peon"
schedule_file=f"{install_path}/servers/schedule.json"

# Settings file
settings = json.load(open(f"{project_path}/config.json", 'r'))
# Container prefix
prefix = "peon.warcamp."
# Server list
global servers
servers = []
# Docker client file
client = docker.from_env()