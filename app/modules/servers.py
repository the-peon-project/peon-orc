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

def server_update_description(server_uid, description):
    try:
        logging.debug(f"Updating {server_uid}'s description to [{description}]")
        config_file = f"{server_root_path}/{server_uid.replace('.','/')}/config.json"
        with open(config_file, 'r') as json_file:
            server_config = json.load(json_file)
        server_config['metadata']['description']=description
        with open(config_file, 'w') as json_file:
            json.dump(server_config, json_file, indent=4)
        return {"status" : "success"}
    except Exception as e:
        return {"status" : "error", "info" : "Could not update the desciption of the server.", "exception" : f"{e}"}

def docker_compose_do(action,server_uid):
    working_dir = f"{server_root_path}/{server_uid.replace('.','/')}"
    try:
        result = execute_shell(f"cd {working_dir} && docker compose {action}")
        return {"status" : "success", "info" : f"{server_uid}", "stdout" : f"{result}"}
    except Exception as e:
        logging.error(f"docker_compose_do.nok. {e}")
        return {"status" : "error", "info" : f"Could not complete the requested action for [{server_uid}].", "exception" : f"{e}"}

def server_create(server_uid):
    logging.info("Creating server [{0}]".format(server_uid))
    return docker_compose_do(action='create',server_uid=server_uid)

def server_start(server_uid):
    logging.info("Starting server [{0}]".format(server_uid))
    return docker_compose_do(action="up -d",server_uid=server_uid)

def server_stop(server_uid):
    logging.info("Stopping server [{0}]".format(server_uid))
    return docker_compose_do(action="stop",server_uid=server_uid)

def server_restart(server_uid):
    logging.info("Restarting server [{0}]".format(server_uid))
    return docker_compose_do(action="restart",server_uid=server_uid)

def server_delete(server_uid):
    logging.info("Deleting server [{0}]".format(server_uid))
    return docker_compose_do(action="down",server_uid=server_uid)

def server_delete_files(server_uid):
    try:
        working_dir=f"{server_root_path}/{server_uid.replace('.','/')}"
        shutil.rmtree(working_dir)
    except Exception as e:
        logging.error(f"Could not delete files in [{working_dir}]. {e}")
        

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

# MAIN - for dev purposes
if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_actions_servers.log', filemode='a',
                        format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    print(servers_get_all())
