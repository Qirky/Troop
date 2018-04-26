"""
    Server/message.py
    -----------------
    Use -1 as an ID when it doesn't matter

"""

from __future__ import absolute_import

import json

class MESSAGE(object):
    type = None
    def __init__(self, src_id):
        self.data = {"src_id": src_id, "type": self.type}

    def as_string(self):
        return str(self)

    def as_bytes(self):
        return str(self).encode("utf-8")

    def dict(self):
        return self.data

    def __str__(self):
        """ Prepares the json message to be sent with first 4 digits
            denoting the length of the message """
        packet = str(json.dumps(self.data, separators=(',',':')))
        length = "{:04d}".format( len(packet) )
        return length + packet

    def __len__(self):
        return len(str(self))

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, key):
        return key in self.data

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
        self["operation"] = [str(item) if not isinstance(item, int) else item for item in operation]
        self["revision"]  = int(revision)

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
        MSG_SELECT,
        MSG_REMOVE,
        MSG_PASSWORD,
        MSG_KILL,
        MSG_EVALUATE_BLOCK,
        MSG_EVALUATE_STRING,
        MSG_RESET,
    ]
}

def convert_to_message(string):
    """ Takes a dict of values and returns the appropriate message wrapper """
    data = json.loads(string)
    cls = MESSAGE_TYPE[data["type"]]
    del data["type"]
    return cls(**data)

def read_from_socket(sock):
    """ Reads data from the socket """
    # Get number single int that tells us how many digits to read
    try:
        bits = int(sock.recv(4))
        if bits > 0:
            # Read the remaining data (JSON)
            data = sock.recv(bits)
            # Convert back to Python data structure
            return convert_to_message(data)
    except (ConnectionAbortedError, ConnectionResetError):
        return None

def send_to_socket(sock, data):
    """ Sends instances of MESSAGE to a connected socket """
    assert isinstance(data, MESSAGE)
    # Get length and store as string
    msg_len, msg_str = len(data), data.as_bytes()
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