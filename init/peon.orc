#!/bin/bash
echo "##### Initialisation - START - $(date) #####"
# Check for docker socket
echo "Checking docker.sock availability."
if ! [ -e "/var/run/docker.sock" ]
then
    echo "ERROR: The docker socket was not found. Please update the '.env' file's 'DOCKER_SOCKET_PATH=' to your hosts docker socket path."
    sleep 10
    exit 0
fi
version=" v$VERSION"
echo "##### Initialisation - END #####"
echo "##### Application - START #####"
echo "-> Starting PEON Orchestrator$version"
cd /app
python3 main.py # Start main program
echo "##### Application - END #####"