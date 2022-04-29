#!/usr/bin/python3
import logging
import traceback
import json
from pathlib import Path
import urllib.request
from .shell import execute_shell

root_path = "/root/peon"
plan_path = "{0}/plans".format(root_path)
plan_game_path = "{0}/games".format(plan_path)
plan_file_path = "{0}/plans.json".format(plan_path)


def get_latest_plans_list():
    logging.debug("Pulling latest list of plans.")
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/nox-noctua-consulting/peon-plans/master/plans.json", plan_file_path)


def plans_get_current():
    logging.debug("Getting current list of plans.")
    plan_file = Path(plan_file_path)
    if plan_file.is_file():
        return json.load(open(plan_file_path))
    else:
        try:
            get_latest_plans_list()
            return json.load(open(plan_file_path))
        except Exception as e:
            logging.error(traceback.format_exc())
            return {"error":"Could not get latest plans."}

def download_shared_plans():
    logging.debug("Downloading shared plans".format())
    url = "https://github.com/nox-noctua-consulting/peon-plans/archive/master.tar.gz"
    urllib.request.urlretrieve(
        url, "{0}/master.tar.gz".format(plan_path))
    execute_shell('''
    cd {0} && 
    rm -rf {0}/shared &&
    tar -xvf master.tar.gz &&
    cp -R peon-plans-master/shared . &&
    rm -rf peon-plans-master &&
    rm -rf master.tar.gz &&
    chown -R 1000:1000 shared
    '''.format(plan_path))


def download_game_plan(url):
    logging.info("Downloading game plan from {0}".format(url))
    urllib.request.urlretrieve(
        url, "{0}/master.tar.gz".format(plan_game_path))
    main_dir = execute_shell("cd {0} && tar -tvf master.tar.gz | grep drwx".format(
        plan_game_path))
    main_dir = (main_dir[0].split(" "))[-1]
    game_dir = (str(main_dir)).replace("-main/","")
    execute_shell ('''
        cd {0} && 
        rm -rf {1} && 
        tar -xvf master.tar.gz && 
        mv {2} {1} && 
        rm -rf master.tar.gz &&
        chown -R 1000:1000 {1}'''.format(plan_game_path,game_dir,main_dir)
        )

def get_plan_url(game_uid):
    plans = plans_get_current()
    error = "NOT-FOUND"
    for plan in plans:
        if plan["game_uid"] == game_uid:
            return plan["source"]
    return error
            

def get_plan(game_uid):
    logging.debug("Get plan for Game_UID [{0}]".format(game_uid))
    url = get_plan_url(game_uid)
    if url != "NOT-FOUND":
        download_game_plan(url)
        return "none"
    else:
        return "Game UID not found."

if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_actions_plans.log', filemode='a',
                        format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    print (get_plan('csgo'))