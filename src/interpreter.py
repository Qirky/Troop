"""
    Interpreter
    -----------

    Runs a block of FoxDot code. Designed to be overloaded
    for other language communication

"""

from config import *
import time

class Clock:
    def __init__(self):
        self.time = 0
        self.mark = time.time()
    def kill(self):
        return
    def reset(self):
        self.time = 0
        self.mark = time.time()
    def settime(self, t):
        self.time = t
    def get_bpm(self):
        return 60.0
    def now(self):
        now = time.time()
        self.time += now - self.mark
        self.mark = now
        return self.time

class Interpreter(Clock):
    lang     = None
    clock    = None
    def evaluate(self, string):
        return

class FoxDotInterpreter(Interpreter):
    def __init__(self):
        import FoxDot
        self.lang  = FoxDot
        self.clock = FoxDot.Clock
        self.counter = None

    def kill(self):
        self.clock.stop()

    def now(self):
        return self.clock.now()

    def get_bpm(self):
        return self.clock.bpm

    def settime(self, t):
        ''' Adds 1 second to the current time based the current bpm '''
        bpm   = float(self.get_bpm())
        if self.counter is None:
            self.counter = float(t) * (bpm / 60)
        else:
            self.counter += (bpm / 60)
        now   = float(self.now())
        if self.counter < 0.95 * now or self.counter > 1.05 * now:
            self.clock.time = self.counter
        return
            
    def evaluate(self, string):
        return self.lang.execute(string)


class SuperColliderInterpreter(Interpreter):
    def __init__(self):
        import OSC

        # Get password for Troop quark
        from getpass import getpass
        self.__password = getpass("Enter the password for your SuperCollider Troop Quark: ")

        # Connect to OSC client
        self.host = 'localhost'
        self.port = 57120
        self.lang = OSC.OSCClient()
        self.lang.connect((self.host, self.port))

        # Define a function to produce new OSC messages
        self.new_msg = lambda: OSC.OSCMessage()
        
    def evaluate(self, string):
        msg = self.new_msg()
        msg.setAddress("/troop")
        msg.append([self.__password, string])
        self.lang.send(msg)
        return

langtypes = { FOXDOT : FoxDotInterpreter,
              SUPERCOLLIDER : SuperColliderInterpreter }
