"""
A microservice server importable. Abstracts the mess of setting up a microservice with
basic token authentication.
"""

import functools
import toml
import msgpack
import bottle

class Server:
    """
    Server class. Handles incoming HTTP requests and authentication.
    """
    def __init__(self, config_file="config/config.toml"):
        with open(config_file, encoding="utf-8") as f:
            config = toml.loads(f.read())
        self.service_name = config.get("")
