#!/usr/bin/env python3

"""
    Troop-Server
    ------------

    The Troop Server runs on the local machine by default on port 57890.
    This needs to be running before connecting using the client application.
    See "run-client.py" for more information on how to connect to the
    server.

"""

from argparse import ArgumentParser
from src.server import TroopServer
from getpass import getpass

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", help="Specify a port to use (default is 57890, auto-increments when multiple instances are running.)", default=57890, type=int)
    parser.add_argument("-P", "--password", help="Set a password. If not specified, you will be prompted for it.")
    parser.add_argument("-d", "--debug", help="Run the server in debug mode.", default=False, action='store_true')
    parser.add_argument("-l", "--log", help="Turn the logging on. The logs will be saved to the 'logs' directory.", default=False, action='store_true')
    parser.add_argument("-H", "--hub", help="Create a public Troop server via the Troop Hub Service.", default=False, action='store_true')
    args = parser.parse_args()

    if args.password is None:
        password = getpass("Password (leave blank for no password): ")
    else:
        password = args.password

    try:
        if args.hub:
            from src.hub import HubClient
            myServer = HubClient(password=password, host='127.0.0.1')
        else:
            myServer = TroopServer(password=password, port=args.port, debug=args.debug, log=args.log)
        myServer.start()
    except KeyboardInterrupt:
        # Exit cleanly on Ctrl + c
        pass
