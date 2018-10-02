#!/usr/bin/env python

"""
    Troop-Server
    ------------

    The Troop Server runs on the local machine by default on port 57890.
    This needs to be running before connecting using the client application.
    See "run-client.py" for more information on how to connect to the
    server. 

"""
from src.__main__ import run_server

run_server()