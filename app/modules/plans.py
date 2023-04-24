#!/usr/bin/python3
import logging
import json
import requests
import sys
sys.path.insert(0,'/app')
from modules.github import *

config = json.load(open("/app/config.json", 'r'))

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

def download_latest_plans_from_repository(repo='github'): # On start (if empty) & on request
    if "github" in repo:
        return update_plans_from_github()
    else:
        return { "status" : "error", "info" : f"The repository [{repo}] is not yet supported." }

def get_remote_plan_version(game_uid):
    game_plan_url = config['settings']['plan_url'].format(game_uid)
    if (response := requests.get(game_plan_url)).status_code == 200:
        try:
            return (json.loads(response.content))['metadata']['version']
        except Exception as e:
            logging.warn(f"[get_remote_plan_version] Plan definition for [{game_uid}] not found at [game_plan_url].")
    return None

def get_local_plan_version(game_uid): # /home/peon/plans/{game_uid}
    pass

def copy_default_plan_to_server_path(game_uid,server_path): # /home/peon/plans/{game_uid}/{server_name}/plan.json
    pass

def consolidate_user_settings_with_config(server_path,user_settings): # /home/peon/plans/{game_uid}/{server_name}/settings.json
    pass

def generate_build_file(server_path,server_settings): # /home/peon/plans/{game_uid}/{server_name}/docker-compose.yml
    pass

def configure_permissions(server_path): # chown & chmod on path
    pass

def prepare_warcamp(user_settings,ignore_remote_plans=False):
    game_uid=user_settings["game_uid"]
    if (version_local := get_local_plan_version(game_uid)) in None:
        if (get_remote_plan_version(game_uid)) in None: return { "status" : "error", "info" : f"No plan for game_uid [{game_uid}] found." }
        else: version_local = '0.0.0'
    if not ignore_remote_plans:
        version_remote = get_remote_plan_version(game_uid)
        if 'remote' in identify_newest_version(version_local,version_remote) or '0.0.0' in version_remote:
            download_latest_plans_from_repository()
    server_path = f"/home/peon/servers/{game_uid}/{user_settings['server_name']}"
    if "success" not in (result := copy_default_plan_to_server_path(game_uid=game_uid,server_path=server_path))['status']: return result
    if "success" not in (result := consolidate_user_settings_with_config(server_path=server_path,user_settings=user_settings))['status']: return result
    if "success" not in (result := generate_build_file(server_path=server_path,server_settings=result))['status']: return result
    return configure_permissions(server_path=server_path)


if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_plans.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    logging.critical(get_remote_plan_version(game_uid='csgo2'))


# root_path = "/root/peon"
# plan_path = "{0}/plans".format(root_path)
# plan_game_path = "{0}/games".format(plan_path)
# plan_file_path = "{0}/plans.json".format(plan_path)


# def get_latest_plans_list():
#     logging.debug("Pulling latest list of plans.")
#     urllib.request.urlretrieve(
#         "https://raw.githubusercontent.com/the-peon-project/peon-warplans/master/plans.json", plan_file_path)


# def plans_get_current():
#     logging.debug("Getting current list of plans.")
#     plan_file = Path(plan_file_path)
#     if plan_file.is_file():
#         return json.load(open(plan_file_path))
#     else:
#         try:
#             get_latest_plans_list()
#             return json.load(open(plan_file_path))
#         except Exception:
#             logging.error(traceback.format_exc())
#             return {"error":"Could not get latest plans."}

# def download_game_plan(url):
#     logging.info("Downloading game plan from {0}".format(url))
#     urllib.request.urlretrieve(
#         url, "{0}/master.tar.gz".format(plan_game_path))
#     main_dir = execute_shell("cd {0} && tar -tvf master.tar.gz | grep drwx".format(
#         plan_game_path))
#     main_dir = (main_dir[0].split(" "))[-1]
#     game_dir = (str(main_dir)).replace("-main/","")
#     execute_shell ('''
#         cd {0} && 
#         rm -rf {1} && 
#         tar -xvf master.tar.gz && 
#         mv {2} {1} && 
#         rm -rf master.tar.gz &&
#         chown -R 1000:1000 {1}'''.format(plan_game_path,game_dir,main_dir)
#         )

# def get_plan_url(game_uid):
#     plans = plans_get_current()
#     error = "NOT-FOUND"
#     for plan in plans:
#         if plan["game_uid"] == game_uid:
#             logging.critical(plan)
#             return plan["plan_url"]
#     return error
            

# def get_plan_from_repo(game_uid):
#     logging.debug("Get plan for Game_UID [{0}]".format(game_uid))
#     url = get_plan_url(game_uid)
#     if url != "NOT-FOUND":
#         download_game_plan(url)
#         return {"response" : "OK"}
#     else:
#         return {"error" : "Game UID not found."}

# if __name__ == "__main__":
#     logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_actions_plans.log', filemode='a',
#                         format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
#     print (get_plan_from_repo('csgo'))