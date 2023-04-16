import logging
from . import settings

def authorized(headers):
    api_key = settings['api']['key']
    auth = headers.get("X-Api-Key")
    if auth == api_key:
        return True
    else:
        logging.error("Failed Authorization for API call. key [{0}]".format(auth))
        return False