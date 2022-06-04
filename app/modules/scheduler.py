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

def get_schedule():
    if (Path(schedule_file)).exists():
        with open(schedule_file, 'r') as f:
            schedule = json.load(f)
        return schedule
    else:
        return []

def save_schedule(schedule):
    with open(schedule_file, 'w') as json_file:
        json.dump(schedule, json_file)

def scheduler_add_event(server_uid, epoch_time, action="stop"):
    schedule=get_schedule()
    schedule.append(dict({
        "server_uid" : server_uid,
        "time" : epoch_time,
        "action" : action
    }))
    save_schedule(schedule)
    return epoch_time

def scheduler_time_extend(server_uid, interval, action="stop"):
    now = datetime.today()
    data = re.split('(\d+)', interval)
    multiplier=int(data[1])
    granularity=data[2]
    if granularity.lower() == "d":
        event_time = now + relativedelta(days=multiplier)
    elif granularity.lower() == "h":
        event_time = now + relativedelta(hours=multiplier)
    elif granularity.lower() == "m":
        event_time = now + relativedelta(minutes=multiplier)
    elif granularity.lower() == "s":
        event_time = now + relativedelta(seconds=multiplier)
    else:
        return '0'
    epoch_time = int(time.mktime(event_time.timetuple()))
    return scheduler_add_event(server_uid, epoch_time, action)

def schedular_tick():
    now = int(time.mktime(datetime.today().timetuple()))
    print (now)
    schedule_changes=False
    schedule=get_schedule()
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
            new_schedule.append(dict(item)) # Drop actioned event from list (i.e. only save to come events)
    if schedule_changes:
        save_schedule(new_schedule)
    threading.Timer(interval, schedular_tick).start()


if __name__ == "__main__":
    output = scheduler_time_extend("vrising.countjugular", interval="2m", action="start")
    print (output)