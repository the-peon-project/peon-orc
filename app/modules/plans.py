#!/usr/bin/python3
import logging
import json
import yaml
import requests
import sys
import shutil
import glob
import os
sys.path.insert(0,'/app')
from modules.github import *
from modules.shell import execute_shell
from modules.peon import get_warcamp_name
from modules import settings

# SPECIAL FUNCTIONS
def identify_newest_version(version_local, version_remote):
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

# REMOTE REPOSITORY PLANS
def download_latest_plans_from_repository(repo='github'): # On start (if empty) & on request
    if "github" in repo:
        return get_plans_from_github()
    else:
        return { "status" : "error", "info" : f"The repository [{repo}] is not yet supported." }
    
def update_latest_plans_from_repository(repo='github', force=True):
    if "github" in repo:
        return update_plans_from_github(force=force)
    else:
        return { "status" : "error", "info" : f"The repository [{repo}] is not yet supported." }

def get_remote_plan_version(config_peon,game_uid):
    try:
        game_plan_url = config_peon['settings']['plan_url'].format(game_uid)
        if (response := requests.get(game_plan_url)).status_code == 200: # type: ignore
            return (json.loads(response.content))['metadata']['version']
    except Exception as e:
            logging.warning(f"[get_remote_plan_version] A plan definition file for [{game_uid}] was not found at [{game_plan_url}]. {e}")
    return None

def get_plans_local(config_peon):
    try:
        with open(f"{config_peon['path']['plans']}/plans.json") as json_file:
            plans = json.load(json_file)
        return sorted(plans, key=lambda x: x["title"])
    except Exception as e:
        logging.error(f"[get_plans_local] Could not get the local plans file. {e}")
        return None

def get_plans_remote(config_peon):
    try:
        response = requests.get(config_peon['settings']['plans_url'])
        with open(f"{config_peon['path']['plans']}/plans.json", mode='wb') as f:
            f.write(response.content)
        return get_plans_local(config_peon=config_peon)
    except Exception as e:
        logging.error(f"[get_plans_remote] There was an issue getting the latest plans from the Github repo. {e}")
        return None

def configure_plan_permissions():
    try:
        logging.error("Setting folder permissions...")
        execute_shell(cmd_as_string=f"chown -R 1000:1000 {settings['path']['plans']}")
        return { "status" : "success" }
    except Exception as e:
        logging.error("--- FAILED")
        return {"status" : "error", "info" : "Could not set permissions on plans folder.", "exception" : f"{e}" }

# LOCAL PLAN FUNCTIONS
def get_local_plan_definition(file_path):
    try: 
        if os.path.isfile(file_path):
            with open(file_path) as json_file:
                game_plan = json.load(json_file)    
        return game_plan
    except Exception as e:
        logging.debug(f"get_local_plan_definition.nok The plan definition file [{file_path}] was not found. {e}")
    return None

def get_all_required_settings(config_peon,game_uid):
    try:
        if (plan := get_local_plan_definition(f"{config_peon['path']['plans']}/{game_uid}/plan.json")):  # type: ignore
            settings = plan['environment']
            settings['description'] = f"A PEON game server for {game_uid}."
            required = {}
            optional = {}
            for key, value in settings.items():
                if key not in ['STEAM_ID']:
                    if value: 
                        optional[key] = f"{value}"
                    else: required[key] = ""
            required.update(optional)
            return required
    except Exception as e:
        logging.error(f"[get_all_required_settings] An issue occured getting the required settings for {game_uid}. <{e}>")
    return None

def get_required_settings(config_peon,game_uid,warcamp):
    if (plan := get_local_plan_definition(f"{config_peon['path']['servers']}/{game_uid}/{warcamp}/config.json")):  # type: ignore
        return ([key for key, value in plan['environment'].items() if value is None])
    else:
        return None

def consolidate_settings(config_peon,user_settings,plan): # Check exisiting config and update new config accordingly. If there is an unknown entity, throw an error.
    # CHECK IF ALL REQUIRED SETTINGS HAVE BEEN PROVIDED
    provided_settings = list(user_settings.keys())
    required_settings = get_required_settings(config_peon=config_peon,game_uid=plan['metadata']['game_uid'],warcamp=plan['metadata']['warcamp'])
    if required_settings: 
        if not any(setting in provided_settings for setting in required_settings): return { "status" : "error", "info" : f"Not all required server settings were provided. Namely: {required_settings}" }
    # UPDATE METADATA
    if "description" in user_settings: plan['metadata']["description"] = user_settings["description"]
    if "warcamp" in user_settings: plan['metadata']["warcamp"] = user_settings["warcamp"]
    plan['metadata']['hostname']=f"peon.warcamp.{user_settings['game_uid']}.{plan['metadata']['warcamp']}"
    plan['metadata']['container_name']=plan['metadata']['hostname']
    # ENVIRONMENT VARIABLES
    for key in plan['environment']:
        if key in user_settings and key not in ['STEAM_ID']:
            plan['environment'][key] = user_settings[key]
    return { "status" : "success", "plan" : plan}

def update_build_file(server_path,config_warcamp): # Take a config and create a docker-compose.yml file
    manifest = {}
    port_list = []
    env_var_list = []
    mount_list = []
    # Metadata
    manifest['version'] = "3"
    manifest['services'] = {
        'server': {
            'container_name': config_warcamp['metadata']['container_name'],
            'hostname': config_warcamp['metadata']['hostname'],
            'image': config_warcamp['metadata']['image']
        }
    }
    # Ports
    for port in config_warcamp['ports']:
        name=list(port.keys())[0].upper()
        value=port[name][0]
        proto=port[name][1].lower()
        if proto in ['tcp','udp']:
            port_list.append(f"{value}:{value}/{proto}")
        else:
            port_list.append(f"{value}:{value}/tcp")
            port_list.append(f"{value}:{value}/udp")
        env_var_list.append(f"{name}={value}")
    manifest['services']['server']['ports'] = port_list
    # Environment Variables
    for env_var, value in config_warcamp['environment'].items(): 
        env_var_list.append(f"{env_var}={value}")
    manifest['services']['server']['environment']=env_var_list
    # Volumes
    docker_host_path = os.environ.get('HOST_DIR')
    if not docker_host_path:
        return { "status" : "error", "info" : f"PEON_DIRECTORY not configured in .env file. (HOST_DIR env var is empty)" }
    host_server_path=server_path.replace(settings['path']['servers'],f"{docker_host_path}/servers")
    for source, target in config_warcamp['volumes'].items():
        if '~!' in source: # Added to allow custom mount paths, but have to link to specific location on the host system
            source = source.replace("~!", host_server_path)
        mount_list.append(f"{source}:{target}")
    # Custom file mount
    if 'files' in config_warcamp:
        for source, target in config_warcamp['files'].items():
            if '~!' in source: source = source.replace("~!/", "")
            if os.path.exists(f"{server_path}/{source}"):
                mount_list.append(f"{host_server_path}/{source}:{target}")
    manifest['services']['server']['volumes']=mount_list
    # User
    manifest['services']['server']['user']="1000:1000"
    # # Restart Policy
    # manifest['services']['server']['restart']="unless-stopped"
    try:
        with open(f"{server_path}/docker-compose.yml", "w") as f:
            yaml.dump(manifest, f, sort_keys=False, indent=4)
        return { "status" : "success" , "manifest" : manifest}
    except Exception as e:
        return { "status" : "error", "info" : f"Could not create the `docker-compose.yml` file. {e}" }

def configure_permissions(server_path): # chown & chmod on path
    try:
        execute_shell(cmd_as_string=f"chown -R 1000:1000 {server_path}")
        execute_shell(cmd_as_string=f"chmod 755 {server_path}/scripts/.")
        return {"status" : "success"}
    except Exception as e:
        return {"status" : "error", "info" : f"Unable to configure permissions for server. {e}"}

def identify_available_port_group(config_peon,game_uid,warcamp):
    ports = (get_local_plan_definition(f"{config_peon['path']['servers']}/{game_uid}/{warcamp}/config.json"))['ports']
    ## TODO - Figure out how to check which ports are available.
    # return {"status" : "error", "info" : f"The could not find a valid available port group to use for {game_uid}"}
    ## Figure out how to check which ports are available. END
    ports = ports[0]
    return { "status" : "success", "open_ports" : ports }

# WARCAMP FUNCTIONS
def create_new_warcamp(config_peon,user_settings):
    game_uid=user_settings["game_uid"]
    warcamp=user_settings['warcamp']
    server_path=user_settings['server_path']
    # Check if there is already a plan in that directory
    logging.debug("create_warcamp.01. Check if there is already a configured server.")
    try: 
        if (get_local_plan_definition(f"{server_path}/config.json")): return { "status" : "error" , "info" : f"There is already a config.json file for [{game_uid}] [{warcamp}]. Please run update on the game/server instead. (Can be added in a future release.)" }
    except:
        logging.debug("create_warcamp.01. No pre-existing server config found.")
    # Get default plan definition
    logging.debug("create_warcamp.02. Collect plan definition from plan path.")
    if not (plan := get_local_plan_definition(f"{config_peon['path']['plans']}/{game_uid}/plan.json")): return {"status" : "error", "info" : f"There is no local default plan for {game_uid}."}  # type: ignore
    # Create new game directory, if required
    logging.debug("create_warcamp.03. Create a directory for the game server.")
    if not os.path.exists(f"{config_peon['path']['servers']}/{game_uid}"):
        os.makedirs(f"{config_peon['path']['servers']}/{game_uid}", exist_ok=True)
    shutil.copytree(f"{config_peon['path']['plans']}/{game_uid}/", server_path)
    shutil.copy(f"{server_path}/plan.json",f"{server_path}/config.json")
    # Configure default settings
    logging.debug("create_warcamp.04. Colate user settings with plan default settings.")
    if "warcamp" not in user_settings: user_settings['warcamp'] = get_warcamp_name()
    plan['metadata']['warcamp'] = user_settings['warcamp']
    if "success" not in (result := consolidate_settings(config_peon=config_peon,user_settings=user_settings,plan=plan))['status']: return result  # type: ignore
    plan=result['plan']
    if "success" not in (result := identify_available_port_group(config_peon=config_peon,game_uid=game_uid,warcamp=warcamp))['status']: return result # type: ignore
    plan['ports'] = result['open_ports']
    with open(f'{server_path}/config.json', 'w') as f:
        json.dump(plan, f, indent=4)
    logging.debug("create_warcamp.05. Create server specific config file.")
    if "success" not in (result := update_build_file(server_path=server_path,config_warcamp=plan))['status']: return result  # type: ignore
    logging.debug("create_warcamp.06. Configure file permissions.")
    if "success" not in configure_permissions(server_path=server_path)['status']: return result
    return {"status" : "success", "game_uid" : f"{game_uid}", "warcamp" : f"{warcamp}", "server_path" : f"{server_path}" }

def update_warcamp(game_uid,warcamp):
    # TODO Update config where possible (return highlighted change if something is missing)
    pass

def get_warcamp_config(config_peon,game_uid,warcamp,user_friendly=True):
    files_active = []
    warcamp_path=f"{config_peon['path']['servers']}/{game_uid}/{warcamp}"
    warcamp_config_file=f"{warcamp_path}/config.json"
    #warcamp_active_config_file=f"{warcamp_path}/docker-compose.yml"
    if os.path.exists(warcamp_config_file):
        # Load current config
        with open(warcamp_config_file, "r") as f:
            config_warcamp = json.load(f)
        # Identify any loaded gamer server config files
        if 'files' in config_warcamp:
            for filename in config_warcamp['files']:
                if os.path.isfile(f"{warcamp_path}/{filename}"):
                    files_active.append(filename)
            del config_warcamp['files']
            if files_active: config_warcamp['uploaded_files'] = files_active
        # Check if there is a config folders and therefore supplimental info to provide
        if os.path.exists(f"{warcamp_path}/config"):
            supplimental_info = {}
            for file_path in glob.glob(os.path.join(f"{warcamp_path}/config/", '*')):
                filename = os.path.basename(file_path)
                if filename.startswith('.'): continue # Skip `hidden` files
                with open(file_path, 'r') as file:
                    contents = file.read()
                    supplimental_info[filename.lower()] = contents.strip() # Removed newlines and enforce 
            if supplimental_info: config_warcamp['supplimental'] = supplimental_info
        # Get container information
        # Clean output for user friendlyness
        if user_friendly: 
            config_warcamp_uf = {}
            config_warcamp_uf['game_uid'] = config_warcamp['metadata']['game_uid']
            config_warcamp_uf['warcamp'] = config_warcamp['metadata']['warcamp']
            config_warcamp_uf['description'] = config_warcamp['metadata']['description']
            if "supplimental" in config_warcamp:
                config_warcamp_uf['state'] = config_warcamp['supplimental']['state'] if config_warcamp['supplimental']['state'] else "UNKNOWN"
                config_warcamp_uf['ip'] = config_warcamp['supplimental']['ip'] if config_warcamp['supplimental']['ip'] else ""
            if files_active: config_warcamp_uf['uploaded_files'] = files_active
            for port_dict in config_warcamp['ports']:
                port_name, (port_number, protocol) = list(port_dict.items())[0]
                config_warcamp_uf[port_name] = f"{port_number}/{protocol}"
            for env_var in config_warcamp['environment']:
                if env_var not in ['STEAM_ID','STEAM_GSLT','STEAM_PASSWORD']:
                    config_warcamp_uf[env_var] = config_warcamp['environment'][env_var]
            return {"status" : "success", "data" : config_warcamp_uf }
        return {"status" : "success", "data" : config_warcamp }
    else:
        return { "status" : "error", "info" : "There does not appear to be a server at that path."}

# MAIN - DEV TEST

if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_plans.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    config_peon = json.load(open("/app/config.json", 'r'))
    # VRISING
    # user_settings={
    #     "game_uid"    : "vrising",
    #     "warcamp"     : "vrsingsun",
    #     "description" : "A V Rising server",
    #     "SERVER_NAME" : "vrsingsun",
    #     "WORLD_NAME"  : "vrsingsun",
    #     "PASSWORD"    : "MeatOnTheMenu"
    # }
    # CSGO
    # user_settings={
    #     "game_uid"    : "csgo",
    #     "description" : "A CSGO server",
    #     "SERVER_NAME" : "fightnight",
    #     "STEAM_GSLT"  : "29FAFDA01234567890123416C352C430",
    # }
    # VALHEIM
    # user_settings={
    #      "game_uid"    : "valheim",
    #      "description" : "A Valheim server",
    #      "SERVER_NAME" : "valserv",
    #      "WORLD_NAME"  : "myworld",
    #      "PASSWORD"    : "Shmeep"
    #  }
    # QUAKE 3
    # user_settings={
    #     "game_uid"    : "quake3",
    #     "description" : "A quake3 server"
    # }
    # Satisfactory
    # user_settings={
    #     "game_uid"    : "satisfactory",
    #     "description" : "A Satisfactory server",
    #     "SERVER_NAME" : "N/A"
    # }
    # - - - - - 
    # server = create_new_warcamp(config_peon=config_peon,user_settings=user_settings)
    # print(json.dumps(get_warcamp_config(config_peon=config_peon,game_uid=server['game_uid'],warcamp=server['warcamp'],user_friendly=True),indent=4))
