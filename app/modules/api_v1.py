#!/usr/bin/python3
from flask import request
from flask_restful import Resource, reqparse, abort, marshal, fields
from modules import servers, settings, prefix
from .servers import *
from .plans import *
from .security import *
import logging
import traceback
import time

# Schema For the Server Request JSON
serverFields = {
    "game_uid": fields.String,
    "servername": fields.String,
    "container_state": fields.String,
    "server_state": fields.String,
    "server_config" : fields.String,
    "description": fields.String
}

planFields = {
    "game_uid": fields.String,
    "title": fields.String,
    "logo": fields.String,
    "source": fields.String
}

class Server(Resource):
    def __init__(self):
        # Initialize The Flask Request Parser and add arguments as in an expected request
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("game_uid", type=str, location="json")
        self.reqparse.add_argument("servername", type=str, location="json")
        self.reqparse.add_argument("container_state", type=str, location="json")
        self.reqparse.add_argument("server_state", type=str, location="json")
        self.reqparse.add_argument("description", type=str, location="json")
        self.reqparse.add_argument("eradicate", type=str, location="json")
        super(Server, self).__init__()

    # GET - Returns a single server object given a matching id
    def get(self, action, server_uid):
        logging.debug("APIv1 - Server Get - [{0}]".format(action))
        if not authorized(request.headers): return {"error" : "Not authorized."}, 401
        try:
            server = server_get_server(client.containers.get(
                "{0}{1}".format(prefix, server_uid)))
            if action == "stats":
                server["stats"] = server_get_stats(server_uid)
                serverFieldsWithStats = serverFields.copy()
                serverFieldsWithStats["stats"] = fields.String
                return{"server": marshal(server, serverFieldsWithStats)}, 200
            return{"server": marshal(server, serverFields)}, 200
        except Exception as e:
            logging.error(traceback.format_exc())
            return {"error": "There was an issue getting the server."}, 404

    # PUT - Given an id
    def put(self, action, server_uid):
        logging.info(
            "APIv1 - Server {0} - Action {1}".format(server_uid, action))
        if not authorized(request.headers): return {"error" : "Not authorized."}, 401
        try:
            server = server_get_server(client.containers.get(
                "{0}{1}".format(prefix, server_uid)))
        except Exception as e:
            logging.error(traceback.format_exc())
            return {"error": "The server [0] is inaccessible. Is the name valid?".format(server_uid)}, 404
        if action == "start":
            server_start(server_uid)
        elif action == "stop":
            server_stop(server_uid)
        elif action == "restart":
            server_restart(server_uid)
        elif action == "description":
            try:
                server_update_description(
                    server, (self.reqparse.parse_args())["description"])
            except:
                return {"error": "The description argument was incorrectly provided."}, 404
        else:
            return {"error": "Unsupported action [{0}].".format(action)}, 404
        time.sleep(0.5)
        server = server_get_server(client.containers.get(
            "{0}{1}".format(prefix, server_uid)))
        return{"server": marshal(server, serverFields)}, 200

    # DELETE - Remove a server
    def delete(self, action, server_uid):
        logging.debug("APIv1 - Server Delete")
        if not authorized(request.headers): return {"error" : "Not authorized."}, 401
        note = ""
        if action not in ["destroy","eradicate"]:
            return {"error" : "Incorrect action [{0}] provided".format(action)}, 404
        if action == "destroy":
            try:
                server_get_server(client.containers.get(
                    "{0}{1}".format(prefix, server_uid)))
            except Exception as e:
                logging.error(traceback.format_exc())
                return {"error": "The server {0} is inaccessible. Is the name valid?".format(server_uid)}, 404
            server_stop(server_uid)
            server_delete(server_uid)
            servers_get_all()
            note = "Server {0} was removed."
        args = self.reqparse.parse_args()
        if "eradicate" in args:
            if args["eradicate"] == "True":
                server_delete_files(server_uid)
                note = note + "All files for {0} have been removed."
        return {"success": note.format(server_uid)}, 200


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
        if not authorized(request.headers): return {"error" : "Not authorized."}, 401
        servers_get_all()
        return{"servers": [marshal(server, serverFields) for server in servers]}
    # POST - Create a server

    def post(self):
        logging.debug("APIv1 - Server Create")
        if not authorized(request.headers): return {"error" : "Not authorized."}, 401
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
            error = get_plan(args["game_uid"])
            if error == "none":
                error = server_create("{0}.{1}".format(
                    args["game_uid"], args["servername"]),
                    args["description"],
                    args["settings"])
            if error == "none":
                servers.append(server)
                time.sleep(0.5)
                return server_get_server(client.containers.get(
                    "{0}{1}.{2}".format(prefix, args["game_uid"],args["servername"])))
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
        if not authorized(request.headers): return {"error" : "Not authorized."}, 401
        plans = plans_get_current()
        return{"plans": [marshal(plan, planFields) for plan in plans]}

    # PUT - Update the plans file
    def put(self):
        logging.debug("APIv1 - Plans update List")
        if not authorized(request.headers): return {"error" : "Not authorized."}, 401
        get_latest_plans_list()
        plans = plans_get_current()
        return{"plans": [marshal(plan, planFields) for plan in plans]}
