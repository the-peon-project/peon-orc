#!/usr/bin/python3
import logging
import traceback
import json
from modules import client, servers, prefix
from .shell import execute_shell
from .plans import *

root_path = "/root/peon"
server_root_path = "{0}/servers".format(root_path)


def server_get_uid(server):
    return "{0}.{1}".format(server['game_uid'], server['servername'])


def server_get_stats(server_uid):
    logging.debug("Getting stats")
    try:
        return client.containers.get("{0}{1}".format(prefix, server_uid)).stats(stream=False)
    except:
        return "Not available"


def server_get_server(server):
    server_full_uid = (server.name).split('.')
    try:
        with open('{0}/{1}/{2}/description'.format(server_root_path, server_full_uid[2], server_full_uid[3]), 'r') as f:
            description = f.read()
        if server.status == "running":
            with open('{0}/{1}/{2}/data/server.state'.format(server_root_path, server_full_uid[2], server_full_uid[3]), 'r') as f:
                server_state = f.read()
        else:
            server_state = "UNKNOWN"
    except:
        description = "None - Please add a description"
    server = {
        'game_uid': server_full_uid[2],
        'servername': server_full_uid[3],
        'container_state': server.status,
        'server_state': server_state,
        'description': description
    }
    return server


def server_check(server_uid):
    logging.debug("Checking if server exists")
    try:
        return client.containers.get("{0}{1}".format(prefix, server_uid))
    except:
        return "error"


def servers_get_all():
    logging.debug("Checking exisitng servers")
    servers.clear()
    containers = client.containers.list(all)
    game_servers = []
    for game_server in containers:
        if prefix in game_server.name:
            game_servers.append(game_server)
    for server in game_servers:
        servers.append(server_get_server(server))


def server_update_description(server, description):
    logging.debug("Updating {0}.{1}'s description to [{2}]".format(
        server['game_uid'], server['servername'], description))
    with open("{0}/servers/{1}/{2}/description".format(root_path, server['game_uid'], server['servername']), 'w') as f:
        f.write(description)


def server_start(server_uid):
    logging.info("Starting server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix, server_uid))
    container.start()


def server_stop(server_uid):
    logging.info("Stopping server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix, server_uid))
    container.stop()


def server_restart(server_uid):
    logging.info("Restarting server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix, server_uid))
    container.restart()


def server_delete_files(server_uid):
    execute_shell("rm -rf {0}/{1}".format(server_root_path,str(server_uid).replace(".","/")))

def server_delete(server_uid):
    logging.info("Deleting server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix, server_uid))
    container.remove()


def add_envs(env_vars, content):
    for key in content.keys():
        env_vars[key] = content[key]
    return env_vars


def file_json(path, content):
    with open(path, 'w') as f:
        json.dump(content, f)


def file_txt(path, content):
    with open(path, 'w') as f:
        f.write(content)


def server_create(server_uid, description, settings=[]):
    # START
    error = "none"
    plan_root_path = "{0}/plans".format(root_path)
    game_uid = server_uid.split('.')[0]
    server_name = server_uid.split('.')[1]
    server_path = "{0}/{1}/{2}".format(server_root_path, game_uid, server_name)
    container_name = "{0}{1}".format(prefix, server_uid)
    logging.info("Server deplyment requested [{0}]".format(
        container_name))  # Pull latest server files
    # STEP 1: Initialise game paths
    execute_shell("mkdir -p {0}/data {0}/config {0}/logs".format(server_path))
    with open("{0}/description".format(server_path), 'w') as f:
        f.write(description)
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
    # SET REQUIRED SETTINGS
    container_config["variables"]["PUBLIC_IP"] = execute_shell("dig TXT +short o-o.myaddr.l.google.com @ns1.google.com | tr -d '\"'")[0]
    for setting in settings:
        if 'env' in setting["type"]:
            container_config["variables"] = add_envs(
                container_config["variables"], setting["content"])
        elif 'json' in setting["type"]:
            file_json("{0}/config/{1}".format(server_path,
                      setting["name"]), setting["content"])
        elif 'txt' in setting["type"]:
            file_txt("{0}/config/{1}".format(server_path,
                     setting["name"]), setting["content"])
    # Set all file/path ownership
    execute_shell("chown -R 1000:1000 {0}".format(server_path))
    # STEP 5 - Start container
    if "-REQUIRED-" in container_config["variables"].values():
        return "Not all required settings were provided. Please confirm required settings."
    try:
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
            logging.warn(
                "Failed - container [{0}] was not removed.".format(container_name))
    return error


# MAIN - for dev purposes
if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_actions_servers.log', filemode='a',
                        format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
