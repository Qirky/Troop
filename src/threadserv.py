"""

    threadserv.py
    -------------

    Server object used in receiver.py and server.py. Stops receiver.py
    import FoxDot and running a clock thread when importing from server.py

"""

try:
    import socketserver
except ImportError:
    import SocketServer as socketserver

class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass
