#!/usr/bin/python3
from flask import request, send_file
from flask_restful import Resource, reqparse
from modules import prefix, settings
from .peon import get_warcamp_name
from .servers import *
from .plans import *
from .security import *
from .scheduler import *
import logging
import time
import shutil
import os

class Orchestrator(Resource):
    def __init__(self):
        # Initialize The Flask Request Parser and add arguments as in an expected request
        self.reqparse = reqparse.RequestParser()
        if request.is_json:
            self.args = request.json
        else:
            self.args = {}
        super(Orchestrator, self).__init__()

    # GET - Returns a single server object given a matching id
    def get(self):
        logging.info(f"APIv1 [GET] Orchestrator")
        if not authorized(request.headers): return "Not authorized", 401
        try:
            payload = {}
            version = os.environ.get("VERSION", "-.-.-")
            payload["version"] = version
            return payload, 200
        except Exception as e:
            logging.error(f"Failed to get Orchestrator information. {e}")
            return {"status" : "error" , "info" : "There was an issue getting the Orchestrator information."}, 404


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
        logging.info(f"APIv1 [GET] Server <{server_uid}>")
        if not authorized(request.headers): return "Not authorized", 401
        try:
            server = server_get_server(client.containers.get("{0}{1}".format(prefix, server_uid)))
            if action == "stats":
                server["stats"] = server_get_stats(server_uid)
            elif action == "save":
                file_path = server_download_files(server_uid)
                return send_file(file_path, as_attachment=True)
            return server, 200
        except Exception as e:
            logging.error(f"Failed to get server information. {e}")
            return {"status" : "error" , "info" : "There was an issue getting the server."}, 404

    # PUT - Runs an action on a server
    def put(self, action, server_uid):
        logging.info(f"APIv1 [PUT] server <{action}> <{server_uid}>")
        result = { "status" : "success"}
        clean_on_fail = False
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
            logging.debug("create.01. Check if there are preloaded server files.")
            if not os.path.isdir(self.args['server_path']): clean_on_fail = True
            logging.debug("create.02. Trigger [create_new_warcamp] with with settings.")
            if 'success' in (result := create_new_warcamp(config_peon=settings,user_settings=self.args))['status']: 
                if 'start_later' in self.args and self.args['start_later']:
                    logging.info("create.03. Server created successfully. No-start flag set.")
                    return {"status" : "success" , "info" : f"The server files for [{self.args['warcamp']}] were created, but the server was not started, in accordance with the provided settings."}, 200
                else:
                    logging.debug("create.03. Server created successfully.")
                    action = 'start'
        # UPDATE
        if action == "update":
            if 'mode' in self.args: mode = self.args['mode']
            else: mode = 'full'
            logging.debug("update.01. Running update sequence.")
            if (result := server_update(server_uid,mode.lower()))['status'] != "success": return result, 400
            else: return result, 200
        # START
        if action == "start":
            logging.debug("start.01. Check and configure server shutdown time.")
            if "response" not in (result := scheduler_stop_request(server_uid,self.args)): return result, 400
            logging.debug(f"start.02. Trigger the startup of the server.")
            result = server_start(server_uid)
        # STOP
        elif action == "stop":
            logging.debug("stop.01. Check if automated shutdown is being requested server shutdown time.")
            result = scheduler_stop_request(server_uid,self.args)
            if "response" in result and result["response"] == "NOW":
                logging.debug(f"[stop][02] Triggering server shutdown.")
                scheduler_remove_exisiting_stop(server_uid)
                result = server_stop(server_uid)
        # RESTART
        elif action == "restart":
            logging.debug("restart.01. Restarting server.")
            result = server_restart(server_uid)
        # DESCRIPTION
        elif action == "description":
            try:
                logging.debug(f"description.01. Updating the server description.")
                result = server_update_description(server_uid=server_uid, description=self.args["description"])
            except:
                return {"status" : "error" , "info" : "The description argument was incorrectly provided."}, 400
        elif action == "skip":
            logging.debug("skip.01. Skip additional actions requested.")
        else:
            if result['info']: info = result['info']
            else: info = f"Unsupported action [{action}]."
            return { "status" : "error" , "info" : info }, 404
        time.sleep(0.5) # Wait some time for the docker daemon to do some magic
        if "success" in result["status"]:
            logging.debug(f"Fetching the status of the server.")
            server = server_get_server(client.containers.get("{0}{1}".format(prefix, server_uid)))
            return server, 200
        else:
            if clean_on_fail:
                if 'noclean' in self.args and self.args['noclean']:
                    logging.info("Do not clean on failure flag was set.")
                else:
                    logging.warning(f"Removing server {server_uid} folder from filesystem.")
                    shutil.rmtree(self.args['server_path'])
            return result, 400

    # DELETE - Remove a server
    def delete(self, action, server_uid):
        logging.info(f"APIv1 [DEL] server <{action}> <{server_uid}>")
        if not authorized(request.headers): return "Not authorized", 401
        note = ""
        if action not in ["destroy","eradicate"]:
            return {"error" : "Incorrect action [{0}] provided".format(action)}, 404
        if action == "destroy":
            logging.debug(f"Removing the server container environment.")
            if 'success' not in ( result := server_delete(server_uid))['status']: return {"status" : "error", "info" : f"Failed to remove the server [{server_uid}].", "exception" : f"{result['exception']}"}, 404
            note = f"Server {server_uid} was removed. "
        if "eradicate" in self.args and self.args["eradicate"]:
            logging.debug(f"Removing the server & user data from the filesystem.")
            server_delete_files(server_uid)
            note = note + f"All files for {server_uid} will be purged from the server. This may take a few moments."
        return {"status" : "success", "info" : note}, 200

class Servers(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()

    # GET - List all servers
    def get(self):
        logging.info(f"APIv1 [GET] servers - list all servers")
        if not authorized(request.headers): return "Not authorized", 401
        servers = servers_get_all()
        return servers, 200
    
    def put(self):
        logging.info(f"APIv1 [PUT] servers - import")
        if not authorized(request.headers): return "Not authorized", 401
        servers_import()
        return servers_get_all(), 200

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
        logging.info(f"APIv1 [GET] plans")
        if not authorized(request.headers): return "Not authorized", 401
        if ( plans := get_plans_local(config_peon=self.config_peon)):
            return plans, 200
        return "There was an issue getting the local plans list.", 404

    # PUT - Update the plans file
    def put(self):
        logging.info(f"APIv1 [PUT] plans <update>")
        if not authorized(request.headers): return "Not authorized", 401
        #if ( plans := get_plans_remote(config_peon=self.config_peon)):
        old_plans = get_plans_local(settings)
        if 'success' not in ( result := update_latest_plans_from_repository())['status']:
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
        logging.info(f"APIv1 [GET] plans <{game_uid}>")
        if not authorized(request.headers): return "Not authorized", 401
        if ( settings := get_all_required_settings(config_peon=self.config_peon,game_uid=game_uid)): return settings, 200
        else: return f"Could not get the settings for [{game_uid}]" , 404
            
