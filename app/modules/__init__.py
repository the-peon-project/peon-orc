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
# Server list
global servers
servers = []
# Docker client file
client = docker.from_env()

def get_newest_version(version_local, version_remote):
    # split the version strings into their components
    version_local_components = [int(c) for c in version_local.split('.')]
    version_remote_components = [int(c) for c in version_remote.split('.')]
    # compare the major version component
    if version_local_components[0] < version_remote_components[0]:
        return "remote"
    elif version_local_components[0] > version_remote_components[0]:
        return "local"
    # compare the minor version component
    if version_local_components[1] < version_remote_components[1]:
        return "remote"
    elif version_local_components[1] > version_remote_components[1]:
        return "local"
    # compare the patch version component
    if version_local_components[2] < version_remote_components[2]:
        return "remote"
    elif version_local_components[2] > version_remote_components[2]:
        return "local"
    # the versions are equal
    return "same"