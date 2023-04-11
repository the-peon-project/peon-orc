#!/usr/bin/python3

# BUG: Double tick - change app.run(debug=True) to app.run(debug=False) in main.py
import logging
import time, threading
from pathlib import Path
import json
import re
from datetime import datetime
from dateutil.relativedelta import *
from modules import schedule_file
from modules.servers import server_start, server_stop, server_restart

interval = 30 # Seconds

def schedule_read_from_disk():
    if (Path(schedule_file)).exists():
        with open(schedule_file, 'r') as f:
            schedule = json.load(f)
        return schedule
    else:
        return []

def schedule_write_to_disk(schedule):
    with open(schedule_file, 'w') as json_file:
        json.dump(schedule, json_file)

def schedule_add_event(server_uid, epoch_time, action="stop"):
    try:
        schedule=schedule_read_from_disk()
        schedule.append(dict({
            "server_uid" : server_uid,
            "time" : epoch_time,
            "action" : action
        }))
        schedule_write_to_disk(schedule)
        return { "response" : "Added scheduled event." }
    except:
        return { "error" : f"An error occured when scheduling the [{action}] event." }

def add_delta(start_time,interval):
    data = (re.findall('(\d+)(\w)', interval))[0]
    if len(data) != 2:
        return { "error" : f"Invalid input. Expected 2 values, got {len(data)}. e.g 10m" }
    multiplier=int(data[0])
    granularity=data[1]
    if granularity.lower() == "d":
        event_time = start_time + relativedelta(days=multiplier)
    elif granularity.lower() == "h":
        event_time = start_time + relativedelta(hours=multiplier)
    elif granularity.lower() == "m":
        event_time = start_time + relativedelta(minutes=multiplier)
    elif granularity.lower() == "s":
        event_time = start_time + relativedelta(seconds=multiplier)
    else:
        return { "error": "Invalid time interval. Options are (d)ays,(h)ours,(m)inutes,(s)econds. e.g. 5h" }
    return { "response" : event_time }

def schedule_add_timeout_event(server_uid, interval, action="stop"):
    now = datetime.today()
    result = add_delta(now,interval)
    if "response" in result:
        epoch_time = int(time.mktime(result["response"].timetuple()))
        return schedule_add_event(server_uid, epoch_time, action)
    else: return result

def scheduler_change_event(list_index, epoch_time):
    schedule=schedule_read_from_disk()
    schedule[list_index]["time"] = epoch_time
    schedule_write_to_disk(schedule)
    return { "response" : "Changed scheduled date/time." }

def scheduler_delete_event(list_index):
    schedule=schedule_read_from_disk()
    del schedule[list_index]
    schedule_write_to_disk(schedule)
    return { "response" : "Removed scheduled event." }

def scheduler_tick():
    now = int(time.mktime(datetime.today().timetuple()))
    schedule_changes=False
    schedule=schedule_read_from_disk()
    new_schedule=[]
    # Process the schedule
    for item in schedule:
        if int(item["time"]) <= now:
            if item["action"] == "start":
                server_start(item["server_uid"])
            elif item["action"] == "stop":
                server_stop(item["server_uid"])
            elif item["action"] == "restart":
                server_restart(item["server_uid"])
            schedule_changes=True
        else:
            new_schedule.append(dict(item)) # Drop actioned event from list (i.e. only save 'to come' events)
    if schedule_changes:
        schedule_write_to_disk(new_schedule)
    threading.Timer(interval, scheduler_tick).start()

def scheduler_remove_exisiting_stop(server_uid):
    schedules = schedule_read_from_disk()
    new_schedule = []
    for item in schedules:
        if item["server_uid"] == server_uid and item["action"] == "stop":
            logging.debug(f"Removing {item} from schedule.")
        else:
            new_schedule.append(item)
    schedule_write_to_disk(new_schedule)

def scheduler_stop_request(server_uid,args):
    result = { "response" : "NOW" }
    if "interval" in args and args["interval"] != None:
        scheduler_remove_exisiting_stop(server_uid)
        result = schedule_add_timeout_event(server_uid,args["interval"])
    if "epoch_time" in args and args["epoch_time"] != None:
        if re.search("^[0-9]{10}$", args["epoch_time"]): # Check that it appears to be a valid Epoch number
            scheduler_remove_exisiting_stop(server_uid)
            result = schedule_add_event(server_uid,args["epoch_time"])
        else:
            result = { "error" : "Non-epoch time value provided for scheduler" }
    return result
    
if __name__ == "__main__":
    output = schedule_add_timeout_event("vrising.countjugular", interval="2m", action="start")
    print (output)