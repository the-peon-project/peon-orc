import logging
from . import settings
import os

def authorized(headers):
    api_key = os.environ.get("API_KEY", "Zu88Zu88")
    auth = headers.get("X-Api-Key")
    if auth == api_key:
        return True
    else:
        logging.error("Failed Authorization for API call. key [{0}]".format(auth))
        return False