#!/usr/bin/python3
import logging
from flask import Flask
from flask_restful import Api
# Import Peon Modules
from modules.api_v1 import *
from modules.servers import *
from modules.scheduler import *
from modules.shared import configure_logging
from modules import *
# Configure CORS (secure http/s requests)
from flask_cors import CORS
cors_allowed_headers = ["Content-Type", "api_key", "Authorization"]
cors_allowed_methods = ["GET", "POST", "DELETE", "PUT", "PATCH", "OPTIONS"]

# # Initialize Flask
app = Flask(__name__)
CORS(app, allow_headers=cors_allowed_headers, methods=cors_allowed_methods)
api_v1 = Api(app)

api_v1.add_resource(Orchestrator, "/api/v1/orchestrator")
api_v1.add_resource(Servers, "/api/v1/servers")
api_v1.add_resource(Server, "/api/v1/server/<string:action>/<string:server_uid>")
api_v1.add_resource(Plans, "/api/v1/plans")
api_v1.add_resource(Plan, "/api/v1/plan/<string:game_uid>")

# Start flask listener
if __name__ == "__main__":
    # Configure logging
    configure_logging()
    logging.debug("[START]")
    # Start the schedulers timer
    scheduler_tick()
    # load all registered servers into memory
    servers_get_all()
    # Start Orchestrator services
    logging.debug(app.run(host="0.0.0.0", port=5000, debug=False)) # Setting DEBUG=true will make timer trigger x2 # DEBUG LOGGING CAN BE ENABLED WITH THE `.env` ENTRY `DEV_MODE=enabled`
    logging.debug("[END]")
