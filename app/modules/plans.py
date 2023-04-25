#!/usr/bin/python3
import logging
import json
import yaml
import requests
import sys
import os
import shutil
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

def get_remote_plan_version(config_peon,game_uid):
    try:
        game_plan_url = config_peon['settings']['plan_url'].format(game_uid)
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

def get_required_settings(config_peon,game_uid,warcamp):
    if (plan := get_local_plan_definition(f"{config_peon['path']['servers']}/{game_uid}/{warcamp}/config.json")):  # type: ignore
        return ([key for key, value in plan['environment'].items() if value is None])
    else:
        return None

def consolidate_settings(config_peon,user_settings,plan): # Check exisiting config and update new config accordingly. If there is an unknown entity, throw an error.
    # CHECK IF ALL REQUIRED SETTINGS HAVE BEEN PROVIDED
    provided_settings = list(user_settings.keys())
    required_settings = get_required_settings(config_peon=config_peon,game_uid=plan['metadata']['game_uid'],warcamp=plan['metadata']['warcamp'])
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
    for port in config_warcamp['ports'][0]:
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
    for source, target in config_warcamp['volumes'].items(): mount_list.append(f"./{source}:{target}")
    # Custom file mount
    for source, target in config_warcamp['files'].items():
        if os.path.exists(f"{server_path}/{source}"):
            mount_list.append(f"./{source}:{target}")
    manifest['services']['server']['volumes']=mount_list
    try:
        with open(f"{server_path}/docker-compose.yml", "w") as f:
            yaml.dump(manifest, f, sort_keys=False, indent=4)
        return { "status" : "success" , "manifest" : manifest}
    except Exception as e:
        return { "status" : "error", "info" : f"Could not create the `docker-compose.yml` file. {e}" }
        

def configure_permissions(server_path): # chown & chmod on path
    try:
        for filename in os.listdir(server_path):
            filepath = os.path.join(server_path, filename)
            print(filepath)
            if os.path.isfile(filepath):
                os.chown(filepath, 1000, 1000)
                if any(filename.endswith(valid_scripts) for valid_scripts in ['server_start','init_custom']):
                    os.chmod(filepath, 0o755)
        return {"status" : "success"}
    except Exception as e:
        return {"status" : "error", "info" : f"Unable to configure permissions for server. {e}"}

# WARCAMP FUNCTIONS
def create_new_warcamp(config_peon,user_settings):
    game_uid=user_settings["game_uid"]
    if "warcamp" not in user_settings: user_settings['warcamp'] = get_warcamp_name()
    warcamp=user_settings['warcamp']
    server_path=f"{config_peon['path']['servers']}/{game_uid}/{warcamp}"
    # Check if there is already a plan in that directory
    try: 
        if (get_local_plan_definition(f"{server_path}/config.json")): return { "status" : "error" , "info" : f"There is already a config.json file for [{game_uid}] [{warcamp}]. Please run update on the game/server instead. (Can be added in a future release.)" }
    except:
        logging.debug("[create_warcamp] No pre-existing config found.")
    # Get default plan definition
    if not (plan := get_local_plan_definition(f"{config_peon['path']['plans']}/{game_uid}/plan.json")): return {"status" : "error", "info" : f"There is no local default plan for {game_uid}."}  # type: ignore
    # Create new game directory, if required
    if not os.path.exists(f"{config_peon['path']['servers']}/{game_uid}"):
        os.makedirs(f"{config_peon['path']['servers']}/{game_uid}", exist_ok=True)
    shutil.copytree(f"{config_peon['path']['plans']}/{game_uid}/", server_path)
    shutil.copy(f"{server_path}/plan.json",f"{server_path}/config.json")
    # Configure default settings and save plan as default
    if "warcamp" not in user_settings: user_settings['warcamp'] = get_warcamp_name()
    plan['metadata']['warcamp'] = user_settings['warcamp']
    if "success" not in (result := consolidate_settings(config_peon=config_peon,user_settings=user_settings,plan=plan))['status']: return result  # type: ignore
    with open(f'{server_path}/config.json', 'w') as f:
        json.dump(result['plan'], f, indent=4)
    if "success" not in (result := update_build_file(server_path=server_path,config_warcamp=result['plan']))['status']: return result  # type: ignore
    if "success" not in configure_permissions(server_path=server_path)['status']: return result
    return {"status" : "success", "game_uid" : f"{game_uid}", "warcamp" : f"{warcamp}"}

def update_warcamp(game_uid,warcamp):
    # Update config where possible (return highlighted change if something is missing)
    pass

def get_warcamp_config(config_peon,game_uid,warcamp,user_mode=True):
    config_warcamp_path=f"{config_peon['path']['servers']}/{game_uid}/{warcamp}/config.json"
    if os.path.exists(config_warcamp_path):
        with open(config_warcamp_path, "r") as f:
            config_warcamp = json.load(f)
        if user_mode:
            pass
        return {"status" : "success", "data" : config_warcamp }
    else:
        return { "status" : "error", "info" : "There does not appear to be a server at that path."}

# MAIN - DEV TEST

if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_plans.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    config_peon = json.load(open("/app/config.json", 'r'))
    user_settings={
        "game_uid"    : "vrising",
        "description" : "A V Rising server",
        "SERVER_NAME" : "countjugular",
        "WORLD_NAME"  : "townsville",
        "PASSWORD"    : "Zu88Zu88"
    }
    print(create_new_warcamp(config_peon=config_peon,user_settings=user_settings))
    # print(get_warcamp_config(config_peon=config_peon,game_uid='vrising',warcamp='mysticlake'))
