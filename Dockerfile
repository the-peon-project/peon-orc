# Base image debian bullseye slim
FROM python:3.9-slim-bullseye
# Install python requirements
COPY ./requirements.txt /app/requirements.txt
# Update pip and install required python modules
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip3 install --no-cache-dir --upgrade -r /app/requirements.txt
# Install tools for 'ps'
RUN apt-get update && apt-get -y install procps ssh 
# Copy application files into container
COPY ./app /app
# Start the app called api
CMD ["python3", "/app/orchestrator.py"]