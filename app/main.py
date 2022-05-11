#!/usr/bin/python3
import logging
#from xmlrpc.client import Server
from flask import Flask
from flask_restful import Api
# Import Peon Modules
from modules.api_v1 import *
from modules.servers import *

# Configure CORS (secure http/s requests)
from flask_cors import CORS
cors_allowed_headers=["Content-Type", "api_key", "Authorization"]
cors_allowed_methods=["GET","POST","DELETE","PUT","PATCH","OPTIONS"]

# Scheduler
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
def my_job(text):
    print(text)

# Initialize Flask
app = Flask(__name__)
CORS(app,allow_headers=cors_allowed_headers,methods=cors_allowed_methods)
api_v1 = Api(app)

api_v1.add_resource(Servers, "/api/1.0/servers")
api_v1.add_resource(Server, "/api/1.0/server/<string:action>/<string:server_uid>")
api_v1.add_resource(Plans, "/api/1.0/plans")
# api_v1.add_resource(Plan, "/api/1.0/plan/<string:game_uid>")

# Start flask listener
if __name__ == "__main__":
    sched = BlockingScheduler()
    sched.add_job(my_job, 'date', run_date=datetime(2022, 5, 11, 19, 38, 0), args=['text'])
    sched.start()

    servers_get_all()
    logging.basicConfig(filename='/var/log/peon/orc.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    logging.debug(app.run(host="0.0.0.0", port=5000, debug=False))
    