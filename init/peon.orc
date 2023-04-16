#!/bin/bash
echo "##### Initialisation - START - $(date) #####"
# Check for docker socket
echo "Checking docker.sock availability."
if ! [ -e "/var/run/docker.sock" ]
then
    echo "The docker socket was not found. Please update the '.env' file's 'DOCKER_SOCKET_PATH=' to your hosts docker socket path."
fi
echo "##### Initialisation - END #####"
echo "##### Application - START #####"
echo "-> Starting PEON Orchestrator v$VERSION"
cd /app
python3 main.py # Start main program
echo "##### Application - END #####"