#!/usr/bin/python3
import logging
from flask import Flask
from flask_restful import Api
import time
# Import Peon Modules
from modules.api_v1 import *
from modules.servers import *
from modules.scheduler import *
from modules import *
# Configure CORS (secure http/s requests)
from flask_cors import CORS
cors_allowed_headers = ["Content-Type", "api_key", "Authorization"]
cors_allowed_methods = ["GET", "POST", "DELETE", "PUT", "PATCH", "OPTIONS"]


# Initialize Flask
app = Flask(__name__)
CORS(app, allow_headers=cors_allowed_headers, methods=cors_allowed_methods)
api_v1 = Api(app)

api_v1.add_resource(Servers, "/api/1.0/servers")
api_v1.add_resource(Server, "/api/1.0/server/<string:action>/<string:server_uid>")
api_v1.add_resource(Plans, "/api/1.0/plans")
# api_v1.add_resource(Plan, "/api/1.0/plan/<string:game_uid>")

# Start flask listener
if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/orc.log', filemode='a',
                        format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    logging.debug("[START]")
    # Check for DEV mode (contents of the /dev dir are ignored by the docker build, but can be used in development)
    dev_mode()
    # Verify that the orchestrator has access to the underlying host
    authorized = "NOK"
    while authorized != 'OK':
        try:
            authorized = execute_shell("ssh 172.20.0.1 -p 22222 echo 'OK'")[0]
        except:
            logging.error(
                "############################## Orchestrator not authorised!!! ##############################")
            time.sleep(5)
    # Start the schedulers timer
    scheduler_tick()
    # load all registered servers into memory
    servers_get_all()
    # Start Orchestrator services
    logging.debug(app.run(host="0.0.0.0", port=5000, debug=False)) # Setting DEBUG=true will make timer trigger x2
    logging.debug("[END]")
