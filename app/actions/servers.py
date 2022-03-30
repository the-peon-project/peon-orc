#!/usr/bin/python3
import logging
import docker

prefix = "peon.warcamp."

def server_start(server_uid):
    logging.info("Starting server [{0}]".format(server_uid))
    client = docker.from_env()
    container = client.containers.get("{0}{1}".format(prefix,server_uid))
    container.start()

def server_stop(server_uid):
    logging.info("Stopping server [{0}]".format(server_uid))
    client = docker.from_env()
    container = client.containers.get("{0}{1}".format(prefix,server_uid))
    container.stop()

# Start flask listener
if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/peon/DEV.peon.orc_actions_servers.log', filemode='a', format='%(asctime)s %(thread)d [%(levelname)s] - %(message)s', level=logging.DEBUG)
    server_start("csgo.server01")