"""
    bin/interpreter.py
    ------------------

    Runs a block of FoxDot code. Designed to be overloaded
    for other language communication

"""
try:
    import FoxDot
except ImportError:
    print("ImportError: FoxDot not installed")

class Interpreter:
    def __call__(self, string):
        return FoxDot.execute(string)
    def quit(self):
        FoxDot.Clock.stop()
        FoxDot.Server.quit()
    
        
