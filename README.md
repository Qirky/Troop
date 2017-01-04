# Troop v0.2
---
## Real-time collaborative live coding with FoxDot

Troop is a real-time collaborative tool that enables group live coding within the same document. There are two modes of use: local and remote. In local mode, code is executed on the client side and on the server side in remote mode. How you set up Troop is up to you and your preferences.

### Remote example

If all the connected users are using Troop and are all in the same room, it would make sense to use the remote mode and only execute code on the server, which should be on a machine (can be a client) dedicated to producing the sound. This ensures all sonic events are coordinated together in time and you only need to connect one machine to speakers.

### Local example

If you are playing with someone who is not in the same geographical area as you, it would make more sense for both machines to run the  code so that you can both hear and see the results. 

Prerequisites:

- [Python 2.7](https://www.python.org/downloads/release/python-2712/)
- [SuperCollider](http://supercollider.github.io/)
- [FoxDot](https://github.com/Qirky/FoxDot)

### Running Troop Server

#### Remote

Make sure you have FoxDot and SuperCollider installed - these are required to make sounds. Open `OSCFunc.scd` found in FoxDot's SCLang folder in SuperCollider and execute the code pressing Ctrl+Return; this will boot up the SuperCollider server and listen for messages from FoxDot.

Start the Troop Server by running the `run-server.py` Python file.

	python run-server.py --remote

You will be asked to enter a password. You can leave this blank if you wish - but make sure you are on a secure network if you do. Connecting clients will be required to enter the same password when connecting to the server. By default the server will run on port 57890 but this isn't always the case. Make a note of the address and port number so that Troop Clients can connect to the server and you're up and running!

**Warning:** All Python code sent from the Clients to Server is executed, so be careful when using public networks as you will then be susceptible to having malicious code run on your machine. Avoid using public networks and only give your server password to people you trust.

#### Local

	python run-server.py --local

### Running Troop Client

Run the `run-client.py` Python file as above. You will be asked for four things:

- The IP address of the Troop Server
- The port of the Troop Server
- A name you wish to be identified by while using Troop
- The password for the Troop Server

If you've connected successfully then you'll open a black text box. Just type in some Python and press Ctrl+Return to evaluate the block of code your cursor is in. If there are any other collaborators you should see coloured markers in the text displaying their names. You can even execute code they've written and vice versa.

There are no bells or whistles in the Troop editor: so there's currently no automatic bracketing, keyboard short-cuts, or syntax highlighting. To stop all current sound, type `Clock.clear()` and press Ctrl+Return to evaluate.  

---

#### Using other Live Coding Languages:
    
Troop is designed to be used with FoxDot (http://foxdot.org) but the `__call__` method of `interpreter.Interpreter` can be replaced to do other interesting things with the evaluated portions of code.
