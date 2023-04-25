#!/usr/bin/python3
import logging
import json
import yaml
import requests
import sys
import os
sys.path.insert(0,'/app')
from modules.github import *
from modules.peon import get_warcamp_name



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

def get_remote_plan_version(game_uid):
    try:
        game_plan_url = config['settings']['plan_url'].format(game_uid)
        if (response := requests.get(game_plan_url)).status_code == 200: # type: ignore
            return (json.loads(response.content))['metadata']['version']
    except Exception as e:
            logging.warning(f"[get_remote_plan_version] A plan definition file for [{game_uid}] was not found at [{game_plan_url}]. {e}")
    return None

# LOCAL PLAN FUNCTIONS
def get_local_plan_definition(file_path):
    try: 
        if os.path.isfile(file_path):
            with open(file_path) as json_file:
                game_plan = json.load(json_file)    
        return game_plan
    except Exception as e:
        logging.warning(f"[get_game_plan_from_file] The plan definition file [{file_path}] was not found. {e}")
    return None

def get_required_settings(game_uid,config):
    if (plan := get_local_plan_definition(f"{config['path']['plans']}/{game_uid}/plan.json")):  # type: ignore
        return ([key for key, value in plan['environment'].items() if value is None])
    else:
        return None

def consolidate_settings(user_settings,plan): # Check exisiting config and update new config accordingly. If there is an unknown entity, throw an error.
    # CHECK FOR REQUIRED VALUES
    provided_settings = list(user_settings.keys())
    required_settings = get_required_settings(plan['metadata']['game_uid'],config)
    if not any(setting in provided_settings for setting in required_settings): return { "status" : "error", "info" : f"Not all required server settings were provided. Namely: {required_settings}" }
    # METADATA
    if "description" in user_settings: plan['metadata']["description"] = user_settings["description"]
    plan['metadata']["warcamp"] = user_settings["warcamp"]
    plan['metadata']['hostname']+=f".{user_settings['warcamp']}"
    plan['metadata']['container_name']=plan['metadata']['hostname']
    # ENVIRONMENT VARIABLES
    for key in plan['environment']:
        if key in user_settings and key not in ['STEAM_ID']:
            plan['environment'][key] = user_settings[key]
    return { "status" : "success", "plan" : plan}

def generate_build_file(server_path,config): # Take a config and create a docker-compose.yml file
    manifest = {}
    # Metadata
# Metadata
    manifest['version'] = "3"
    manifest['services'] = {
        'server': {
            'container_name': config['metadata']['container_name'],
            'hostname': config['metadata']['hostname'],
            'image': config['metadata']['image']
        }
    }
    port_list = []
    for port in config['ports'][0]:
        name=list(port.keys())[0]
        value=port[name][0]
        proto=port[name][1]
        config['environment'][name] = value # Create an envioronment variable for the port
    # Ports
    #manifest['services']['server']['ports']
    # Environment
    
    # Volumes
    
    
    print (yaml.dump(manifest,sort_keys=False, indent=4))
    try:
        with open(f"{server_path}/docker-compose.yml", "w") as file:
            yaml.dump(config,file, sort_keys=False, indent=4)
        return { "status" : "success" }
    except Exception as e:
        return { "status" : "error", "info" : f"Could not create the `docker-compose.yml` file. {e}" }
        

def configure_permissions(server_path): # chown & chmod on path
    logging.critical("[consolidate_settings] TODO !!!!") # TODO

# WARCAMP FUNCTIONS
def create_warcamp(user_settings,config):
    game_uid=user_settings["game_uid"]
    if "warcamp" not in user_settings: user_settings['warcamp'] = get_warcamp_name()
    warcamp=user_settings['warcamp']
    server_path=f"{config['path']['servers']}/{game_uid}/{warcamp}"
    # Check if there is already a plan in that directory
    try: 
        if (get_local_plan_definition(f"{server_path}/docker-compose.yml")): return { "status" : "error" , "info" : f"There is already a config for [{game_uid}] [{warcamp}]. Please run update on the game/server instead. (Can be added in a future release.)" }
    except:
        logging.debug("[create_warcamp] No pre-existing config found.")
    # Get default plan definition
    if not (default_plan := get_local_plan_definition(f"{config['path']['plans']}/{game_uid}/plan.json")): return {"status" : "error", "info" : f"There is no locally default available plan for {game_uid}."}  # type: ignore
    # Create new directory
    if not os.path.exists(server_path):
        os.makedirs(server_path, exist_ok=True)
    # Configure default settings and save plan as default
    if "warcamp" not in user_settings: user_settings['warcamp'] = get_warcamp_name()
    
    default_plan['metadata']['warcamp'] = user_settings['warcamp']
    with open(f'{server_path}/plan.json', 'w') as f:
        json.dump(default_plan, f, indent=4)
    if "success" not in (result := consolidate_settings(user_settings=user_settings,plan=default_plan))['status']: return result  # type: ignore
    with open(f'{server_path}/config.json', 'w') as f:
        json.dump(result['plan'], f, indent=4)
    if "success" not in (result := generate_build_file(server_path=server_path,config=result['plan']))['status']: return result  # type: ignore
    return configure_permissions(server_path=server_path)

def update_warcamp(game_uid,warcamp):
    # Update config where possible (return highlighted change if something is missing)
    pass

def get_warcamp_config(game_uid,warcamp):
    pass #modified_plan = get_local_plan_version(f"{config['path']['plans']}/{game_uid}/{warcamp}/settings.json")

def modify_warcamp_config(user_settings):
    # game_uid = user_settings['game_uid']
    # warcamp = user_settings['warcamp']
    # # Get default config
    # default_plan = get_local_plan_version(f"{config['path']['plans']}/{game_uid}/plan.json")
    # modified_plan = get_local_plan_version(f"{config['path']['plans']}/{game_uid}/{warcamp}/settings.json")
    pass

# MAIN - DEV TEST

if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_plans.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    config = json.load(open("/app/config.json", 'r'))
    user_settings={
        "game_uid"    : "vrising",
        "description" : "A V Rising server",
        "SERVER_NAME" : "countjugular",
        "WORLD_NAME"  : "townsville",
        "PASSWORD"    : "Zu88Zu88"
    }
    print(create_warcamp(user_settings,config))
