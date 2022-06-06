#!/usr/bin/python3

# BUG: Double tick - change app.run(debug=True) to app.run(debug=False) in main.py
import time, threading
from pathlib import Path
import json
import re
from datetime import datetime
from dateutil.relativedelta import *
from modules.servers import server_start, server_stop, server_restart

interval = 30 # Seconds
schedule_file="/root/peon/servers/schedule.json"

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
    schedule=schedule_read_from_disk()
    schedule.append(dict({
        "server_uid" : server_uid,
        "time" : epoch_time,
        "action" : action
    }))
    schedule_write_to_disk(schedule)
    return { "status" : "success", "response" : "Added scheduled event." }

def add_delta(start_time,interval):
    data = re.split('(\d+)', interval)
    if len(data) != '2':
        return { "status" : "error", "response" : f"Invalid input. Expected 2 values, got {len(data)}. e.g 10m" }
    multiplier=int(data[1])
    granularity=data[2]
    if granularity.lower() == "d":
        event_time = start_time + relativedelta(days=multiplier)
    elif granularity.lower() == "h":
        event_time = start_time + relativedelta(hours=multiplier)
    elif granularity.lower() == "m":
        event_time = start_time + relativedelta(minutes=multiplier)
    elif granularity.lower() == "s":
        event_time = start_time + relativedelta(seconds=multiplier)
    else:
        return { "status" : "error", "response" : "Invalid time interval. Options are (d)ays,(h)ours,(m)inutes,(s)econds. e.g. 5h" }
    return { "status" : "success", "response" : event_time }

def schedule_add_timeout_event(server_uid, interval, action="stop"):
    now = datetime.today()
    response = add_delta(now,interval)
    if response["status"] == "success":
        epoch_time = int(time.mktime(response["data"].timetuple()))
        return schedule_add_event(server_uid, epoch_time, action)
    else: return response

def scheduler_change_event(list_index, epoch_time):
    schedule=schedule_read_from_disk()
    schedule[list_index]["time"] = epoch_time
    schedule_write_to_disk(schedule)
    return { "status" : "success", "response" : "Changed scheduled date/time." }

def scheduler_delete_event(list_index):
    schedule=schedule_read_from_disk()
    del schedule[list_index]
    schedule_write_to_disk(schedule)
    return { "status" : "success", "response" : "Removed scheduled event." }

def schedular_tick():
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
    threading.Timer(interval, schedular_tick).start()


if __name__ == "__main__":
    output = schedule_add_timeout_event("vrising.countjugular", interval="2m", action="start")
    print (output)