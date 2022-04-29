#!/usr/bin/python3
import logging
#from xmlrpc.client import Server
from flask import Flask
from flask_restful import Api
# Import Peon Modules
from modules.api_v1 import *
from modules.servers import *

# Initialize Flask
app = Flask(__name__)
api_v1 = Api(app)

api_v1.add_resource(Servers, "/api/1.0/servers")
api_v1.add_resource(Server, "/api/1.0/server/<string:server_uid>")
api_v1.add_resource(Plans, "/api/1.0/plans")
# api_v1.add_resource(Plan, "/api/1.0/plan/<string:game_uid>")

# Start flask listener
if __name__ == "__main__":
    servers_get_all()
    logging.basicConfig(filename='/var/log/peon/orc.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    logging.debug(app.run(host="0.0.0.0", port=5000, debug=True))
    