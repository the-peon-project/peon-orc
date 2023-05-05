#!/usr/bin/python3
import logging
import traceback
import json
from pathlib import Path
import sys
sys.path.insert(0,'/app')
from modules import client, prefix, schedule_file
from modules.shell import execute_shell
from modules.plans import *
#from .scheduler import schedule_read_from_disk

root_path = "/home/peon"
server_root_path = "{0}/servers".format(root_path)

def server_get_uid(server):
    return "{0}.{1}".format(server['game_uid'], server['servername'])

def server_get_stats(server_uid):
    logging.debug("Getting stats")
    try:
        return client.containers.get("{0}{1}".format(prefix, server_uid)).stats(stream=False)
    except:
        return "Not available"

def schedule_read_from_disk():
    if (Path(schedule_file)).exists():
        with open(schedule_file, 'r') as f:
            schedule = json.load(f)
        return schedule
    else:
        return []

def server_get_server(server):
    server_full_uid = (server.name).split('.')
    server_path=f"{server_root_path}/{server_full_uid[2]}/{server_full_uid[3]}"
    try:            
        with open(f'{server_path}/config.json', 'r') as file:
            config_data = dict(json.load(file))
        description = config_data['metadata']['description']
        #version_peon = config_data['metadata']['version']
    except:
        description = "None - Please add a description"        
    try:
        server_state = server.status
        server_config = {}
        if server.status == "running":
            for filename in os.listdir(f"{server_path}/config/"):
                if os.path.isdir(os.path.join(f"{server_path}/config/", filename)):
                    continue
                with open(os.path.join(f"{server_path}/config/", filename), 'r') as file:
                    contents = file.read().strip()
                server_config[filename] = contents
    except:
        server_state = "UNKNOWN"
        server_config = {"state" : "OFFLINE"}
    try:
        epoch_time = None
        for item in schedule_read_from_disk():
            if item["server_uid"] == "{0}.{1}".format(server_full_uid[2], server_full_uid[3]):
                epoch_time = item["time"]
    except:
        epoch_time = None
    server = {
        'game_uid': server_full_uid[2],
        'servername': server_full_uid[3],
        'container_state': server.status,
        'server_state': server_state,
        'server_config': dict(server_config),
        'description': description,
        'time': epoch_time
    }
    return server


def server_check(server_uid):
    logging.debug("Checking if server exists")
    try:
        return client.containers.get("{0}{1}".format(prefix, server_uid))
    except:
        return "error"


def servers_get_all():
    logging.debug("Checking existing servers")
    servers = []
    containers = client.containers.list(all)
    game_servers = []
    for game_server in containers:
        if prefix in game_server.name:
            game_servers.append(game_server)
    for server in game_servers:
        servers.append(server_get_server(server))
    return servers


def server_update_description(server, description):
    logging.debug("Updating {0}.{1}'s description to [{2}]".format(
        server['game_uid'], server['servername'], description))
    with open("{0}/servers/{1}/{2}/description".format(root_path, server['game_uid'], server['servername']), 'w') as f:
        f.write(description)
    return {"response" : "OK"}


def server_start(server_uid):
    logging.info("Starting server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix, server_uid))
    container.start()
    return {"response" : "OK"}

def server_stop(server_uid):
    logging.info("Stopping server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix, server_uid))
    container.stop()
    return {"response" : "OK"}

def server_restart(server_uid):
    logging.info("Restarting server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix, server_uid))
    container.restart()
    return {"response" : "OK"}

def server_delete_files(server_uid):
    execute_shell("rm -rf {0}/{1}".format(server_root_path, str(server_uid).replace(".", "/")))
    return {"response" : "OK"}

def server_delete(server_uid):
    logging.info("Deleting server [{0}]".format(server_uid))
    container = client.containers.get("{0}{1}".format(prefix, server_uid))
    container.remove()
    return {"response" : "OK"}

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

def server_create(config_peon,user_settings):
    if 'success' not in (result := create_new_warcamp(config_peon=config_peon,user_settings=user_settings))['status']: return result # type: ignore
    try:
        execute_shell(f"cd {result['server_path']} && docker-compose up -d")
    except Exception as e:
        logging.error(f"[server_create] Could not start the server. <{e}>")
        return {"status" : "error", "info" : "Unable to start the server."}
    # # START
    # error = None
    # plan_root_path = "{0}/plans".format(root_path)
    # game_uid = server_uid.split('.')[0]
    # server_name = server_uid.split('.')[1]
    # server_path = "{0}/{1}/{2}".format(server_root_path, game_uid, server_name)
    # container_name = "{0}{1}".format(prefix, server_uid)
    # logging.info("Server deplyment requested [{0}]".format(
    #     container_name))  # Pull latest server files
    # # STEP 1: Initialise game paths
    # execute_shell("mkdir -p {0}/data {0}/config {0}/logs".format(server_path))
    # with open("{0}/description".format(server_path), 'w') as f:
    #     f.write(description)
    # # STEP 2: Import plan config data
    # config = json.load(
    #     open("{0}/games/{1}/config.json".format(plan_root_path, game_uid), 'r'))
    # logging.debug(json.dumps(config["metadata"], indent=4, sort_keys=True))
    # # STEP 3: Deploy container with game server requirements
    # container_config = config["container_config"]
    # server_config = config["server_config"]
    # logging.debug("Container Configuration")
    # logging.debug(json.dumps(container_config, indent=4, sort_keys=True))
    # # Set shared volume path with unique name in key from config, then delete old temp key
    # container_config["volumes"]["{0}/shared".format(
    #     plan_root_path)] = container_config["volumes"]["shared_plan_path"].copy()
    # del container_config["volumes"]["shared_plan_path"]
    # container_config["volumes"]["{0}/games/{1}".format(
    #     plan_root_path, game_uid)] = container_config["volumes"]["unique_plan_path"].copy()
    # del container_config["volumes"]["unique_plan_path"]
    # container_config["volumes"]["{0}/data".format(
    #     server_path)] = container_config["volumes"]["data_path"].copy()
    # del container_config["volumes"]["data_path"]
    # if "config" in container_config["volumes"]:
    #     container_config["volumes"]["{0}/config".format(
    #         server_path)] = container_config["volumes"]["config"].copy()
    #     del container_config["volumes"]["config"]
    # container_config["volumes"]["{0}/logs".format(
    #     server_path)] = container_config["volumes"]["log_path"].copy()
    # del container_config["volumes"]["log_path"]
    # # STEP 4 - Process settings
    # # CLEAN OLD SETTINGS
    # server_config_file = f"{server_path}/config/server.config"
    # if (Path(server_config_file)).is_file():
    #     with open(server_config_file, 'w') as f:
    #         f.write('Services starting...')
    # # SET REQUIRED SETTINGS
    # #container_config["variables"]["PUBLIC_IP"] = execute_shell(
    # #    "dig TXT +short o-o.myaddr.l.google.com @ns1.google.com | tr -d '\"'")[0]
    # for setting in settings:
    #     if 'env' in setting["type"]:
    #         container_config["variables"] = add_envs(
    #             container_config["variables"], setting["content"])
    #     elif 'json' in setting["type"]:
    #         file_json("{0}/config/{1}".format(server_path, setting["name"]), setting["content"])
    #     elif 'txt' in setting["type"]:
    #         file_txt("{0}/config/{1}".format(server_path, setting["name"]), setting["content"])
    # # Set all file/path ownership
    # execute_shell("chown -R 1000:1000 {0}".format(server_path))
    # # STEP 5 - Start container
    # if "-REQUIRED-" in container_config["variables"].values():
    #     return "Not all required settings were provided. Please confirm required settings."
    # try:
    #     container = client.containers.run(
    #         container_config["image"],
    #         name=container_name,
    #         working_dir=container_config["working_directory"],
    #         user=container_config["user"],
    #         volumes=container_config["volumes"],
    #         ports=container_config["ports"],
    #         environment=container_config["variables"],
    #         command=container_config["command"],
    #         detach=True,
    #         tty=True
    #     )
    #     # STEP 6: Run server scripts to deploy container
    #     logging.debug("Executing commands in container")
    #     logging.debug(" {0}".format(server_config["commands"]))
    #     for shell_command in server_config["commands"]:
    #         container.exec_run(
    #             shell_command, user=container_config["user"], environment=container_config["variables"], detach=True, tty=True)
    # except Exception as e:
    #     logging.error(traceback.format_exc())
    #     error = "Container failed to start. Please check orc.logs for details."
    #     try:
    #         container.remove()
    #     except:
    #         logging.warn(f"Failed - container [{container_name}] was not removed. {e}")
    # if error == None:
    #     return {"response" : "OK"}
    # else:
    #     return {"error" : error}


# MAIN - for dev purposes
if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_actions_servers.log', filemode='a',
                        format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    print(servers_get_all())
