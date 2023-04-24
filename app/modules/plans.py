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
    
def update_latest_plans_from_repository(repo='github', force=True): # On start (if empty) & on request
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
def get_local_plan(file_path):
    try: 
        if os.path.isfile(file_path):
            with open(file_path) as json_file:
                game_plan = json.load(json_file)    
        return game_plan
    except Exception as e:
        logging.warn(f"[get_game_plan_from_file] The plan definition file [{file_path}] was not found. {e}")
    return None

def generate_build_file(server_path,server_settings): # /home/peon/plans/{game_uid}/{server_name}/docker-compose.yml
    pass

def configure_permissions(server_path): # chown & chmod on path
    pass

# WARCAMLP FUNCTIONS

def create_warcamp(user_settings):
    game_uid=user_settings["game_uid"]
    server_name=user_settings["server_name"]
    
    if not (default_plan := get_local_plan_version(f"{config['path']['plans']}/{game_uid}/")): return {"status" : "error", "info" : f"There is no locally available plan for {game_uid}."}

    default_plan['server_name'] = user_settings['server_name']
    default_plan['server_name'] = user_settings['server_name']


    # Specify the destination directory where you want to copy the file to
    destination_directory = '/path/to/destination'

    # Create the destination directory if it does not already exist
    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)

    # Use shutil.copy2 to copy the file to the destination directory
    
    
    
    
    
    
    
    default_plan = get_local_plan_version(f"{config['path']['plans']}/{game_uid}/plan.json")
    modified_plan_path = f"{config['path']['plans']}/{game_uid}/{server_name}/settings.json"
    
    # Check for local customised plan file
    if modified_plan: modified_plan_version = modified_plan['metadata']['version']
    else: modified_plan_version = '0.0.0'   
    # Check for local default plan file
    if default_plan: default_plan_version = default_plan['metadata']['version']
    else: default_plan_version = '0.0.0'
    # Check for 
    
    
    # If remote is newer than local, download
    server_path = f"/home/peon/servers/{game_uid}/{user_settings['server_name']}"
    if "success" not in (result := copy_default_plan_to_server_path(game_uid=game_uid,server_path=server_path))['status']: return result
    if "success" not in (result := consolidate_user_settings_with_config(server_path=server_path,user_settings=user_settings))['status']: return result
    if "success" not in (result := generate_build_file(server_path=server_path,server_settings=result))['status']: return result
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