#!/usr/bin/python3
from flask_restful import Resource, reqparse, abort, marshal, fields
from modules import servers, settings
from .servers import *
import logging
import traceback

# Schema For the Server Request JSON
serverFields = {
    "game_uid": fields.String,
    "servername": fields.String,
    "password": fields.String,
    "state": fields.String,
    "description": fields.String
}


class Server(Resource):
    def __init__(self):
        # Initialize The Flask Request Parser and add arguments as in an expected request
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("game_uid", type=str, location="json")
        self.reqparse.add_argument("servername", type=str, location="json")
        self.reqparse.add_argument("password", type=str, location="json")
        self.reqparse.add_argument("state", type=str, location="json")
        self.reqparse.add_argument("description", type=str, location="json")
        super(Server, self).__init__()

    # GET - Returns a single server object given a matching id
    def get(self, server_uid):
        logging.debug("APIv1 - Server Get")
        server = [server for server in servers if server_get_uid(
            server) == server_uid]
        if(len(server) == 0):
            abort(404)
        return{"server": marshal(server[0], serverFields)}

    # PUT - Given an id
    def put(self, server_uid):
        logging.debug("APIv1 - Server Put")
        server = [server for server in servers if server_get_uid(
            server) == server_uid]
        if len(server) == 0:
            abort(404)
        server = server[0]
        # Loop Through all the passed agruments
        args = self.reqparse.parse_args()
        for key, value in args.items():
            # Check if the passed value is not null
            if value is not None:
                # if not, set the element in the servers dict with the 'key' object to the value provided in the request.
                server[key] = value
                if key == "state":
                    if value == "start":
                        server_start(server_get_uid(server))
                    elif value == "stop":
                        server_stop(server_get_uid(server))
                    elif value == "restart":
                        server_stop(server_get_uid(server))
                        server_start(server_get_uid(server))
                if key == "description":
                    pass
        return{"server": marshal(server, serverFields)}
    # DELETE - Remove a server

    def delete(self, server_uid):
        logging.debug("APIv1 - Server Delete")
        server = [server for server in servers if server_get_uid(
            server) == server_uid]
        if(len(server) == 0):
            abort(404)
        server_uid = "{0}.{1}".format(
            server[0]["game_uid"], server[0]["servername"])
        server_stop(server_uid)
        server_delete(server_uid)
        servers_reload_current()
        return {"success": "Server {0} was deleted.".format(server_uid)}, 200


class Servers(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "game_uid", type=str, required=True, help="The PEON game id must be provided.", location="json")
        self.reqparse.add_argument(
            "servername", type=str, required=True, help="A custom server name must be provided.", location="json")
        self.reqparse.add_argument(
            "password", type=str, required=True, help="A custom server password must be provided.", location="json")
        self.reqparse.add_argument(
            "description", type=str, required=False, help="A server description can be provided", location="json")
        self.reqparse.add_argument(
            "settings", type=list, required=False, help="Settings data provided for the server", location="json")
    # GET - List all servers

    def get(self):
        logging.debug("APIv1 - Servers Get/List")
        servers_reload_current()
        return{"servers": [marshal(server, serverFields) for server in servers]}
    # POST - Create a server

    def post(self):
        logging.debug("APIv1 - Server Post/Create")
        args = self.reqparse.parse_args()
        server = {
            "game_uid": args["game_uid"],
            "servername": args["servername"],
            "password": args["password"],
            "description": args["description"],
            "settings" : args["settings"]
        }
        try:
            servers_reload_current()
            for serv in servers:
                if args["game_uid"] == serv["game_uid"] and args["servername"] == serv["servername"]:
                    return{"error": "Server already exists."}, 501
            if "settings" not in args.keys():
                args["settings"] = []
            server_create("{0}.{1}".format(
                args["game_uid"],args["servername"]), 
                args["settings"])
            servers.append(server)
            return{"server": marshal(server, serverFields)}, 201
        except Exception as e:
            logging.error(traceback.format_exc())
            return {"error": "Zer is a boog in ze code. Check the 'orc.log' for the traceback."}, 500
