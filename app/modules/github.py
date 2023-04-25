import logging
from git import Repo
import os
import sys
sys.path.insert(0,'/app')
from modules.shell import execute_shell

plan_path = '/home/peon/plans'
repo_url = 'https://github.com/the-peon-project/peon-warplans.git'

def get_plans_from_github():
    logging.debug(f'[get_plans_from_github] Pulling latest plans from [{repo_url}].')
    try:
        Repo.clone_from(repo_url, plan_path)
        return { "status" : "success" }
    except Exception as e:
        logging.error(f'[get_plans_from_github] Could not pull plans from [{repo_url}]. {e}')
        return { "status" : "error", "info" : f"{e}" }
    
def update_plans_from_github(force=False):
    if not os.listdir(plan_path): # Check if the plans currently exist
        logging.warn(f"[update_plans_from_github] No plans found. Downloading plans from [{repo_url}]")
        if "success" not in (result := get_plans_from_github()['status']): return result # type: ignore
    else: { "status" : "success" }
    try:
        logging.debug(f"[update_plans_from_github] Refreshing the plans from [{repo_url}]")
        # CORRECT SOLUTION [BROKEN]
        #repo = Repo(plan_path)
        #repo.remotes.origin.pull()
        # TEMP SOLUTION [START] - as python git is full of sh**
        if force:
            execute_shell(cmd_as_string=f'cd {plan_path} && git reset --hard && git pull')
        else:
            execute_shell(cmd_as_string=f'cd {plan_path} && git pull')
        # TEMP SOLUTION [END] - as python git is full of sh**
        return { "status" : "success" }
    except Exception as e:
        logging.error(f'[get_plans_from_github] Could not pull plans from [{repo_url}]. {e}')
        return { "status" : "error", "info" : f"{e}" }    

if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_github.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    update_plans_from_github()