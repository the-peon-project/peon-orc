#!/usr/bin/python3
import logging
import docker

prefix = "peon.warcamp."

def server_start(client,serverid):
    logging.info("Starting server [{0}]".format(serverid))
    container = client.containers.get("{0}{1}".format(prefix,serverid))
    container.start()

def server_stop(client,serverid):
    logging.info("Stopping server [{0}]".format(serverid))
    container = client.containers.get("{0}{1}".format(prefix,serverid))
    container.stop()

# Start flask listener
if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_actions_servers.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    client = docker.from_env()
    server_start(client,"csgo.server01")