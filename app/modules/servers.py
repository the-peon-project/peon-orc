#!/usr/bin/python3
import logging
import traceback
import json
from modules import client, servers, settings, prefix
from .shell import execute_shell


def server_get_uid(server):
    return "{0}.{1}".format(server['game_uid'], server['servername'])


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
            'game_uid': server_full_uid[2],
            'servername': server_full_uid[3],
            'password': "**********",
            'state': game_server.status,
            'description': "- IMPLEMENT A DB -"
        }
        servers.append(server)


def server_start(server_uid):
    logging.info("Starting server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix, server_uid))
    container.start()


def server_stop(server_uid):
    logging.info("Stopping server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix, server_uid))
    container.stop()


def server_delete(server_uid):
    logging.info("Deleting server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix, server_uid))
    container.remove()

def add_envs(env_vars,content):
    for key in content.keys():
        env_vars[key] = content[key]
    return env_vars

def file_json(path,content):
    with open(path, 'w') as f: json.dump(content, f)

def file_txt(path,content):
    with open(path, 'w') as f: f.write(content)

def server_create(server_uid, settings=[]):
    # START
    error = "none"
    root_path = "/root/peon"
    server_root_path = "{0}/servers".format(root_path)
    plan_root_path = "{0}/plans".format(root_path)
    game_uid = server_uid.split('.')[0]
    server_name = server_uid.split('.')[1]
    server_path = "{0}/{1}/{2}".format(server_root_path, game_uid, server_name)
    container_name = "{0}{1}".format(prefix, server_uid)
    logging.info("Server deplyment requested [{0}]".format(container_name))
    # STEP 1: Initialise game paths
    execute_shell("mkdir -p {0}/data {0}/config {0}/logs".format(server_path))
    # STEP 2: Import plan config data
    config = json.load(
        open("{0}/games/{1}/config.json".format(plan_root_path, game_uid), 'r'))
    logging.debug(json.dumps(config["metadata"], indent=4, sort_keys=True))
    # STEP 3: Deploy container with game server requirements
    container_config = config["container_config"]
    server_config = config["server_config"]
    logging.debug("Container Configuration")
    logging.debug(json.dumps(container_config, indent=4, sort_keys=True))
    # Set shared volume path with unique name in key from config, then delete old temp key
    container_config["volumes"]["{0}/shared".format(
        plan_root_path)] = container_config["volumes"]["shared_plan_path"].copy()
    del container_config["volumes"]["shared_plan_path"]
    container_config["volumes"]["{0}/games/{1}".format(
        plan_root_path, game_uid)] = container_config["volumes"]["unique_plan_path"].copy()
    del container_config["volumes"]["unique_plan_path"]
    container_config["volumes"]["{0}/data".format(
        server_path)] = container_config["volumes"]["data_path"].copy()
    del container_config["volumes"]["data_path"]
    if "config" in container_config["volumes"]:
        container_config["volumes"]["{0}/config".format(
            server_path)] = container_config["volumes"]["config"].copy()
        del container_config["volumes"]["config"]
    container_config["volumes"]["{0}/logs".format(
        server_path)] = container_config["volumes"]["log_path"].copy()
    del container_config["volumes"]["log_path"]
    # STEP 4 - Process settings
    for setting in settings:
        print (setting)
        if 'env' in setting["type"]: container_config["variables"] = add_envs(container_config["variables"],setting["content"])
        elif 'json' in setting["type"]: file_json("{0}/config/{1}".format(server_path,setting["name"]),setting["content"])
        elif 'txt' in setting["type"]: file_txt("{0}/config/{1}".format(server_path,setting["name"]),setting["content"])
    # Set all file/path ownership
    execute_shell("chown -R 1000:1000 {0}".format(server_path))
    # STEP 5 - Start container
    if "-REQUIRED-" in container_config["variables"]:
        error = "Not all required settings were provided. Please confirm required settings."
    try:
        if error == "none":
            container = client.containers.run(
                container_config["image"],
                name=container_name,
                working_dir=container_config["working_directory"],
                user=container_config["user"],
                volumes=container_config["volumes"],
                ports=container_config["ports"],
                environment=container_config["variables"],
                command=container_config["command"],
                detach=True,
                tty=True
            )
            # STEP 6: Run server scripts to deploy container
            logging.debug("Executing commands in container")
            logging.debug(" {0}".format(server_config["commands"]))
            for shell_command in server_config["commands"]:
                container.exec_run(
                    shell_command, user=container_config["user"], environment=container_config["variables"], detach=True, tty=True)
    except Exception as e:
        logging.error(traceback.format_exc())
        error = "Container failed to start. Please check orc.logs for details."
        try: 
            container.remove()
        except:
            logging.warn("Failed container [{0}] was not removed.".format(container_name))
    return error


# MAIN - for dev purposes
if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_actions_servers.log', filemode='a',
                        format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
