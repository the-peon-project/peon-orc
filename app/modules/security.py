import logging

api_key = "my-super-secret-api-key"

def authorized(headers):
    auth = headers.get("X-Api-Key")
    if auth == api_key:
        return True
    else:
        logging.error("Failed Authorization for API call. key [{0}]".format(auth))
        return False