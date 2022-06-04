#!/usr/bin/python3

# BUG: Double tick - change app.run(debug=True) to app.run(debug=False) in main.py
import time, threading

interval = 30 # Seconds

def schedular_tick():
    print(time.ctime())    
    threading.Timer(interval, schedular_tick).start()

