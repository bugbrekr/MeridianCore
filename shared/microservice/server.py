"""
A microservice server importable. Abstracts the mess of setting up a microservice with
basic token authentication.
"""

import os
import re
import toml
import bottle
import msgpack

class MethodError(Exception):
    """
    Custom error that's called internally when a method does `server.error()`
    """
    def __init__(self, code, message):
        self.code = code
        self.message = message

class HTTPErrorResponses:
    """
    Returns a MessagePack response for HTTP errors.
    """
    code_messages = {
        400: "Bad Request",
        401: "Unauthorized",
        402: "Payment Required",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        406: "Not Acceptable",
        408: "Request Timed Out",
        409: "Conflict",
        410: "Gone",
        411: "Length Required",
        412: "Precondition Failed",
        413: "Content Too Large",
        414: "URI Too Long",
        415: "Unsupported Media Type",
        416: "Range Not Satisfiable",
        417: "Expectation Failed",
        418: "I'm a teapot"
    }
    def _generate_error_response(self, code, message):
        success = code < 400
        response = {
            "success": success,
            "code": code
        }
        if not success:
            response["error"] = self.code_messages.get(code, "") if not message else message
        return response
    def error(self, code, message=None, set_status=True):
        """
        Returns a MessagePack response given a HTTP error code.
        """
        response = self._generate_error_response(code, message)
        if set_status:
            bottle.response.status = code
        return msgpack.dumps(response)
    def bottle_error_handler(self, e):
        """
        Handles errors directly from Bottle server.
        """
        bottle.response.add_header("Content-Type", "application/msgpack")
        code = int(e.status.split()[0])
        return self.error(code)

class Server:
    """
    Server class. Handles incoming requests and authentication.
    """
    def __init__(self, config_file="config/config.toml", auth_tokens_file="config/auth_tokens"):
        with open(config_file, encoding="utf-8") as f:
            config = toml.loads(f.read())
        self.auth_tokens_file = auth_tokens_file
        if not os.path.isfile(auth_tokens_file):
            open(auth_tokens_file, "w", encoding="utf-8").close()
        self.service_name = config["service"]["name"]
        self.port = config["service"]["port"]
        self.host = config["service"].get("host", "127.0.0.1")
        self.bottle_app = bottle.Bottle()
        self.bottle_app.route("/call", "POST", self._bottle_request)
        self._error = HTTPErrorResponses()
        self.bottle_app.default_error_handler = self._error.bottle_error_handler
        self.registered_methods = {}
    def method(self, func):
        """
        Decorator to register a method.
        """
        method_name = func.__name__
        self.registered_methods[method_name] = func
    def error(self, code, message=None):
        """
        Returns an error.
        `return server.error(404, "Not found")`
        """
        raise MethodError(code, message)
    def _authenticate_token(self, auth_token):
        with open(self.auth_tokens_file, encoding="utf-8") as f:
            auth_tokens = [i.strip() for i in f.readlines()]
        return auth_token in auth_tokens
    def _bottle_request(self):
        raw_data = bottle.request.body.read()
        bottle.response.add_header("Content-Type", "application/msgpack")
        if not isinstance(bottle.request.headers.get("Authorization"), str):
            return self._error.error(401, "Authorization header missing.")
        authorization_header = bottle.request.headers["Authorization"]
        match = re.match(r"^Bearer\s+([A-Za-z0-9\-_]+)$", authorization_header)
        if not match:
            return self._error.error(400, "Authorization header format incorrect.")
        is_authenticated = self._authenticate_token(match.group(1))
        if not is_authenticated:
            return self._error.error(403, "auth_token invalid.")
        try:
            request = msgpack.loads(raw_data)
        except (
            ValueError,
            msgpack.exceptions.BufferFull,
            msgpack.exceptions.ExtraData,
            msgpack.exceptions.FormatError,
            msgpack.exceptions.OutOfData,
            msgpack.exceptions.StackError,
            msgpack.exceptions.UnpackException
        ):
            return self._error.error(400, "Content not MessagePack format.")
        if not isinstance(request.get("method"), str) and request["method"] != "":
            return self._error.error(400, "method parameter must be type str and cannot be empty.")
        if not isinstance(request.get("data"), dict):
            return self._error.error(400, "data parameter must be type dict.")
        method_name = request["method"]
        if method_name not in self.registered_methods:
            return self._error.error(404, "Specified method does not exist.")
        method_func = self.registered_methods[method_name]
        try:
            response = method_func(**request["data"])
        except MethodError as e:
            return self._error.error(e.code, e.message)
        except TypeError as e:
            return self._error.error(400, str(e))
        except Exception as e:
            raise e from e
        if response is None:
            response = {}
        elif not isinstance(response, dict):
            response = {"output": response}
        try:
            return msgpack.dumps({
                "success": True,
                "code": 200,
                "data": response
            })
        except (ValueError, TypeError):
            return self._error.error(500, "Error while encoding response!")
    def run(self):
        """
        Runs the service server.
        """
        self.bottle_app.run(host=self.host, port=self.port, server="auto")
    def get_wsgi_app(self):
        """
        Get the WSGI app for deployment with other servers.
        """
        return self.bottle_app
