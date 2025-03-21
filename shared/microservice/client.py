"""
A microservice client importable. Abstracts the mess of connecting to a microservice
with basic token authentication.
"""

import os
import re
import base64
import toml
import msgpack
import requests

class ServiceClient:
    """
    Service client class. Actually allows sending requests.
    """
    def __init__(self, host, service_name, port, auth_token, discover_methods=True):
        self._host = host
        self._service_name = service_name
        self._port = port
        self._auth_token = auth_token
        self._method_list = None
        if discover_methods:
            self._discover_methods()
    def _make_request(self, endpoint, method, data=None):
        response = requests.request(
            method,
            f"http://{self._host}:{self._port}{endpoint}",
            data=msgpack.dumps(data),
            headers={"Authorization": f"Bearer {self._auth_token}"},
            timeout=5
        ).content
        return msgpack.loads(response)
    def call(self, method, **kwargs):
        """
        Call a method with keyword arguments.
        """
        if isinstance(self._method_list, list):
            if method not in self._method_list:
                raise AttributeError(f"'{self._service_name}' service has no method '{method}'")
        response = self._make_request(
            "/call",
            "POST",
            {
                "method": method,
                "data": kwargs
            }
        )
        success = response.get("success")
        return (response.get("code"),
            success,
            response.get("data") if success else response.get("error")
        )
    def _add_method(self, method_name):
        def innermethod(**kwargs):
            return self.call(method_name, **kwargs)
        innermethod.__name__ = method_name
        setattr(self, method_name, innermethod)
    def _discover_methods(self):
        self._method_list = self._make_request("/list", "GET")
        for method in self._method_list:
            self._add_method(method)

class Client:
    """
    Client class. Facilitates outgoing requests and authentication.
    """
    def __init__(self, config_file="config/config.toml", access_tokens_file="config/access_tokens"):
        with open(config_file, encoding="utf-8") as f:
            config = toml.loads(f.read())
        self._host = config["service-client"].get("host", "127.0.0.1")
        self._access_tokens_file = access_tokens_file
        if not os.path.isfile(access_tokens_file):
            open(access_tokens_file, "w", encoding="utf-8").close()
        with open(access_tokens_file, encoding="utf-8") as f:
            access_tokens = [i.strip() for i in f.readlines()]
        self._accessible_services = {}
        for access_token in access_tokens:
            service, port, auth_token = self._parse_access_token(access_token)
            self._accessible_services[service] = (port, auth_token)
    def _parse_access_token(self, access_token):
        matches = re.match(
            r"([a-z][0-9]-[a-zA-Z0-9_-]+)\.([A-Za-z0-9+/=]+)\.([A-Za-z0-9_-]+)",
            access_token
        )
        service = matches.group(1)
        port = int.from_bytes(base64.b64decode(matches.group(2)))
        auth_token = matches.group(3)
        return service, port, auth_token
    def get_client(self, service):
        """
        Returns an instantiated ServiceClient.
        """
        if service not in self._accessible_services:
            raise KeyError("Service not accessible.")
        port, auth_token = self._accessible_services[service]
        return ServiceClient(self._host, service, port, auth_token)
    def call_service(self, service, method, **kwargs):
        """
        Directly call a service method without handling a ServiceClient.
        """
        if service not in self._accessible_services:
            raise KeyError("Service not accessible.")
        port, auth_token = self._accessible_services[service]
        return ServiceClient(self._host, service, port, auth_token, False).call(method, **kwargs)
