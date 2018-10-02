#!/usr/bin/env python
"""
    Troop-Client
    ------------
    Real-time collaborative Live Coding.

    - Troop is a real-time collaborative tool that enables group live
      coding within the same document. To run the client application it
      must be able to connect to a running Troop Server instance on
      your network. Running `python run-client.py` will start the process
      of connecting to the server by asking for a host and port (defaults
      are localhost and port 57890). 

    - Using other Live Coding Languages:
    
        Troop is designed to be used with FoxDot (http://foxdot.org) but
        is also configured to work with Tidal Cycles (http://tidalcycles.org).
        You can run this file with the `--mode` flag followed by "tidalcycles"
        to use the Tidal Cycles language. You can also use any other application
        that can accept code commands as strings via the stdin by specifying
        the path of the interpreter application, such as ghci in the case of
        Tidal Cycles, in place of the "tidalcycles" string when using the
        `--mode` flag.
"""

from src.__main__ import run_client

run_client()