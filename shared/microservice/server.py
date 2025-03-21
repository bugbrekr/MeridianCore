"""
A microservice server importable. Abstracts the mess of setting up a microservice with
basic token authentication.
"""

import json
import functools
import bottle

class Server:
    """
    Server class. Handles incoming HTTP requests and authentication.
    """
    def __init__(self, service, token_file="config/tokens"):
        pass
