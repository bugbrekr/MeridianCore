"""
A microservice client importable. Abstracts the mess of connecting to a microservice
with basic token authentication.
"""

import msgpack
import requests

class Client:
    """
    Client class. Facilitates outgoing requests and authentication.
    """
    def __init__(self):
        pass