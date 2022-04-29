#!/usr/bin/python3
from flask_restful import Resource, reqparse, abort, marshal, fields
from modules import servers, settings, prefix
from .servers import *
from .plans import *
import logging
import traceback
import time

# Schema For the Server Request JSON
serverFields = {
    "game_uid": fields.String,
    "servername": fields.String,
    "container_state": fields.String,
    "server_state": fields.String,
    "description": fields.String
}

planFields = {
    "game_uid": fields.String,
    "title": fields.String,
    "logo": fields.String,
    "source": fields.String
}


def server_get(server_uid):
    try:
        server = server_get_server(client.containers.get(
            "{0}{1}".format(prefix, server_uid)))
        return{"server": marshal(server, serverFields)}, 200
    except Exception as e:
        logging.error(traceback.format_exc())
        return {"error": "There was an issue getting the server."}, 404


class Server(Resource):
    def __init__(self):
        # Initialize The Flask Request Parser and add arguments as in an expected request
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("game_uid", type=str, location="json")
        self.reqparse.add_argument("servername", type=str, location="json")
        self.reqparse.add_argument(
            "container_state", type=str, location="json")
        self.reqparse.add_argument("server_state", type=str, location="json")
        self.reqparse.add_argument("description", type=str, location="json")
        super(Server, self).__init__()

    # GET - Returns a single server object given a matching id
    def get(self, server_uid):
        logging.debug("APIv1 - Server Get")
        return server_get(server_uid)

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
                if key == "container_state":
                    if value == "start":
                        server_start(server_get_uid(server))
                    elif value == "stop":
                        server_stop(server_get_uid(server))
                    elif value == "restart":
                        server_stop(server_get_uid(server))
                        server_start(server_get_uid(server))
                    # Let the services have a short period to process state change
                    time.sleep(0.5)
                if key == "description":
                    server_update_description(server, server[key])
                server_get(server_uid)
        return{"server": marshal(server, serverFields)}, 200

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
        servers_get_all()
        return {"success": "Server {0} was deleted.".format(server_uid)}, 200


class Servers(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "game_uid", type=str, required=True, help="The PEON game id must be provided.", location="json")
        self.reqparse.add_argument(
            "servername", type=str, required=True, help="A custom server name must be provided.", location="json")
        self.reqparse.add_argument(
            "description", type=str, required=True, help="A server description can be provided", location="json")
        self.reqparse.add_argument(
            "settings", type=list, required=True, help="Settings data provided for the server. Can be an empty list.", location="json")
    # GET - List all servers

    def get(self):
        logging.debug("APIv1 - Servers Get/List")
        servers_get_all()
        return{"servers": [marshal(server, serverFields) for server in servers]}
    # POST - Create a server

    def post(self):
        logging.debug("APIv1 - Server Create")
        args = self.reqparse.parse_args()
        server = {
            "game_uid": args["game_uid"],
            "servername": args["servername"],
            "description": args["description"],
            "settings": args["settings"]
        }
        try:
            servers_get_all()
            for serv in servers:
                if args["game_uid"] == serv["game_uid"] and args["servername"] == serv["servername"]:
                    return{"error": "Server already exists."}, 501
            if "settings" not in args.keys():
                args["settings"] = []
            get_latest_plans_list()
            download_shared_plans()  # Pull latest shared files
            error = get_plan(serv["game_uid"])
            if error == "none":
                error = server_create("{0}.{1}".format(
                    args["game_uid"], args["servername"]),
                    args["description"],
                    args["settings"])
            if error == "none":
                servers.append(server)
                time.sleep(0.5)
                return server_get("{0}.{1}".format(args["game_uid"], args["servername"]))
            else:
                return{"error": error}, 501
        except Exception as e:
            logging.error(traceback.format_exc())
            return {"error": "Something bad happened. Check the logs for details. Please submit to (@peon devs) to improve error handling."}, 500


class Plans(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "game_uid", type=str, required=True, help="The PEON game id must be provided.", location="json")
        self.reqparse.add_argument(
            "title", type=str, required=True, help="A plan title must be provided", location="json")
        self.reqparse.add_argument(
            "logo", type=str, required=True, help="A plan logo must be provided", location="json")
        self.reqparse.add_argument(
            "source", type=str, required=True, help="The source files for the PEON plan must be provided.", location="json")
    # GET - List all plans

    def get(self):
        logging.debug("APIv1 - Plans Get/List")
        plans = plans_get_current()
        return{"plans": [marshal(plan, planFields) for plan in plans]}

    # PUT - Update the plans file
    def put(self):
        logging.debug("APIv1 - Plans update List")
        get_latest_plans_list()
        plans = plans_get_current()
        return{"plans": [marshal(plan, planFields) for plan in plans]}
