#!/usr/bin/python3
import logging
import json
from modules import client,servers,settings,prefix
from shell import execute_shell

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
    root_path = "/root/peon/servers"
    game_uid=server_uid.split('.')[0]
    server_name=server_uid.split('.')[1]
    server_path = "{0}/{1}/{2}".format(root_path,game_uid,server_name)
    container_name = "{0}{1}".format(prefix,server_uid)
    logging.info("Server deplyment requested [{0}]".format(container_name))
    # STEP 1: Initialise game path
    execute_shell("mkdir -p {0}/data && chown -R 1000:1000 {0}".format(server_path))
    execute_shell("mkdir -p /var/log/peon/{0} && chown -R 1000:1000 /var/log/peon/.".format(server_uid))
    # STEP 2: Import plan config data
    config = json.load(open("{0}/{1}/config.json".format(root_path,game_uid), 'r'))
    logging.debug(json.dumps(config["metadata"], indent=4, sort_keys=True))
    # STEP 3: Deploy container with game server requirements
    container_config=config["container_config"]
    server_config=config["server_config"]
    logging.debug("Container Configuration")
    logging.debug(json.dumps(container_config, indent=4, sort_keys=True))
    container_config["volumes"]["{0}/data".format(server_path)] = container_config["volumes"]["data_path"].copy()
    del container_config["volumes"]["data_path"]
    container_config["volumes"]["/var/log/peon/{0}".format(server_uid)] = container_config["volumes"]["log_path"].copy()
    del container_config["volumes"]["log_path"]
    container = client.containers.run(
        container_config["image"],
        name=container_name,
        working_dir=container_config["working_directory"],
        user=container_config["user"],
        volumes=container_config["volumes"],
        ports=container_config["ports"],
        environment=container_config["variables"],
        detach=True,
        tty=True
    )
    # STEP 4: Copy necessary plan deployment files into container
    logging.debug("Copy deplyment files into container.")
    for file in config["server_config"]["files"]:
        logging.debug(" {0}".format(file))
        execute_shell("docker cp {0}/{1}/{2} {3}:{4}/".format(root_path,game_uid,file,container_name,container_config["working_directory"]))
    # STEP 5: Run server scripts to deploy container
    logging.debug("Exectuing commands in container")
    logging.debug(" {0}".format(server_config["commands"]))
    container.exec_run(
        server_config["commands"],
        workdir=container_config["working_directory"],
        user=container_config["user"],
        detach=True,
        tty=True
    )

# MAIN - for dev purposes
if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_actions_servers.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)