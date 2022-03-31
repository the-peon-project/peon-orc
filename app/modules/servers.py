#!/usr/bin/python3
import logging
import docker


global servers
servers = []

prefix = "peon.warcamp."

def servers_reload_current():
    client = docker.from_env()
    containers = client.containers.list(all)
    game_servers = []
    for game_server in containers:
        if prefix in game_server.name:
            game_servers.append(game_server)
    for indx,game_server in enumerate(game_servers):
        server_full_uid = (game_server.name).split('.')
        server = {
                'id' : indx + 1,
                'game_uid' : server_full_uid[2],
                'servername' : server_full_uid[3],
                'password' : "**********",
                'state' : game_server.status
        }
        servers.append(server)

def server_start(server_uid):
    logging.info("Starting server [{0}]".format(server_uid))
    client = docker.from_env()
    container = client.containers.get("{0}{1}".format(prefix,server_uid))
    container.start()

def server_stop(server_uid):
    logging.info("Stopping server [{0}]".format(server_uid))
    client = docker.from_env()
    container = client.containers.get("{0}{1}".format(prefix,server_uid))
    container.stop()

# MAIN - for dev purposes
if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_actions_servers.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    print (servers_reload_current())