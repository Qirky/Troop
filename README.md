# Troop v0.1
---
## Real-time collaborative live coding with FoxDot

Troop is a real-time collaborative tool that enables group live coding within the same document. Currently, code is only executed on the server-side (which may be running on the same machine as a client) but this may change in future. 

Prerequisites:

- [Python 2.7](https://www.python.org/downloads/release/python-2712/)
- [SuperCollider](http://supercollider.github.io/) (Server only)
- [FoxDot](https://github.com/Qirky/FoxDot) (Server only)

### Running Troop Server

Make sure you have FoxDot and SuperCollider installed - these are required to make sounds. Open `OSCFunc.scd` found in FoxDot's SCLang folder in SuperCollider and execute the code pressing Ctrl+Return; this will boot up the SuperCollider server and listen for messages from FoxDot.

Start the Troop Server by running the `run-server.py` Python file. Depending on your installation of Python you can do this by double-clicking it, or in the terminal with the following code:

	python run-server.py

By default the server will run on port 57890 but this isn't always the case. Make a note of the address and port number so that Troop Clients can connect to the server and you're up and running!

**Warning:** All Python code sent from the Clients to Server is executed, so be careful when using public networks as you will then be susceptible to having malicious code run on your machine. A password system will be introduced soon.

### Running Troop Client

Run the `run-client.py` Python file as above. You will be asked for three things:

- The IP address of the Troop Server
- The port of the Troop Server
- A name you wish to be identified by while using Troop

If you've connected successfully then you'll open a black text box. Just type in some Python and press Ctrl+Return to evaluate the block of code your cursor is in. If there are any other collaborators you should see coloured markers in the text displaying their names. You can even execute code they've written and vice versa.

There are no bells or whistles in the Troop editor: so there's currently no automatic bracketing, keyboard short-cuts, or syntax highlighting. To stop all current sound, type `Clock.clear()` and press Ctrl+Return to evaluate.  

---

#### Using other Live Coding Languages:
    
Troop is designed to be used with FoxDot (http://foxdot.org) but the `__call__` method of `interpreter.Interpreter` can be replaced to do other interesting things with the evaluated portions of code.