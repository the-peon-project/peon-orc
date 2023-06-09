#!/usr/bin/python3
from flask import request
from flask_restful import Resource, reqparse
from modules import prefix, settings
from .peon import get_warcamp_name
from .servers import *
from .plans import *
from .security import *
from .scheduler import *
import logging
import traceback
import time
import shutil

class Server(Resource):
    def __init__(self):
        # Initialize The Flask Request Parser and add arguments as in an expected request
        self.reqparse = reqparse.RequestParser()
        if request.is_json:
            self.args = request.json
        else:
            self.args = {}
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
        server_uid_parts = server_uid.split('.')
        self.args['game_uid'] = server_uid_parts[0]
        if len(server_uid_parts) < 2:
            if 'create' not in action:
                return {"status" : "error", "info" : f"For the requested action [{action}] a warcamp name is required. You only provided [{server_uid}]" }, 400
            else:
                self.args['warcamp'] = get_warcamp_name()
                server_uid=f"{self.args['game_uid']}.{self.args['warcamp']}"
        else:
            self.args['warcamp'] = server_uid_parts[1]
        self.args['server_path']=f"{settings['path']['servers']}/{self.args['game_uid']}/{self.args['warcamp']}"
        # CREATE
        if action == "create":
            clean_on_fail = False
            if not os.path.isdir(self.args['server_path']): clean_on_fail = True
            if 'success' not in (result := create_new_warcamp(config_peon=settings,user_settings=self.args))['status']:  # type: ignore
                if clean_on_fail:
                    shutil.rmtree(self.args['server_path'])
                return self.args, 400
            if 'start_later' in self.args and self.args['start_later']: return result, 200
            else:
                action = 'start'
        if action == "start":
            if "response" not in (result := scheduler_stop_request(server_uid,self.args)): return result, 400 # type: ignore
            result = server_start(server_uid)
        # STOP
        elif action == "stop":
            result = scheduler_stop_request(server_uid,self.args)
            if "response" in result and result["response"] == "NOW":
                scheduler_remove_exisiting_stop(server_uid)
                result = server_stop(server_uid)
        # RESTART
        elif action == "restart":
            result = server_restart(server_uid)
        # DESCRIPTION
        elif action == "description":
            try:
                result = server_update_description(server_uid=server_uid, description=self.args["description"])
            except:
                return {"status" : "error" , "info" : "The description argument was incorrectly provided."}, 400
        else:
            return {"status" : "error" , "info" : "Unsupported action [{0}].".format(action)}, 404
        time.sleep(0.5) # Wait some time for the docker daemon to do some magic
        if "status" in result:
            server = server_get_server(client.containers.get("{0}{1}".format(prefix, server_uid)))
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
            if 'success' not in ( result := server_delete(server_uid))['status']: return {"status" : "error", "info" : f"Failed to remove the server [{server_uid}].", "exception" : f"{result['exception']}"}, 404 # type: ignore
            note = "Server {0} was removed. "
        if "eradicate" in self.args and self.args["eradicate"] == "True":
            server_delete_files(server_uid)
            note = note + "All files for {0} have been removed."
        return {"status" : "success", "info" : note.format(server_uid)}, 200

class Servers(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        
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
        #if ( plans := get_plans_remote(config_peon=self.config_peon)): # type: ignore
        old_plans = get_plans_local(settings)
        if 'success' not in ( result := update_latest_plans_from_repository())['status']: # type: ignore
            return result, 404
        new_plans = get_plans_local(settings)
        differences = {}
        for new_dict in new_plans:
            game_uid = new_dict['game_uid']
            found = False
            for old_dict in old_plans:
                if old_dict['game_uid'] == game_uid:
                    found = True
                    break
            if not found:
                differences[game_uid] = new_dict
        configure_plan_permissions()
        return { "new_recipies" : differences }, 200

class Plan(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.config_peon = json.load(open("/app/config.json", 'r'))
    
    def get(self,game_uid):
        logging.debug("APIv1 - Plan - Get settings")
        if not authorized(request.headers): return "Not authorized", 401
        if ( settings := get_all_required_settings(config_peon=self.config_peon,game_uid=game_uid)): return settings, 200 # type: ignore
        else: return f"Could not get the settings for [{game_uid}]" , 404
            
