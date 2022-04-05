#!/usr/bin/python3
import logging
import json
from modules import client,servers,settings,prefix

def server_get_uid(server):
    return "{0}.{1}".format(server['game_uid'],server['servername'])

def servers_reload_current():
    logging.debug("Checking exisitng servers")
    servers.clear()
    containers = client.containers.list(all)
    game_servers = []
    for game_server in containers:
        if prefix in game_server.name:
            game_servers.append(game_server)
    for game_server in game_servers:
        server_full_uid = (game_server.name).split('.')
        server = {
                'game_uid' : server_full_uid[2],
                'servername' : server_full_uid[3],
                'password' : "**********",
                'state' : game_server.status,
                'description' : "- IMPLEMENT A DB -"
        }
        servers.append(server)

def server_start(server_uid):
    logging.info("Starting server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix,server_uid))
    container.start()

def server_stop(server_uid):
    logging.info("Stopping server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix,server_uid))
    container.stop()

def server_delete(server_uid):
    logging.info("Deleting server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix,server_uid))
    container.remove()

def server_deploy(server_uid,user_settings):

    # START
    # STEP 1: Clone plans into server path
    temp_working_dir = "/root/peon/servers/csgo"
    # STEP 2: Import plan config
    server_config = json.load(open("{0}/config.json".format(temp_working_dir), 'r'))
    logging.info("Server deplyment requested:")
    logging.info(json.dumps(server_config["metadata"], indent=4, sort_keys=True))
    # STEP 3: Collect options
    
    # STEP 4: Update config with settings
    # STEP 5: Deploy container based on prefered settings
    container_config=server_config["container_config"]
    logging.debug("Contatiner Configuration")
    logging.debug(json.dumps(container_config, indent=4, sort_keys=True))
    container = client.containers.run(
        container_config["image"],
        name="{0}{1}".format(prefix,server_uid),
        working_dir=container_config["working_directory"],
        user=container_config["user"],
        volumes=container_config["volumes"],
        ports=container_config["ports"],
        detach=True,
        tty=True
    )

# MAIN - for dev purposes
if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_actions_servers.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)