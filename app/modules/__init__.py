import json
import os
import docker
import logging

project_path = "/".join(((os.path.dirname(__file__)).split("/"))[:-1])
install_path = "/root/peon"
schedule_file=f"{install_path}/servers/schedule.json"

# Settings file
settings = json.load(open(f"{project_path}/settings.json", 'r'))
# Container prefix
prefix = "peon.warcamp."

def dev_mode():
    if os.path.isdir(f"{project_path}/dev"):
        logging.warn("DEV MODE ENABLED")
        return True
    else:
        return False

# Server list
global servers
servers = []
# Docker client file
client = docker.from_env()