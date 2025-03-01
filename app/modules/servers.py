#!/usr/bin/python3
import logging
import json
from pathlib import Path
import sys
import datetime
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
    container_type = 'unknown'
    build_version = 'unknown'
    server_full_uid = (server.name).split('.')
    server_path=f"{server_root_path}/{server_full_uid[2]}/{server_full_uid[3]}"
    try:            
        with open(f'{server_path}/config.json', 'r') as file:
            config_data = dict(json.load(file))
        description = config_data['metadata']['description']
    except:
        description = "None - Please add a description"        

    server_state = server.status
    server_config = {}
    try:
        if server.status == "running":
            container_type=execute_shell(f"docker exec {server.name} printenv CONTAINER_TYPE")[0]
            build_version=execute_shell(f"docker exec {server.name} printenv VERSION")[0]
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
        'container_type': container_type,
        'build_version': build_version,
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

def get_exposed_ports():
    logging.debug("Getting exposed ports for all containers")
    exposed_ports = {}
    try:
        containers = client.containers.list(all=True)
        for container in containers:
            container_info = container.attrs
            ports = container_info['NetworkSettings']['Ports']
            exposed_ports[container.name] = ports
    except Exception as e:
        logging.error(f"Error getting exposed ports: {e}")
        return {"status": "error", "info": "Could not retrieve exposed ports.", "exception": str(e)}
    return exposed_ports

def server_port_check(server_uid):
    logging.debug("Checking if server can start")
    try:
        # Step 1: Load docker-compose file into dict and check used ports
        rootpath=f"{server_root_path}/{server_uid.replace('.','/')}"
        result = {"status" : "success"}
        current_config=f"{rootpath}/docker-compose.yml"
        # Step 2: Check if the ports are currently in use
        with open(current_config, 'r') as file:
            config_data = yaml.load(file, Loader=yaml.FullLoader)
        ports = []
        for service in config_data['services']:
            try:
                ports.append(config_data['services'][service]['ports'][0].split(":")[0])
            except:
                pass
        exposed_ports = get_exposed_ports()
        for container in exposed_ports:
            for port in exposed_ports[container]:
                if "".join([char for char in port if char.isdigit()]) in ports:
                    logging.debug(f"Server [{server_uid}] cannot start because port [{port}] is in use by [{container}]")
                    try:
                        container_uid = ".".join(container.split(".")[-2:])
                    except:
                        container_uid = container
                    if server_uid != container_uid:
                        result =  {"status" : "error", "info" : f'Server [{container_uid}] is using one or more of the ports required by [{server_uid}]', 'err_code' : 'srv.portsused' }
                    else:
                        result = {"status" : "success", "data" : "Server is already running."}
    except Exception as e:
        result = { "status" : "error", "exception" : f"{e}" }
    return result

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
    servers = sorted( servers,key=lambda x: (x["game_uid"], x["servername"]) )
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
        result = execute_shell(f"cd {working_dir} && chown -R 1000:1000 . && docker compose -p {server_uid.replace('.','_')} {action}")
        return {"status" : "success", "info" : f"{server_uid}", "stdout" : f"{result}"}
    except Exception as e:
        logging.error(f"docker_compose_do.nok. {e}")
        return {"status" : "error", "info" : f"Could not complete the requested action for [{server_uid}].", "exception" : f"{e}"}

def server_create(server_uid):
    logging.info("Creating server [{0}]".format(server_uid))
    working_dir = f"{server_root_path}/{server_uid.replace('.','/')}"
    execute_shell(f'[ -d "{working_dir}" ] || mkdir -p "{working_dir}"')
    return docker_compose_do(action='create',server_uid=server_uid)

def server_update(server_uid,mode='full'):
    logging.info(f"Updating server [{server_uid}] (update type = {mode})")
    docker_compose_do(action="stop",server_uid=server_uid)
    logging.debug(f"update mode {mode}")
    if mode == 'reinit':
        logging.debug("Reinitializing server")
        server_delete_files(server_uid,server_only=True)
    if mode in ['reinit','full','all','image','container']:
        logging.debug("Pulling docker image")
        docker_compose_do(action="pull",server_uid=server_uid)
    if mode in ['reinit','full','all','server','game']:
        logging.debug("Updating server files")
        update_flag = f"{server_root_path}/{server_uid.replace('.','/')}/actions/.update"
        if os.path.exists(update_flag):
            os.remove(update_flag)
            logging.debug(".update flag file removed successfully.")
    if (result := server_port_check(server_uid))['status'] != 'success': return result
    logging.debug("Starting server")
    return docker_compose_do(action="up -d",server_uid=server_uid)

def server_start(server_uid):
    logging.info("Starting server [{0}]".format(server_uid))
    if (result := server_port_check(server_uid))['status'] != 'success': return result
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

def server_delete_files(server_uid,server_only=False):
    try:
        working_dir=f"{server_root_path}/{server_uid.replace('.','/')}"
        if server_only:
            execute_shell(f'rm -rf {working_dir}/data/*')  
        else:
            shutil.rmtree(working_dir)
    except Exception as e:
        logging.error(f"Could not delete files in [{working_dir}]. {e}")

def server_backup(server_uid):
    try:
        working_dir = f"{server_root_path}/{server_uid.replace('.', '/')}"
        zip_path = f"/home/peon/backup/{server_uid}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
        execute_shell(f"cd {working_dir} && zip -r {zip_path} . -x '*data/*'")
        return zip_path
    except Exception as e:
        logging.error(f"Could not back up [{working_dir}]. {e}")

def server_download_files(server_uid):
    try:
        return server_backup(server_uid=server_uid)
    except Exception as e:
        logging.error(f"Could not get server content for [{server_uid}]. {e}")

def servers_import():
    # Walk through the directory
    base_path = "/home/peon/servers"
    for root, dirs, files in os.walk(base_path):
        # Split the root directory into parts
        parts = root.split(os.sep)
        # Check if the length of parts is equal to the length of base_path plus 2
        # This indicates a second level folder
        if len(parts) == len(base_path.split(os.sep)) + 2:
            docker_project = f"{root.split('/')[-2]}_{root.split('/')[-1]}"
            # Check if there is a file called `docker-compose.yml` in the root directory
            if "docker-compose.yml" in files:
                execute_shell(f"cd {root} && docker compose -p {docker_project} create")
    
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
    logging.basicConfig(filename='/var/log/DEV.peon.orc_actions_servers.log', filemode='a',
                        format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    print("------------------")
    print(servers_get_all())
    print("------------------")
    print(get_exposed_ports())
    print("------------------")
    print(server_port_check('enshrouded.minesofazhul'))
    print("------------------")
