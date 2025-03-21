"""
a0-IDAuthDB
"""

from shared.microservice import Server

server = Server()

@server.method
def test1(test=None):
    """
    test
    """
    if test:
        server.error(499, "my custom error")
    return "hi"
server.run()
