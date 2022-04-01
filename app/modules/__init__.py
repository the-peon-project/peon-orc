import json
import docker

global servers
servers = []
client = docker.from_env()
settings = json.load(open("settings.json", 'r'))