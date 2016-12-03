"""

    threadserv.py
    -------------

    Server object used in receiver.py and server.py. Stops receiver.py
    import FoxDot and running a clock thread when importing from server.py

"""

import SocketServer
class ThreadedServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass
