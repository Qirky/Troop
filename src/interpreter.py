"""
    Interpreter
    -----------

    Runs a block of FoxDot code. Designed to be overloaded
    for other language communication

"""
from subprocess import Popen
from subprocess import PIPE, STDOUT
from config import *
import sys
import time
import re

def compile_regex(kw):
    """ Takes a list of strings and returns a regex that
        matches each one """
    return re.compile(r"(?<![a-zA-Z.])(" + "|".join(kw) + ")(?![a-zA-Z])")

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
    re       = compile_regex([])
    stdout   = None
    def evaluate(self, string):
        return
    def stop_sound(self):
        return ""

class FoxDotInterpreter(Interpreter):
    def __init__(self):
        import FoxDot
        self.lang  = FoxDot
        self.clock = FoxDot.Clock
        self.counter = None
        try: self.keywords = list(FoxDot.get_keywords()) + list(FoxDot.SynthDefs)
        except AttributeError:
            # Old FoxDot version
            self.keywords = ['bytearray', 'PShuf', 'elif', 'set', 'help', 'vars',
                             'PAlt', 'not', 'unicode', 'memoryview', 'rMod',
                             'isinstance', 'PRange', 'except', 'rGet', 'dict',
                             'get_expanded_len', 'input', 'Mod', 'bin', 'return',
                             'format', 'repr', 'PDur', 'P', 'asStream', 'sorted',
                             'Div', 'False', 'PSine', 'list', 'iter', 'try', 'PZip',
                             'PStretch', 'modi', 'round', 'dir', 'cmp', 'Scale',
                             'Sub', 'Clock', 'PWhite', 'reduce', 'issubclass',
                             'Mul', '\\A\\s*@.+', 'locals', 'slice', 'for', 'reload',
                             'PZip2', 'sum', 'rDiv', 'P10', 'getattr', 'abs', 'print',
                             'import', 'True', 'None', 'hash', 'rSub', 'basestring',
                             'len', 'Server', 'frozenset', 'ord', 'PSq', 'super', 'zip',
                             'filter', 'range', 'staticmethod', 'LCM', 'or', 'lambda',
                             'Group', 'eval', 'sliceToRange', 'pow', 'float',
                             'EuclidsAlgorithm', 'Add', 'globals', 'divmod', 'enumerate',
                             'open', 'patternclass', 'from', 'linvar', 'Get', 'PNe',
                             'hex', 'PEq', 'long', 'next', 'chr', 'max_length', 'PTri',
                             'var', 'type', 'tuple', 'reversed', 'else', 'PPairs', 'with',
                             'hasattr', 'delattr', 'setattr', 'raw_input', 'PEuclid',
                             'Pvar', 'compile', 'while', 'str', 'property', 'def', 'and',
                             'rAdd', 'int', 'xrange', 'is', 'PRand', 'as', 'file', 'in',
                             'unichr', 'inf', 'any', 'if', 'Nil', 'min', 'self', 'when',
                             'execfile', 'id', 'complex', 'bool', 'group_modi', 'loop_pattern_func',
                             '__import__', 'map', 'all', 'rPow', 'max', 'object', 'callable',
                             'PStutter', 'BufferManager', 'Root', 'class', 'PStep',
                             'classmethod', 'Pow', 'PSum', 'karp', 'varsaw', 'bell',
                             'scratch', 'pulse', 'blip', 'pads', 'rave', 'donk', 'saw',
                             'orient', 'creep', 'growl', 'marimba', 'dub', 'arpy', 'ambi',
                             'viola', 'quin', 'crunch', 'noise', 'bass', 'dab', 'dirt',
                             'twang', 'swell', 'pluck', 'glass', 'soprano', 'charm', 'spark',
                             'bug', 'squish', 'zap', 'snick', 'play', 'ripple',
                             'fuzz', 'lazer', 'klank', 'nylon', 'soft', 'scatter']

        self.re = compile_regex(self.keywords)

    def kill(self):
        self.clock.stop()

    def stop_sound(self):
        return "Clock.clear()"

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

    def stop_sound(self):
        return "s.freeAll"
        
    def evaluate(self, string):
        msg = self.new_msg()
        msg.setAddress("/troop")
        msg.append([self.__password, string])
        self.lang.send(msg)
        return

class TidalInterpreter(Interpreter):
    def __init__(self):
        self.lang = Popen(['ghci'], shell=False, universal_newlines=True,
                       stdin=PIPE, stdout=PIPE, stderr=STDOUT)

        self.lang.stdin.write("import Sound.Tidal.Context\n")
        self.lang.stdin.write(":set -XOverloadedStrings\n")
        self.lang.stdin.write("(cps, getNow) <- bpsUtils\n")

        d_vals = range(1,10)
        
        for n in d_vals:
            self.lang.stdin.write("(d{}, t{}) <- superDirtSetters getNow\n".format(n, n))

        self.lang.stdin.write("let hush = mapM_ ($ silence) [d1,d2,d3,d4,d5,d6,d7,d8,d9]\n")

        self.keywords  = ["d{}".format(n) for n in d_vals]
        self.keywords += ["\$", "#", "hush"] # add string regex?
        self.re = compile_regex(self.keywords)

    def evaluate(self, string):
        # prints to console -- maybe have the author or each eval?

        self.lang.stdin.write(":{\n"+string+"\n:}\n")

        self.lang.stdout.seek(0,2)      # Doesn't give us the real end -- threading the issue?
        buf_end = self.lang.stdout.tell()
        self.lang.stdout.seek(0)

        print self.lang.stdout.read(buf_end)
        
        return

    def stop_sound(self):
        return "hush"

    def kill(self):
        self.lang.communicate()
        self.lang.kill()        

langtypes = { FOXDOT        : FoxDotInterpreter,
              TIDAL         : TidalInterpreter,
              SUPERCOLLIDER : SuperColliderInterpreter }
