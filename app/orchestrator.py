from xmlrpc.client import Server
from flask import Flask
from flask_restful import Api
# Import Peon Modules
from api.api_v1 import ServerList, Server

# Initialize Flask
app = Flask(__name__)
api_v1 = Api(app)

api_v1.add_resource(ServerList, "/api/1.0/servers")
api_v1.add_resource(Server, "/api/1.0/servers/<int:id>")

# Start flask listener
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
