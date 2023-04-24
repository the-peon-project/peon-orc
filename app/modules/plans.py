#!/usr/bin/python3
import logging
import json
import requests
import sys
import shutil
import os
sys.path.insert(0,'/app')
from modules.github import *

config = json.load(open("/app/config.json", 'r'))

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
        if (response := requests.get(game_plan_url)).status_code == 200:
            return (json.loads(response.content))['metadata']['version']
    except Exception as e:
            logging.warn(f"[get_remote_plan_version] A plan definition file for [{game_uid}] was not found at [{game_plan_url}]. {e}")
    return None

# LOCAL PLAN FUNCTIONS
def get_local_plan_definition(file_path):
    try: 
        if os.path.isfile(file_path):
            with open(file_path) as json_file:
                game_plan = json.load(json_file)    
        return game_plan
    except Exception as e:
        logging.warn(f"[get_game_plan_from_file] The plan definition file [{file_path}] was not found. {e}")
    return None

def consolidate_settings(user_settings,plan): # Check exisiting config and update new config accordingly. If there is an unknown entity, throw an error.
    logging.critical("[consolidate_settings] TODO !!!!") # TODO
    return { "status" : "success", "plan" : plan}

def generate_build_file(config): # Take a config and create a docker-compose.yml file
    logging.critical("[consolidate_settings] TODO !!!!") # TODO

def configure_permissions(server_path): # chown & chmod on path
    logging.critical("[consolidate_settings] TODO !!!!") # TODO

# WARCAMLP FUNCTIONS

def create_warcamp(user_settings):
    game_uid=user_settings["game_uid"]
    server_name=user_settings["server_name"]
    server_path=f"{config['path']['server']}/{game_uid}/{server_name}"
    # Check if there is already a plan in that directory
    try: 
        if (get_local_plan_definition(f"{server_path}/docker-compose.yml")): return { "status" : "error" , "info" : f"There is already a config for [{game_uid}] [{server_name}]. Please run update on the game/server instead. (Can be added in a future release.)" }
    except:
        logging.debug("[create_warcamp] No pre-existing config found.")
    # Get default plan definition
    if not (default_plan := get_local_plan_definition(f"{config['path']['plans']}/{game_uid}/plan.json")): return {"status" : "error", "info" : f"There is no locally default available plan for {game_uid}."}
    # Create new directory
    if not os.path.exists(server_path):
        os.makedirs(server_path, exist_ok=True)
    # Configure default settings and save plan as default
    default_plan['server_name'] = server_name
    with open(f'{server_path}/plan.json', 'w') as f:
        json.dump(default_plan, f)
    if "success" not in (config := consolidate_settings(user_settings=user_settings,plan=default_plan))['result']: return result
    with open(f'{server_path}/config.json', 'w') as f:
        json.dump(config['plan'], f)
    if "success" not in (result := generate_build_file(config['plan']))['status']: return result
    return configure_permissions(server_path=server_path)

def update_warcamp(game_uid,server_name):
    # Copy plan from /plans over default
    # Update config where possible (return highlighted change if something is missing)
    pass

def get_warcamp_config(game_uid,server_name):
    pass #modified_plan = get_local_plan_version(f"{config['path']['plans']}/{game_uid}/{server_name}/settings.json")

def modify_warcamp_config(user_settings):
    # game_uid = user_settings['game_uid']
    # server_name = user_settings['server_name']
    # # Get default config
    # default_plan = get_local_plan_version(f"{config['path']['plans']}/{game_uid}/plan.json")
    # modified_plan = get_local_plan_version(f"{config['path']['plans']}/{game_uid}/{server_name}/settings.json")
    pass

# MAIN - DEV TEST

if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_plans.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    logging.critical(update_latest_plans_from_repository())