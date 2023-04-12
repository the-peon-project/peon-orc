# BASE: Base image - Python (Debian + slim)
FROM python:3.11-slim-bullseye
# CONTAINER: Configuration
LABEL "com.peon.description"="Peon Orchestrator"
LABEL "maintainer"="Umlatt <richard@noxnoctua.com>"
# BRANDING: Copy branding into container
COPY ./media/banner /etc/motd
RUN echo "cat /etc/motd" >> /etc/bash.bashrc
# OS: Prepare the OS and middleware
RUN apt-get update
# DOCKER
RUN apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io
# PYTHON
COPY ./requirements.txt /app/requirements.txt
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip3 install --no-cache-dir --upgrade -r /app/requirements.txt
# DEBUG: Install tools for debugging
RUN apt-get -y install procps iputils-ping dnsutils vim
# APPLICATION
COPY ./app /app
WORKDIR /app
# Start application
CMD ["/bin/sh", "-c","python3 main.py >> /var/log/peon/orc.log 2>&1"]