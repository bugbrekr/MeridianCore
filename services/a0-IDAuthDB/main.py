"""
a0-IDAuthDB
"""

from shared.microservice import Server

server = Server()

@server.method
def test1():
    """
    test
    """
    return {"hi": "bye"}

server.run()
