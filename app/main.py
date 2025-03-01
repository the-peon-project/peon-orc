#!/usr/bin/python3
import logging
from flask import Flask
from flask_restful import Api
from werkzeug.serving import run_simple
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

# Configure logging first
configure_logging()
# Use logging instead of print for consistency
logging.info("[START]")

# Disable Flask default logging
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None

# # Initialize Flask
app = Flask(__name__)
app.logger.handlers = []  # Remove default handlers
app.logger.propagate = True  # Use root logger
CORS(app, allow_headers=cors_allowed_headers, methods=cors_allowed_methods)
api_v1 = Api(app)

api_v1.add_resource(Orchestrator, "/api/v1/orchestrator")
api_v1.add_resource(Servers, "/api/v1/servers")
api_v1.add_resource(Server, "/api/v1/server/<string:action>/<string:server_uid>")
api_v1.add_resource(Plans, "/api/v1/plans")
api_v1.add_resource(Plan, "/api/v1/plan/<string:game_uid>")

# Start flask listener
if __name__ == "__main__":
    # Start the schedulers timer
    scheduler_tick()
    # load all registered servers into memory
    servers_get_all()
    # Start Orchestrator services
    run_simple('0.0.0.0', 5000, app, use_reloader=False)
    logging.debug("[END]")
