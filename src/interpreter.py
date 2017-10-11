"""
    Interpreter
    -----------

    Runs a block of FoxDot code. Designed to be overloaded
    for other language communication

"""
from __future__ import absolute_import
from .config import *

from subprocess import Popen
from subprocess import PIPE, STDOUT
from datetime import datetime

import sys
import re
import time
import threading

DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

def compile_regex(kw):
    """ Takes a list of strings and returns a regex that
        matches each one """
    return re.compile(r"(?<![a-zA-Z.])(" + "|".join(kw) + ")(?![a-zA-Z])")

SEPARATOR = ":"; _ = " %s " % SEPARATOR

def colour_format(text, colour):
    return '<colour="{}">{}</colour>'.format(colour, text)

## dummy interpreter

class DummyInterpreter:
    def __init__(self, *args, **kwargs):
        self.re={}
    def evaluate(self, *args, **kwargs):
        pass
    def stdout(self, *args, **kwargs):
        pass
    def kill(self, *args, **kwargs):
        pass
    def print_stdin(self, string, name=None, colour="White"):
        """ Handles the printing of the execute code to screen with coloured
            names and formatting """
        # Split on newlines
        string = [line.strip() for line in string.split("\n") if len(line.strip()) > 0]
        if len(string) > 0:
            name = str(name)
            print(colour_format(name, colour) + _ + string[0])
            # Use ... for the remainder  of the  lines
            n = len(name)
            for i in range(1,len(string)):
                print(colour_format("." * n, colour) + _ + string[i])
        return
    def stop_sound(self):
        return ""
    @staticmethod
    def format(string):
        return string
    
class Interpreter(DummyInterpreter):
    lang     = None
    clock    = None
    re       = {"tag_bold": compile_regex([]), "tag_string": string_regex}
    stdout   = None
    def __init__(self, path):
        self.lang = Popen([path], shell=True, universal_newlines=True,
                          stdin=PIPE,
                          stdout=PIPE,
                          stderr=STDOUT)

    def evaluate(self, string, *args, **kwargs):
        """ Sends a string to the stdin and prints the text to the console """
        # Print to console
        self.print_stdin(string, *args, **kwargs)
        # Write to stdin
        try:
            self.lang.stdin.write(self.format(string))
        except Exception as e:
            stdout(e, string)
        # Read stdout (wait 0.1 seconds)
        threading.Thread(target=self.stdout).start()
        return

    def stdout(self):
        """ Waits 0.1 seconds then reads the stdout from the self.lang process """
        if self.lang.stdout is not None:
            try:
                # Wait 0.1 sec
                time.sleep(0.1)
                # Go to the end of the stdout buffer
                self.lang.stdout.seek(0,2)
                # Get the end of the buffer
                buf_end = self.lang.stdout.tell()
                # Go back
                self.lang.stdout.seek(0)
                # Read to end of buffer
                text = self.lang.stdout.read(buf_end)
                # Print to console
                print(text)
                # Return length of text (useful for nonzero tests)
                return len(text)
            except IOError:
                return 0

    def kill(self):
        """ Stops communicating with the subprocess """
        self.lang.communicate()
        self.lang.kill() 

    

class CustomInterpreter:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    def __call__(self):
        return Interpreter(*self.args, **self.kwargs)

class FoxDotInterpreter(Interpreter):
    def __init__(self):
        import FoxDot

        self.lang  = FoxDot

        try:

            self.keywords = list(FoxDot.get_keywords()) + list(FoxDot.SynthDefs) + ["play"]

        except AttributeError:

            self.keywords = ['>>']

        self.re["tag_bold"] = compile_regex(self.keywords)

    def kill(self):
        self.evaluate("Clock.stop()")

    def stop_sound(self):
        return "Clock.clear()"
            
    def evaluate(self, *args, **kwargs):
        """ Sends code to FoxDot instance and prints any error text """
        Interpreter.print_stdin(self, *args, **kwargs)

        response = self.lang.execute(args[0], verbose=False)

        if response is not None:

            if response.startswith("Traceback"):

                print(response)
        
        return


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

    def stop_sound(self):
        return "s.freeAll"
        
    def evaluate(self, *args, **kwargs):
        Interpreter.evaluate(self, *args, **kwargs)
        msg = self.new_msg()
        msg.setAddress("/troop")
        msg.append([self.__password, string])
        self.lang.send(msg)
        return

class TidalInterpreter(Interpreter):
    def __init__(self):
        # Start haskell interpreter
        Interpreter.__init__(self, 'ghci')

        # Import Tidal and set the cps
        self.lang.stdin.write("import Sound.Tidal.Context\n")
        self.lang.stdin.write(":set -XOverloadedStrings\n")
        self.lang.stdin.write("(cps, getNow) <- bpsUtils\n")

        # Not always necessary but some versions of windows need setting d1-9
        d_vals = range(1,10)
        
        for n in d_vals:
            self.lang.stdin.write("(d{}, t{}) <- superDirtSetters getNow\n".format(n, n))

        # Define hush

        self.lang.stdin.write("let hush = mapM_ ($ silence) [d1,d2,d3,d4,d5,d6,d7,d8,d9]\n")

        # Set any keywords e.g. d1 and $

        self.keywords  = ["d{}".format(n) for n in d_vals]
        self.keywords += ["\$", "#", "hush"] # add string regex?

        self.re["tag_bold"] = compile_regex(self.keywords)

        # Wait until ghci finishes printing to terminal

        while self.stdout() > 0:

            pass
    
    @staticmethod
    def format(string):
        """ Used to formant multiple lines in haskell """
        return ":{\n"+string+"\n:}\n"

    def stop_sound(self):
        """ Triggers the 'hush' command using Ctrl+. """
        return "hush"       

langtypes = { FOXDOT        : FoxDotInterpreter,
              TIDAL         : TidalInterpreter,
              SUPERCOLLIDER : SuperColliderInterpreter }
