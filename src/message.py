"""
    Server/message.py
    -----------------

    Messages are sent as a series of arguments surrounnded by
    <arrows><like><so>.

    Use -1 as an ID when it doesn't matter

    //TODO - just use JSON

"""

from __future__ import absolute_import

import re
import inspect
import json

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

                args = [json.loads(data[n]) for n in range(i+1, i+j)]

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
        return "".join([self.format(item) for item in self])

    @staticmethod
    def format(value):
        return "<{}>".format(json.dumps(value))

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
        args = inspect.getargspec(cls.__init__).args
        args[0] = 'type'
        return args

# Define types of message
        
class MSG_CONNECT(MESSAGE):
    type = 1
    def __init__(self, src_id, name, hostname, port):
        MESSAGE.__init__(self, src_id)
        self['name']      = str(name)
        self['hostname']  = str(hostname)
        self['port']      = int(port)

class MSG_OPERATION(MESSAGE):
    type = 2
    def __init__(self, src_id, operation, revision):
        MESSAGE.__init__(self, src_id)
        self["operation"] = operation
        self["revision"]  = revision

class MSG_SET_MARK(MESSAGE):
    type = 3
    def __init__(self, src_id, index, reply=1):
        MESSAGE.__init__(self, src_id)
        self['index'] = int(index)
        self['reply'] = int(reply)

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
        self['document'] = document
        self["peer_tag_loc"] = peer_tag_loc
        self["peer_loc"] = peer_loc

# class MSG_SELECT(MESSAGE):
#     type = 10
#     def __init__(self, src_id, start, end, reply=1):
#         MESSAGE.__init__(self, src_id)
#         self['start']=str(start)
#         self['end']=str(end)
#         self['reply']=int(reply)


class MSG_PASSWORD(MESSAGE):
    type = 13
    def __init__(self, src_id, password):
        MESSAGE.__init__(self, src_id)
        self['password']=str(password)   

class MSG_KILL(MESSAGE):
    type = 20
    def __init__(self, src_id, string):
        MESSAGE.__init__(self, src_id)
        self['string']=str(string)

 
# Create a dictionary of message type to message class 

MESSAGE_TYPE = {msg.type : msg for msg in [
        MSG_CONNECT,
        MSG_OPERATION,
        MSG_SET_ALL,
        MSG_GET_ALL,
        MSG_SET_MARK,
        MSG_REMOVE,
        MSG_PASSWORD,
        MSG_KILL,
        MSG_EVALUATE_BLOCK,
        MSG_EVALUATE_STRING
    ]
}

def read_from_socket(sock):
    """ Reads data from the socket """
    # Get number single int that tells us how many digits to read
    try:
        bits = int(sock.recv(4))
        if bits > 0:
            # Read the remaining data (JSON)
            data = sock.recv(bits)
            # Convert back to Python data structure
            return json.loads(data)
    except (ConnectionAbortedError, ConnectionResetError):
        return None

def send_to_socket(sock, data):
    """ Converts Python data structure to JSON message and
        sends to a connected socket """
    msg = Message(data)
    # Get length and store as string
    msg_len, msg_str = len(msg), msg.as_bytes()
    # Continually send until we know all of the data has been sent
    sent = 0
    while sent < msg_len:
        bits = sock.send(msg_str[sent:])
        sent += bits
    return

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

    test = MSG_OPERATION(1, [0, "s", 4], 1)

    print(test)

    test["reply"] = 1

    print(test)

    print(test.info())
    print(test.bytes())