"""
Test client
"""
# pylint: disable=no-member,

from shared.microservice import Client

client = Client()

# If service will get repeated calls
id_auth_db = client.get_client("a0-IDAuthDB")
id_auth_db.test1()
id_auth_db.test1()
id_auth_db.test1()

# OR

# If don't want to instantiate new class
client.call_service("a0-IDAuthDB", "test1")
