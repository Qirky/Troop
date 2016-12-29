"""
    bin/interpreter.py
    ------------------

    Runs a block of FoxDot code. Designed to be overloaded
    for other language communication

"""
# Option 1: only requiring a clock

import time

class Clock:
    def __init__(self):
        self.time = time.time()
    def quit(self):
        return
    def now(self):
        self.time = time.time() - self.time
        return self.time

# Option 2: FoxDot

class FoxDotInterpreter:
    def __init__(self):
        import FoxDot
        self.lang = FoxDot
    def quit(self):
        self.lang.Clock.stop()
    def now(self):
        return self.lang.Clock.now()
    def evaluate(self, string):
        return self.lang.execute(string)

### Define

Interpreter = FoxDotInterpreter
    
        
