"""
    Server/message.py
    -----------------

    Messages are sent as a series of arguments surrounnded by
    <arrows><like><so>.

    Use -1 as an ID when it doesn't matter

"""

from __future__ import absolute_import

import re
import inspect
import json
import ast

class NetworkMessageReader:
    def __init__(self):
        self.string = ""
        self.re_msg = re.compile(r"<(.*?>?)>(?=<|$)", re.DOTALL)

    def feed(self, data):
        """ Adds text (read from server connection) and returns the complete messages within. Any
            text un-processed is stored and used the next time `feed` is called. """

        # Most data is read from the server, which is bytes in Python3 and str in Python2, so make
        # sure it is properly decoded to a string.

        if type(data) is bytes:

            string = data.decode()

        if string == "":

            raise EmptyMessageError()

        # Collate with any existing text
        full_message = self.string + string

        # Identify message tags
        data = self.re_msg.findall(full_message)

        # i is the data, pkg  is the list of messages
        i, pkg = 0, []

        # length is the size of the string processed
        length = 0
        
        while i < len(data):

            # Find out which message type it is
            
            cls = MESSAGE_TYPE[int(data[i])]

            # This tells us how many following items are arguments of this message

            j = len(cls.header())

            try:

                # Collect the arguments

                args = [data[n] for n in range(i+1, i+j)]

                pkg.append(cls(*args))

                # Keep track of how much of the string we have processed

                length += len(str(pkg[-1]))

            except IndexError:

                # If there aren't enough arguments, store the remaining string for next time
                # and return the list we have so far

                self.string = full_message[length:]

                return pkg

            except TypeError as e:

                # Debug info

                stdout( cls.__name__, e )
                stdout( string )

            i += j

        # If we process the whole string, reset the stored string

        self.string = ""

        return pkg


class MESSAGE(object):
    """ Abstract base class """
    data = {}
    keys = []
    type = None
    def __init__(self, src_id):
        self.data = {'src_id' : int(src_id), "type" : self.type}
        self.keys = ['type', 'src_id']

    def __str__(self):
        return "".join(["<{}>".format(item) for item in self])

    def bytes(self):
        return str(self).encode("utf-8")

    def raw_string(self):
        return "<{}>".format(self.type) + "".join(["<{}>".format(repr(item)) for item in self])
        
    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(self.data)

    def info(self):
        return self.__class__.__name__ + str(tuple(self))

    def __iter__(self):
        for key in self.keys:
            yield self.data[key]

    def dict(self):
        return self.data

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        if key not in self.keys:
            self.keys.append(key)
        self.data[key] = value

    def __contains__(self, key):
        return key in self.data

    def __eq__(self, other):
        if isinstance(other, MESSAGE):
            return self.type == other.type and self.data == other.data
        else:
            return False

    def __ne__(self, other):
        if isinstance(other, MESSAGE):
            return self.type != other or self.data != other.data
        else:
            return True

    @staticmethod
    def compile(*args):
        return "".join(["<{}>".format(item) for item in args])

    @staticmethod
    def password(password):
        return MESSAGE.compile(-1, -1, password)

    @classmethod
    def header(cls):
        args = inspect.getargspec(cls.__init__).args
        args[0] = 'type'
        return args

# Define types of message
        
class MSG_CONNECT(MESSAGE):
    type = 1
    def __init__(self, src_id, name, hostname, port, row=1, col=0):
        MESSAGE.__init__(self, src_id)
        self['name']      = str(name)
        self['hostname']  = str(hostname)
        self['port']      = int(port)
        self['row']       = int(row)
        self['col']       = int(col)

class MSG_INSERT(MESSAGE):
    type = 2
    def __init__(self, src_id, char, row, col, reply=1):
        MESSAGE.__init__(self, src_id)
        self['char']  = str(char)
        self['row']   = int(row)
        self['col']   = int(col)
        self['reply'] = int(reply)

class MSG_DELETE(MESSAGE):
    type = 3
    def __init__(self, src_id, row, col, reply=1):
        MESSAGE.__init__(self,  src_id)
        self['row']=int(row)
        self['col']=int(col)
        self['reply']=int(reply)

class MSG_BACKSPACE(MESSAGE):
    type = 4
    def __init__(self, src_id, row, col, reply=1):
        MESSAGE.__init__(self, src_id)
        self['row']=int(row)
        self['col']=int(col)
        self['reply']=int(reply)

class MSG_SELECT(MESSAGE):
    type = 5
    def __init__(self, src_id, start, end, reply=1):
        MESSAGE.__init__(self, src_id)
        self['start']=str(start)
        self['end']=str(end)
        self['reply']=int(reply)

class MSG_EVALUATE_STRING(MESSAGE):
    type = 6
    def __init__(self, src_id, string, reply=1):
        MESSAGE.__init__(self, src_id)
        self['string']=str(string)
        self['reply']=int(reply)

class MSG_EVALUATE_BLOCK(MESSAGE):
    type = 7
    def __init__(self, src_id, start_line, end_line, reply=1):
        MESSAGE.__init__(self, src_id)
        self['start_line']=int(start_line)
        self['end_line']=int(end_line)
        self['reply']=int(reply)

class MSG_GET_ALL(MESSAGE):
    type = 8
    def __init__(self, src_id):
        MESSAGE.__init__(self, src_id)

class MSG_SET_ALL(MESSAGE):
    type = 9
    def __init__(self, src_id, data, client_id):
        MESSAGE.__init__(self, src_id)
        # If the json data is a dict, convert it. If not assume it is correctly formatted
        self['data']=json.dumps(data) if type(data) is dict else data
        self['client_id']=int(client_id)

class MSG_RESPONSE(MESSAGE):
    type = 10
    def __init__(self, src_id, string):
        MESSAGE.__init__(self, src_id)
        self['string']=str(string)

class MSG_SET_MARK(MESSAGE):
    type = 11
    def __init__(self, src_id, row, col, reply=1):
        MESSAGE.__init__(self, src_id)
        self['row']=int(row)
        self['col']=int(col)
        self['reply']=int(reply)

class MSG_REMOVE(MESSAGE):
    type = 12
    def __init__(self, src_id):
        MESSAGE.__init__(self, src_id)

class MSG_PASSWORD(MESSAGE):
    type = 13
    def __init__(self, src_id, password):
        MESSAGE.__init__(self, src_id)
        self['password']=str(password)

class MSG_SET_TIME(MESSAGE):
    type = 14
    def __init__(self, src_id, time, timestamp, client_id):
        MESSAGE.__init__(self, src_id)
        self['time']      = float(time)
        self['timestamp'] = str(timestamp)
        self['client_id'] = int(client_id)

class MSG_GET_TIME(MESSAGE):
    type = 15
    def __init__(self, src_id, client_id):
        MESSAGE.__init__(self, src_id)
        self['client_id'] = client_id

class MSG_BRACKET(MESSAGE):
    type = 16
    def __init__(self, src_id, row1, col1, row2, col2, reply=1):
        MESSAGE.__init__(self, src_id)

        self['row1'] = int(row1)
        self['col1'] = int(col1)
        
        self['row2'] = int(row2)
        self['col2'] = int(col2)

        self['reply'] = int(reply)

class MSG_PING(MESSAGE):
    type = 17
    def __init__(self):
        pass

class MSG_CONSTRAINT(MESSAGE):
    type = 18
    def __init__(self, src_id, name, reply=1):
        MESSAGE.__init__(self, src_id)
        self['name'] = str(name)
        self['reply'] = int(reply)

class MSG_COMPARE(MESSAGE):
    type = 19
    def __init__(self, src_id, data):
        MESSAGE.__init__(self, src_id)
        self['data']=json.dumps(data) if type(data) != str else data     

class MSG_KILL(MESSAGE):
    type = 20
    def __init__(self, src_id, string):
        MESSAGE.__init__(self, src_id)
        self['string']=str(string)

class MSG_MOVE_CURSOR(MESSAGE):
    type = 21
    dirs = ["left", "right", "up", "down", "home", "end"]
    def __init__(self, src_id, direction, reply=1):
        MESSAGE.__init__(self, src_id)
        self["direction"]=int(direction)
        self["reply"] = int(reply)

    @classmethod
    def get_index(cls, string):
        return cls.dirs.index(string.lower())

    def get_direction(self):
        return self.dirs[self["direction"]]

class MSG_MOVE_SELECTION(MSG_MOVE_CURSOR):
    type = 22

 
# Create a dictionary of message type to message class 

MESSAGE_TYPE = { msg.type : msg for msg in [ MSG_CONNECT,
                                             MSG_INSERT,
                                             MSG_DELETE,
                                             MSG_BACKSPACE,
                                             MSG_SELECT,
                                             MSG_EVALUATE_STRING,
                                             MSG_EVALUATE_BLOCK,
                                             MSG_GET_ALL,
                                             MSG_SET_ALL,
                                             MSG_RESPONSE,
                                             MSG_SET_MARK,
                                             MSG_REMOVE,
                                             MSG_PASSWORD,
                                             MSG_SET_TIME,
                                             MSG_GET_TIME,
                                             MSG_BRACKET,
                                             MSG_PING,
                                             MSG_CONSTRAINT,
                                             MSG_COMPARE,
                                             MSG_KILL,
                                             MSG_MOVE_CURSOR,
                                             MSG_MOVE_SELECTION ] }

# Exceptions

class EmptyMessageError(Exception):
    def __init__(self):
        self.value = "Message contained no data"
    def __str__(self):
        return repr(self.value)

class ConnectionError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class DeadClientError(Exception):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "Could not connect to {}".format(self.name)