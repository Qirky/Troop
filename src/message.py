"""
    Server/message.py
    -----------------

    Messages are sent as a series of arguments surrounnded by
    <arrows><like><so>.

"""

from __future__ import absolute_import

import re
import inspect
import json

def escape_chars(s):
    return s.replace(">", "\>").replace("<", "\<")

def unescape_chars(s):
    return s.replace("\>", ">").replace("\<", "<")

class NetworkMessageReader:
    def __init__(self):
        self.string = ""
        self.re_msg = re.compile(r"<(.*?>?)>(?=<|$)", re.DOTALL)

    def findall(self, string):
        """ Returns all values in a message as a list """
        return self.re_msg.findall(string)

    def convert_to_json(self, string):
        """ Un-escapes special characters and converts a string to a json object """
        return json.loads(unescape_chars(string))

    def feed(self, data):
        """ Adds text (read from server connection) and returns the complete messages within. Any
            text un-processed is stored and used the next time `feed` is called. """

        # Most data is read from the server, which is bytes in Python3 and str in Python2, so make
        # sure it is properly decoded to a string.

        string = data.decode() if type(data) is bytes else data

        if string == "":

            raise EmptyMessageError()

        # Join with any existing text
        full_message = self.string + string

        # Identify message tags
        data = self.findall(full_message)

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

                args = [self.convert_to_json(data[n]) for n in range(i+1, i+j)]

                msg_id, args = args[0], args[1:]

                pkg.append(cls(*args))

                pkg[-1].set_msg_id(msg_id)

                # Keep track of how much of the string we have processed

                length += len(str(pkg[-1]))

            except IndexError:

                # If there aren't enough arguments, return what we have so far

                break

            except TypeError as e:

                # Debug info

                print( cls.__name__, e )
                print( string )

            i += j

        # If we process the whole string, reset the stored string

        self.string = full_message[length:]

        return pkg


class MESSAGE(object):
    """ Abstract base class """
    data = {}
    keys = []
    type = None
    def __init__(self, src_id, msg_id=0):
        self.data = {'src_id' : int(src_id), "type" : self.type, "msg_id": msg_id}
        self.keys = ['type', 'msg_id', 'src_id']

    def __str__(self):
        return "".join([self.format(item) for item in self])

    def set_msg_id(self, value):
        self.data["msg_id"] = int(value)

    @staticmethod
    def format(value):
        return "<{}>".format(escape_chars(json.dumps(value)))

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
        return "".join(["<{}>".format(json.dumps(item)) for item in args])

    @staticmethod
    def password(password):
        return MESSAGE.compile(-1, -1, password)

    @classmethod
    def header(cls):
        # args = inspect.getargspec(cls.__init__).args
        # args[0] = 'type'
        args = ['type', 'msg_id'] + inspect.getargspec(cls.__init__).args[1:]
        return args

# Define types of message
        
class MSG_CONNECT(MESSAGE):
    type = 1
    def __init__(self, src_id, name, hostname, port, dummy=False):
        MESSAGE.__init__(self, src_id)
        self['name']      = str(name)
        self['hostname']  = str(hostname)
        self['port']      = int(port)
        self['dummy']     = int(dummy)

class MSG_OPERATION(MESSAGE):
    type = 2
    def __init__(self, src_id, operation, revision):
        MESSAGE.__init__(self, src_id)
        self["operation"] = [str(item) if not isinstance(item, int) else item for item in operation]
        self["revision"]  = int(revision)

class MSG_SET_MARK(MESSAGE):
    type = 3
    def __init__(self, src_id, index, reply=1):
        MESSAGE.__init__(self, src_id)
        self['index'] = int(index)
        self['reply'] = int(reply)

class MSG_PASSWORD(MESSAGE):
    type = 4
    def __init__(self, src_id, password, name):
        MESSAGE.__init__(self, src_id)
        self['password']=str(password)
        self['name']=str(name)

class MSG_REMOVE(MESSAGE):
    type = 5
    def __init__(self, src_id):
        MESSAGE.__init__(self, src_id)

class MSG_EVALUATE_STRING(MESSAGE):
    type = 6
    def __init__(self, src_id, string, reply=1):
        MESSAGE.__init__(self, src_id)
        self['string']=str(string)
        self['reply']=int(reply)

class MSG_EVALUATE_BLOCK(MESSAGE):
    type = 7
    def __init__(self, src_id, start, end, reply=1):
        MESSAGE.__init__(self, src_id)
        self['start']=int(start)
        self['end']=int(end)
        self['reply']=int(reply)

class MSG_GET_ALL(MESSAGE):
    type = 8
    def __init__(self, src_id):
        MESSAGE.__init__(self, src_id)

class MSG_SET_ALL(MESSAGE):
    type = 9
    def __init__(self, src_id, document, peer_tag_loc, peer_loc):
        MESSAGE.__init__(self, src_id)
        self['document']     = str(document)
        self["peer_tag_loc"] = peer_tag_loc
        self["peer_loc"]     = peer_loc

class MSG_SELECT(MESSAGE):
    type = 10
    def __init__(self, src_id, start, end, reply=1):
        MESSAGE.__init__(self, src_id)
        self['start']=int(start)
        self['end']=int(end)
        self['reply']=int(reply)

class MSG_RESET(MSG_SET_ALL):
    type = 11 

class MSG_KILL(MESSAGE):
    type = 12
    def __init__(self, src_id, string):
        MESSAGE.__init__(self, src_id)
        self['string']=str(string)

class MSG_CONNECT_ACK(MESSAGE):
    type = 13
    def __init__(self, src_id, reply=0):
        MESSAGE.__init__(self, src_id)
        self["reply"] = reply

class MSG_REQUEST_ACK(MESSAGE):
    type = 14
    def __init__(self, src_id, flag, reply=0):
        MESSAGE.__init__(self, src_id)
        self['flag'] = int(flag)
        self["reply"] = reply

class MSG_CONSTRAINT(MESSAGE):
    type = 15
    def __init__(self, src_id, constraint_id):
        MESSAGE.__init__(self, src_id)
        self['constraint_id'] = int(constraint_id) 
        # self.peer_id = int(peer) # 

class MSG_CONSOLE(MESSAGE):
    type = 16
    def __init__(self, src_id, string):
        MESSAGE.__init__(self, src_id)
        self['string'] = str(string)
 
# Create a dictionary of message type to message class 

MESSAGE_TYPE = {msg.type : msg for msg in [
        MSG_CONNECT,
        MSG_OPERATION,
        MSG_SET_ALL,
        MSG_GET_ALL,
        MSG_SET_MARK,
        MSG_SELECT,
        MSG_REMOVE,
        MSG_PASSWORD,
        MSG_KILL,
        MSG_EVALUATE_BLOCK,
        MSG_EVALUATE_STRING,
        MSG_RESET,
        MSG_CONNECT_ACK,
        MSG_REQUEST_ACK,
        MSG_CONSTRAINT,
        MSG_CONSOLE,
    ]
}

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
        return "DeadClientError: Could not connect to {}".format(self.name)



if __name__ == "__main__":

    msg = MSG_SET_MARK(42, 24)
    print(msg,)
    print(msg.header())