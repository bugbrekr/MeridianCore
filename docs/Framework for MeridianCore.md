# Framework for MeridianCore

This specific document gives the a rather low-level (just package level, not actually low-level) description of how MeridianCore works.

### Microservices, APIs and Frontends.
So, to make life either complex or organized (we'll know soon), the backend is separated into "layers":
 - Layer **Z** - Usually represents an actual data source.
 - Layers **A** & **B** - Microservices that connect directly to the data source. This is a "trusted layer"*.
 - Layers **C** & **D** - Client-facing APIs, meant to be exposed publicly. **Must have good authentication and security.**
 - Layer **E** - Actual frontends and clients. They usually implement the authentication for connecting with layers C & D.

*more about trusted layer in [inter-service communication](#Inter-service-Communication).
### Inter-service Communication
We will use a custom MessagePack-based protocol over HTTP for inter-microservice authentication and micro-auth (I just made that up) for authentication.
We will call this protocol micro-prot. cuz its micro and its a protocol.

Here are some rules that each service will follow:
  1. Communication must take place only between consecutive layer classes and they must flow only upwards (only **E** to **A**). So one-way inter-layer, not intra-layer. This is for organisation and better security.
  2. Layers **A** & **B** must use micro-auth for incoming requests.
  Layers **C** & **D** will have to use micro-auth for outgoing requests to layer **A** & **B**.
  1. Layers **C** & **D** MUST (in most cases) implement user-facing authentication by using **A**-series microservices.

With the above rules, an example flow of requests would look like this:
```
(e0-LibraryKiosk) <---> (c0-LibraryKioskAPI) <---> (a0-BooksDB)
                  http                       <---> (a1-RFIDAuthDB)
                                           micro-prot
```

The below would be an incorrect implementation
```
(e0-LibraryKiosk) <---> (a0-BooksDB)
                  <---> (a1-RFIDAuthDB)
                micro-prot
```
because **C**-series services enforce authentication. This implementation would mean exposing **A**-series services to the public, which is a massive security hole.

Layers **A** & **B** are "trusted layers". This means, other than a simple token based auth ([micro-auth](#micro-auth)), there are no other security features.

**FAQs:**\
Q: Why do layers **B** and **D** exist if **A** and **C** are their respective twins?\
A: To let more complex service interactions. Let's say we have all the required layer **A** services to achieve a task, but we want to group them together and add some more functionality to serve our task better. Then we create a layer **B** service that uses those layer **A** services. Something similar for layer **D** too.

### micro-auth
It's an absolutely simple authentication system that's meant to be used in communication between layers **A**, **B**, **C** and **D**.\
The idea is to have a config file in each service that includes tokens which have (a) a port number and (b) an auth token embedded in the token. The port number is of the service server, and the auth token is to authenticate with said server.

Here is how a token is produced.
```python
import base64
import secrets

service_name = "RFIDAuthDB"
port = 40123
auth_token = secrets.token_hex(16)

encoded_port = base64.b64encode(port.to_bytes(2)).decode() # nLs=
encoded_service_name = base64.b64encode(service_name.encode()).decode() # UkZJREF1dGhEQg==

token = f"{encoded_service_name}.{encoded_port}.{auth_token}"
# UkZJREF1dGhEQg==.nLs=.9ad0390ca49c850cd3e9a30a6a5f7974
```

and this `token` will be distributed to ONE service (by including in its config file) that needs to talk to this service. This way, just by reading the config file, the service knows it has access to so and so services and all the information it needs to communicate with them, all the while maintaining basic security.

### micro-prot
Super simple MessagePack-based protocol for inter-microservice communication.\
Every request and response is encoded with MessagePack (chosen for versatility and fast serialisation & deserialisation) before sending over the network. Below are example structures for a request and response (shown in JSON).

**Request:**
```json
{
    "call": "<method_name to call>",
    "data": {
        "arg1": "param1",
        "arg2": "param2",
        ...
    }
}
```

**Response:**
```json
{
    "call": "<method_name called>",
    "code": 201,
    "success": true,
    "error": "Error message. (exists only if success is false)",
    "data": {
        "arg1": "param1",
        "arg2": "param2",
        ...
    }
}
```

**Note on `code` in response:**\
The response `code` mimics the utility of HTTP response codes. In fact, their format is also the same:
> 1xx - Information\
> 2xx - Success\
> 3xx - No idea yet.\
> 4xx - Client error\
> 5xx - A very bad server error, is definitely reported in the logs.

Anyways, these codes will be documented in-detail in a separate document, later.