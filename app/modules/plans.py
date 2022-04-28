#!/usr/bin/python3
import logging
import traceback
import json
from pathlib import Path
import urllib.request
from modules import client, servers, prefix
from .shell import execute_shell

root_path = "/root/peon"
plan_file_path = "{0}/plans/plans.json".format(root_path)


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