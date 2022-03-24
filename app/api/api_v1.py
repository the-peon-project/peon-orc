from flask import Flask
from flask_restful import Resource, Api, reqparse, abort, marshal, fields


# A List of Dicts to store all of the servers
servers = []

# Schema For the Server Request JSON
serverFields = {
    "id": fields.Integer,
    "game_uid": fields.String,
    "servername": fields.String,
    "password": fields.String,
    "state": fields.String
}

class Server(Resource):
    def __init__(self):
        # Initialize The Flask Request Parser and add arguments as in an expected request
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("game_uid", type=str, location="json")
        self.reqparse.add_argument("servername", type=str, location="json")
        self.reqparse.add_argument("password", type=str, location="json")
        self.reqparse.add_argument("state", type=str, location="json")
        super(Server, self).__init__()

    # GET - Returns a single server object given a matching id
    def get(self, id):
        server = [server for server in servers if server['id'] == id]
        if(len(server) == 0):
            abort(404)
        return{"server": marshal(server[0], serverFields)}

    # PUT - Given an id
    def put(self, id):
        print ("Do we even get here?")
        server = [server for server in servers if server['id'] == id]
        if len(server) == 0:
            abort(404)
        server = server[0]
        # Loop Through all the passed agruments
        args = self.reqparse.parse_args()
        for k, v in args.items():
            # Check if the passed value is not null
            if v is not None:
                # if not, set the element in the servers dict with the 'k' object to the value provided in the request.
                server[k] = v
        return{"server": marshal(server, serverFields)}

    def delete(self, id):
        server = [server for server in servers if server['id'] == id]
        if(len(server) == 0):
            abort(404)
        servers.remove(server[0])
        return 201


class ServerList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "game_uid", type=str, required=True, help="The PEON game id must be provided", location="json")
        self.reqparse.add_argument(
            "servername", type=str, required=True, help="A custom server name must be provided", location="json")
        self.reqparse.add_argument(
            "password", type=str, required=True, help="A custom server password must be provided", location="json")

    def get(self):
        return{"servers": [marshal(server, serverFields) for server in servers]}

    def post(self):
        args = self.reqparse.parse_args()
        server = {
            "id": servers[-1]['id'] + 1 if len(servers) > 0 else 1,
            "game_uid": args["game_id"],
            "servername": args["servername"],
            "password": args["password"]
        }
        servers.append(server)
        return{"server": marshal(server, serverFields)}, 201