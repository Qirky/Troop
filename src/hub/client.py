import json
import socket
import time
from hashlib import md5

class JSONMessage:
    """ Wrapper for JSON messages sent to the server """
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return self.string

    @property
    def string(self):
        """
        Prepares the json message to be sent with first 4 digits
        denoting the length of the message
        """
        if not hasattr(self, "_string"):
            packet = str(json.dumps(self.data, separators=(',',':')))
            length = "{:04d}".format( len(packet) )
            self._string = length + packet
        return self._string

    def __len__(self):
        return len(str(self))

class HubClient:
    def __init__(self, *args, **kwargs):
        self.hostname = kwargs.get('host', '188.166.144.124')
        self.port = kwargs.get('port', 57990)
        self.address = (self.hostname, self.port)
        self.password = kwargs.get('password', '')

        self.socket = socket.socket()
        self.socket.connect(self.address)
        self.running = False

    def start(self):
        ''' Connect to Hub and instantiate server  '''
        self.running = self.connect()
        while self.running:
            try:
                self.poll()
                time.sleep(1)
            except Exception as e:
                return self.kill(e)
        return

    def connect(self):
        self.send({'password': self.password})
        data = self.poll()
        if 'address' in data:
            print("Server running @ {} on port {}.".format(*data['address']))
            return True
        return False

    def poll(self):
        ''' Used when polling socket, handles errors '''
        data = self.recv()
        if not data:
            self.handle_error("Broken pipe")
        if 'error' in data:
            self.handle_error(data['error'])
        return data

    def handle_error(self, message):
        print(message)
        self.running = False

    def kill(self, message=""):
        self.handle_error(message)
        self.send({'kill': message})

    def recv(self):
        """ Reads data from the socket """
        # Get number single int that tells us how many digits to read
        try:
            bits = int(self.socket.recv(4).decode())
        except Exception as e:
            return None
        if bits > 0:
            # Read the remaining data (JSON)
            data = self.socket.recv(bits).decode()
            # Convert back to Python data structure
            return json.loads(data)

    def send(self, data):
        """ Converts Python data structure to JSON message and
            sends to a connected socket """
        msg = JSONMessage(data)
        # Get length and store as string
        msg_len, msg_str = len(msg), str(msg).encode()
        # Continually send until we know all of the data has been sent
        sent = 0
        while sent < msg_len:
            bits = self.socket.send(msg_str[sent:])
            sent += bits
        return
