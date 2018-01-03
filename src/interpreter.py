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

try:
    broken_pipe_exception = BrokenPipeError
except NameError:  # Python 2
    broken_pipe_exception = IOError

import sys
import re
import time
import threading
import io

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

    def get_block_of_code(self, text, index):
        """ Returns the start and end line numbers of the text to evaluate when pressing Ctrl+Return. """

        # Get start and end of the buffer
        start, end = "1.0", text.index("end")
        lastline   = int(end.split('.')[0]) + 1

        # Indicies of block to execute
        block = [0,0]        
        
        # 1. Get position of cursor
        cur_x, cur_y = index.split(".")
        cur_x, cur_y = int(cur_x), int(cur_y)
        
        # 2. Go through line by line (back) and see what it's value is
        
        for line in range(cur_x, 0, -1):
            if not text.get("%d.0" % line, "%d.end" % line).strip():
                break

        block[0] = line

        # 3. Iterate forwards until we get two \n\n or index==END
        for line in range(cur_x, lastline):
            if not text.get("%d.0" % line, "%d.end" % line).strip():
                break

        block[1] = line

        return block
    
    def evaluate(self, string, *args, **kwargs):
        self.print_stdin(string, *args, **kwargs)
        return

    def start(self):
        return self
    
    def stdout(self, *args, **kwargs):
        pass
    
    def kill(self, *args, **kwargs):
        pass
    
    def print_stdin(self, string, name=None, colour="White"):
        """ Handles the printing of the execute code to screen with coloured
            names and formatting """
        # Split on newlines
        string = [line.replace("\n", "") for line in string.split("\n") if len(line.strip()) > 0]
        if len(string) > 0 and name is not None:
            name = str(name)
            print(colour_format(name, colour) + _ + string[0])
            # Use ... for the remainder  of the  lines
            n = len(name)
            for i in range(1,len(string)):
                sys.stdout.write(colour_format("." * n, colour) + _ + string[i])
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
    filetype = ".txt"
    def __init__(self, path):

        if exe_exists(path.split()[0]):

            self.path = path

        else:

            raise ExecutableNotFoundError("'{}' is not a valid executable. Using Dummy Interpreter instead.".format(path))


    def start(self):

        self.lang = Popen(self.path, shell=True, universal_newlines=True,
                          stdin=PIPE,
                          stdout=PIPE,
                          stderr=STDOUT)

        return self

    def write_stdout(self, string):
        self.lang.stdin.write(self.format(string))
        self.lang.stdin.flush()

    def evaluate(self, string, *args, **kwargs):
        """ Sends a string to the stdin and prints the text to the console """
        # Print to console
        self.print_stdin(string, *args, **kwargs)
        # Write to stdin
        try:
            self.write_stdout(string)
        except Exception as e:
            stdout("Error in {}.evaluate()".format(self.__class__.__name__))
            stdout(e, string)
        # Read stdout (wait 0.1 seconds)
        threading.Thread(target=self.stdout).start()
        return

    def stdout(self):
        """ Reads the stdout from the self.lang process """
        if self.lang.stdout is None:
            return 0

        size = 0
        for stdout_line in iter(self.lang.stdout.readline, ""):
            size = len(stdout_line)
            sys.stdout.write(stdout_line)

        return size

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
    filetype=".py"
    path = "python -m FoxDot --pipe"

    def __init__(self):

        # 1. Try importing directly

        try:
            # Try importing from install

            try:

                import FoxDot

            except ImportError:

                # Import locally if not found

                from . import FoxDot

            self.lang = FoxDot

            self.imported = True

            try:

                self.keywords = list(FoxDot.get_keywords()) + list(FoxDot.SynthDefs) + ["play"]

            except AttributeError:

                self.keywords = ['>>']

            self.re["tag_bold"] = compile_regex(self.keywords)

        except (ImportError, FileNotFoundError):
            
            Interpreter.__init__(self, self.path)

            self.imported = False

            self.keywords = ['classmethod', 'Clock', 'rFloorDiv', 'any', 'type', 'dict', 'max_length', 
                             'sorted', 'staticmethod', 'or', 'loop_pattern_method', 'format', 'super', 
                             'globals', 'rXor', 'inf', 'PTree', 'isinstance', 'callable', 'Scale', 'PRange', 
                             'Div', 'PRand', 'pattern_depth', 'unicode', 'chr', '__import__', 'next', 'Or', 
                             'EuclidsAlgorithm', 'FloorDiv', 'memoryview', 'setattr', 'sum', 'import', 
                             'sliceToRange', 'PatternFormat', 'modi', 'Pow', 'PulsesToDurations', 'True', 
                             'issubclass', 'PWalk', 'cmp', 'PDelay', 'list', 'dir', 'len', 'enumerate', 
                             'Format', 'PTri', 'reduce', 'reload', 'PEuclid', 'PIndex', 'PFibMod', 'divmod', 
                             'PSquare', 'unichr', 'round', 'map', 'long', 'Group', 'linvar', 'mapvar', 
                             'PPairs', 'with', 'Mod', 'None', 'locals', 'basestring', 'P10', 'PRhythm', 
                             'tuple', 'from', 'not', 'class', 'try', 'hasattr', 'compile', 'PSum', 'Pvar', 
                             'filter', 'loop_pattern_func', 'PJoin', 'bool', 'Root', 'eval', 'for', 'Server', 
                             'Add', 'PSq', 'str', 'PStutter', 'get_inverse_op', 'var', 'repr', 'PChain', 
                             'reversed', 'hex', 'Nil', 'rSub', 'equal_values', 'if', 'all', 'rAdd', 'return', 
                             'PZip', 'global', 'else', 'Samples', 'print', 'PWhite', 'file', 'ord', 'rOr', 'range',
                             'complex', 'PwRand', 'PEuclid2', 'group_modi', 'Get', 'PStretch', 'asStream', 'lambda',
                              'PSine', 'PDur', 'self', 'False', 'rGet', 'except', 'PQuicken', 'zip', 'hash', 'PAlt', 
                              'PatternContainer', 'help', 'pow', 'PEq', 'in', 'PStep', 'iter', 'is', 'GeneratorPattern', 
                              'ClassPatternMethod', 'min', 'DominantPattern', 'Mul', 'when', 'metaPattern', 'rMod', 
                              'input', 'object', 'def', 'POperand', 'elif', 'while', 'PNe', 'PShuf', 'xrange',
                              'getattr', 'get_expanded_len', 'rPow', 'bytearray', 'asPattern', 'expvar', 'Pattern', 
                              'EmptyItem', 'vars', 'PZip2', 'delattr', 'frozenset', 'property', 'execfile', 
                              'deepcopy', 'stdout', 'Xor', 'int', 'Sub', 'PxRand', 'PatternMethod', 'as', 'float', 
                              'set', '\\A\\s*@.+', 'max', 'dots', 'patternclass', 'LCM', 'open', 'raw_input', 
                              'PBeat', 'PGroup', 'StaticPatternMethod', 'Convert', 'P', 'and', 'abs', 'bin', 
                              'slice', 'id', 'rDiv', '>>']

            self.re["tag_bold"] = compile_regex(self.keywords)

    def __repr__(self):
        return "FoxDot"

    def write_stdout(self, string):
        self.lang.stdin.write(string + "\n\n")
        self.lang.stdin.flush()
        return

    def start(self):
        if not self.imported:
            Interpreter.start(self)
        return self

    def kill(self):
        if self.imported:
            self.evaluate(self.stop_sound())
        else:
            Interpreter.kill(self)
        return

    def evaluate(self, *args, **kwargs):
        """ Sends code to FoxDot instance and prints any error text """

        if self.imported:
        
            Interpreter.print_stdin(self, *args, **kwargs)

            response = self.lang.execute(args[0], verbose=False)

            if response is not None:

                if response.startswith("Traceback"):

                    print(response)
        else:

            Interpreter.evaluate(self, *args, **kwargs)
        
        return

    def stop_sound(self):
        return "Clock.clear()"


class SuperColliderInterpreter(Interpreter):
    filetype = ".scd"
    def __init__(self):
        
        if PY_VERSION == 2:
            from . import OSC
        else:
            from . import OSC3 as OSC

        # Connect to OSC client
        self.host = 'localhost'
        self.port = 57120
        self.lang = OSC.OSCClient()
        self.lang.connect((self.host, self.port))

        # Define a function to produce new OSC messages
        self.new_msg = lambda: OSC.OSCMessage("/troop")

    def __repr__(self):
        return "SuperCollider"

    def kill(self):
        self.evaluate(self.stop_sound())
        self.lang.close()
        return

    def get_block_of_code(self, text, index):
        """ Returns the start and end line numbers of the text to evaluate when pressing Ctrl+Return. """

        # Get start and end of the buffer
        start, end = "1.0", text.index("end")
        lastline   = int(end.split('.')[0]) + 1

        # Indicies of block to execute
        block = [0,0]        
        
        # 1. Get position of cursor
        cur_y, cur_x = index.split(".")
        cur_y, cur_x = int(cur_y), int(cur_x)

        left_cur_y, left_cur_x   = cur_y, cur_x
        right_cur_y, right_cur_x = cur_y, cur_x

        # Go back to find a left bracket

        while True:

            new_left_cur_y,  new_left_cur_x  = self.get_left_bracket(text, left_cur_y, left_cur_x)
            new_right_cur_y, new_right_cur_x = self.get_right_bracket(text, right_cur_y, right_cur_x)

            if new_left_cur_y is None or new_right_cur_y is None:

                block = [left_cur_y, right_cur_y + 1]

                break

            else:

                left_cur_y,  left_cur_x  = new_left_cur_y,  new_left_cur_x
                right_cur_y, right_cur_x = new_right_cur_y, new_right_cur_x

        return block

    def get_left_bracket(self, text, cur_y, cur_x):
        count = 0
        line_text = text.get("{}.{}".format(cur_y, 0), "{}.{}".format(cur_y, "end"))
        for line_num in range(cur_y, 0, -1):
            # Only check line if it has text
            if len(line_text) > 0:
                for char_num in range(cur_x - 1, -1, -1):
                    
                    try:
                        char = line_text[char_num] 
                    except IndexError as e:
                        print("left bracket, string is {}, index is {}".format(line_text, char_num))
                        raise(e)

                    if char == ")":
                        count += 1
                    elif char == "(":
                        if count == 0:
                            return line_num, char_num
                        else:
                            count -= 1
            line_text = text.get("{}.{}".format(line_num - 1, 0), "{}.{}".format(line_num - 1, "end"))
            cur_x     = len(line_text)
        return None, None

    def get_right_bracket(self, text, cur_y, cur_x):
        num_lines = int(text.index("end").split(".")[0]) + 1
        count = 0
        for line_num in range(cur_y, num_lines):
            line_text = text.get("{}.{}".format(line_num, 0), "{}.{}".format(line_num, "end"))
            # Only check line if it has text
            if len(line_text) > 0:
                for char_num in range(cur_x, len(line_text)):
                    
                    try:
                        char = line_text[char_num] 
                    except IndexError as e:
                        print("right bracket, string is {}, index is {}".format(line_text, char_num))
                        raise(e)

                    if char == "(":
                        count += 1
                    if char == ")":
                        if count == 0:
                            return line_num, char_num + 1
                        else:
                            count -= 1
            cur_x = 0
        else:
            return None, None


    def stop_sound(self):
        return "s.freeAll"
        
    def evaluate(self, string, *args, **kwargs):
        # Print to the console the message
        Interpreter.print_stdin(self, string, *args, **kwargs)
        # Create an osc message and send to SuperCollider
        msg = self.new_msg()
        msg.append([string])
        self.lang.send(msg)
        return

class TidalInterpreter(Interpreter):
    path = 'ghci'
    filetype = ".tidal"
    def __init__(self):
        # Start haskell interpreter
        Interpreter.__init__(self, self.path)

    def start(self):

        self.lang = Popen(self.path, shell=True, universal_newlines=True,
                          stdin=PIPE)

        # Import Tidal and set the cps
        self.lang.stdin.write("import Sound.Tidal.Context\n")
        self.lang.stdin.flush()
        self.lang.stdin.write(":set -XOverloadedStrings\n")
        self.lang.stdin.flush()
        self.lang.stdin.write("(cps, getNow) <- bpsUtils\n")
        self.lang.stdin.flush()

        # Not always necessary but some versions of windows need setting d1-9
        d_vals = range(1,10)
        
        for n in d_vals:
            self.lang.stdin.write("(d{}, t{}) <- superDirtSetters getNow\n".format(n, n))
            self.lang.stdin.flush()

        # Define hush

        self.lang.stdin.write("let hush = mapM_ ($ silence) [d1,d2,d3,d4,d5,d6,d7,d8,d9]\n")
        self.lang.stdin.flush()

        # Set any keywords e.g. d1 and $

        self.keywords  = ["d{}".format(n) for n in d_vals]
        self.keywords += ["\$", "#", "hush"] # add string regex?

        self.re["tag_bold"] = compile_regex(self.keywords)
        
        return self

    def __repr__(self):
        return "TidalCycles"
    
    @staticmethod
    def format(string):
        """ Used to formant multiple lines in haskell """
        return ":{\n"+string+"\n:}\n"

    def stop_sound(self):
        """ Triggers the 'hush' command using Ctrl+. """
        return "hush"

class StackTidalInterpreter(TidalInterpreter):
    path = "stack ghci"

langtypes = { FOXDOT        : FoxDotInterpreter,
              TIDAL         : TidalInterpreter,
              TIDALSTACK    : StackTidalInterpreter,
              SUPERCOLLIDER : SuperColliderInterpreter,
              DUMMY         : DummyInterpreter }
