"""
    Server/message.py
    -----------------

    Messages are sent as a series of arguments surrounnded by
    <arrows><like><so>.

    Use -1 as an ID when it doesn't matter

"""
from config import *

import re
import inspect

re_msg = re.compile(r"<(.*?>?)>(?=<|$)", re.DOTALL)

def NetworkMessage(string):
    
    # Identify message tags
    data = re_msg.findall(string)

    i, pkg = 0, []

    while i < len(data):

        # Find out which message it is, send back a list of messages

        cls = MESSAGE_TYPE[int(data[i])]
        j = len(cls.header())
        
        try:

            pkg.append(cls(*data[i+1:i+j]))

        except TypeError as e:

            stdout( cls.__name__, e )

        i += j

    return pkg

# Message Types

class MESSAGE(object):
    """ Abstract base class """
    data = {}
    keys = []
    def __init__(self, src_id):
        self.data={'src_id' : int(src_id)}
        self.keys = self.data.keys()

    def __str__(self):
        return "<{}>".format(self.type) + "".join(["<{}>".format(item) for item in self])

    def raw_string(self):
        return "<{}>".format(self.type) + "".join(["<{}>".format(repr(item)) for item in self])
        
    def __repr__(self):
        return self.__class__.__name__ + str(tuple(self))

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        for key in self.keys:
            yield self.data[key]

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        if key not in self.keys:
            self.keys.append(key)
        self.data[key] = value

    def __contains__(self, key):
        return key in self.data

    def __eq__(self, other):
        return self.type == other

    def __ne__(self, other):
        return self.type != other

    @staticmethod
    def compile(*args):
        return "".join(["<{}>".format(item) for item in args])

    @staticmethod
    def password(password):
        return NetworkMessage.compile(-1, -1, password)

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
    def __init__(self, src_id, start, end):
        MESSAGE.__init__(self, src_id)
        self['start']=str(start)
        self['end']=str(end)

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
    def __init__(self, src_id, client_id):
        MESSAGE.__init__(self, src_id)
        self['client_id']=int(client_id)

class MSG_SET_ALL(MESSAGE):
    type = 9
    def __init__(self, src_id, string, client_id):
        MESSAGE.__init__(self, src_id)
        self['string']=str(string)
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
    def __init__(self, src_id, beat, timestamp):
        MESSAGE.__init__(self, src_id)
        self['beat']      = str(beat)
        self['timestamp'] = str(timestamp)

class MSG_GET_TIME(MESSAGE):
    type = 15
    def __init__(self):
        pass        

class MSG_BRACKET(MESSAGE):
    type = 16
    def __init__(self, src_id, row1, col1, row2, col2, reply):
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
                                             MSG_PING] }

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
    

if __name__ == "__main__":

    a = MSG_GET_ALL(1,2)
    print 'src_id' in a
