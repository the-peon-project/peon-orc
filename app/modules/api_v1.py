#!/usr/bin/python3
from flask import request
from flask_restful import Resource, reqparse
from modules import prefix
from .servers import *
from .plans import *
from .security import *
from .scheduler import *
import logging
import traceback
import time

class Server(Resource):
    def __init__(self):
        # Initialize The Flask Request Parser and add arguments as in an expected request
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("game_uid", type=str, location="json")
        self.reqparse.add_argument("servername", type=str, location="json")
        self.reqparse.add_argument("description", type=str, location="json")
        self.reqparse.add_argument("eradicate", type=str, location="json")
        self.reqparse.add_argument("interval", type=str, location="json")
        self.reqparse.add_argument("epoch_time", type=str, location="json")
        super(Server, self).__init__()

    # GET - Returns a single server object given a matching id
    def get(self, action, server_uid):
        logging.debug("APIv1 - Server Get - [{0}]".format(action))
        if not authorized(request.headers): return "Not authorized", 401
        try:
            server = server_get_server(client.containers.get(
                "{0}{1}".format(prefix, server_uid)))
            if action == "stats":
                server["stats"] = server_get_stats(server_uid)
            return server, 200
        except Exception as e:
            logging.error(f"[API-Server-GET] Failed to get server information. {e}")
            return {"status" : "error" , "info" : "There was an issue getting the server."}, 404

    # PUT - Runs an action on a server
    def put(self, action, server_uid):
        logging.info("APIv1 - Server {0} - Action {1}".format(server_uid, action))
        result = { "status" : "success"}
        if not authorized(request.headers): return "Not authorized", 401
        try:
            args=self.reqparse.parse_args()
        except:
            args= {}
            logging.debug("[API-Server-PUT] No arguments passed")
        if action == "create":
            # TODO - Implement server create
            
            action = "start"
            return "Server create function is not yet implemented", 501
        else:
            try:
                server = server_get_server(client.containers.get("{0}{1}".format(prefix, server_uid)))
            except Exception as e:
                logging.error(traceback.format_exc())
                return {"status" : "error" , "info" : f"The server [{server_uid}] is inaccessible. Is the name valid? {e}" }, 404
        if action == "start":
            result = scheduler_stop_request(server_uid,args)
            if "status" in result:
                result = server_start(server_uid)
        elif action == "stop":
            result = scheduler_stop_request(server_uid,args)
            if "status" in result and result["status"] == "NOW":
                scheduler_remove_exisiting_stop(server_uid)
                result = server_stop(server_uid)
        elif action == "restart":
            server_restart(server_uid)
        elif action == "description":
            try:
                server_update_description(server, (self.reqparse.parse_args())["description"])
            except:
                return {"status" : "error" , "info" : "The description argument was incorrectly provided."}, 400
        else:
            return {"status" : "error" , "info" : "Unsupported action [{0}].".format(action)}, 404
        time.sleep(0.5)
        server = server_get_server(client.containers.get("{0}{1}".format(prefix, server_uid)))
        if "status" in result:
            return server, 200
        else:
            return result, 400

    # DELETE - Remove a server
    def delete(self, action, server_uid):
        logging.debug("APIv1 - Server Delete")
        if not authorized(request.headers): return "Not authorized", 401
        note = ""
        if action not in ["destroy","eradicate"]:
            return {"error" : "Incorrect action [{0}] provided".format(action)}, 404
        if action == "destroy":
            try:
                server_get_server(client.containers.get(
                    "{0}{1}".format(prefix, server_uid)))
            except Exception as e:
                logging.error(traceback.format_exc())
                return {"status" : "error" , "info" : f"The server {server_uid} is inaccessible. Is the name valid? <{e}>"}, 404
            server_stop(server_uid)
            server_delete(server_uid)
            note = "Server {0} was removed."
        args = self.reqparse.parse_args()
        if "eradicate" in args and args["eradicate"] == "True":
            server_delete_files(server_uid)
            note = note + "All files for {0} have been removed."
        return {"success": note.format(server_uid)}, 200


class Servers(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "game_uid", type=str, required=True, help="The PEON game id must be provided.", location="json")
        self.reqparse.add_argument(
            "servername", type=str, required=False, help="A custom server name must be provided.", location="json")
        self.reqparse.add_argument(
            "description", type=str, required=False, help="A server description can be provided", location="json")
    # GET - List all servers
    def get(self):
        logging.debug("APIv1 - Servers Get/List")
        if not authorized(request.headers): return "Not authorized", 401
        servers = servers_get_all()
        return servers, 200

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
        self.config_peon = json.load(open("/app/config.json", 'r'))
    # GET - List all plans

    def get(self):
        logging.debug("APIv1 - Plans Get/List")
        if not authorized(request.headers): return "Not authorized", 401
        if ( plans := get_plans_local(config_peon=self.config_peon)): # type: ignore
            return plans, 200
        return "There was an issue getting the local plans list.", 404

    # PUT - Update the plans file
    def put(self):
        logging.debug("APIv1 - Plans update List")
        if not authorized(request.headers): return "Not authorized", 401
        if ( plans := get_plans_remote(config_peon=self.config_peon)): # type: ignore
            return plans, 200
        return "There was an issue getting the local plans list.", 404

class Plan(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.config_peon = json.load(open("/app/config.json", 'r'))
    
    def get(self,game_uid):
        logging.debug("APIv1 - Plan - Get settings")
        if not authorized(request.headers): return "Not authorized", 401
        if ( settings := get_all_required_settings(config_peon=self.config_peon,game_uid=game_uid)): return settings, 200 # type: ignore
        else: return f"Could not get the settings for [{game_uid}]" , 404
            
