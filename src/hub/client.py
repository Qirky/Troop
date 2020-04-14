import json
import socket
import time
import sys
import threading

from ..config import PUBLIC_SERVER_ADDRESS

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
        self.name = kwargs.get('name')
        self.hostname = kwargs.get('host', PUBLIC_SERVER_ADDRESS[0])
        self.port = int(kwargs.get('port', 57990))
        self.address = (self.hostname, self.port)
        self.password = kwargs.get('password', '')

        try:
            self.socket = socket.socket()
            self.socket.connect(self.address)
        except socket.error:
            sys.exit("Troop Hub Service | Error: could not connect to service")

        self.polling_thread = threading.Thread(target=self.listen)
        self.polling_thread.daemon = True

        self.running = False

    def start(self):
        ''' Connect to Hub and instantiate server  '''
        self.running = self.connect()
        self.polling_thread.start()
        while self.running:
            try:
                time.sleep(10)
            except KeyboardInterrupt:
                self.kill('KeyboardInterrupt', error=False)
                self.running=False
        return

    def listen(self):
        ''' Continually polls - currently has no handle except errors '''
        while self.running:
            try:
                self.poll()
            except Exception as e:
                self.kill(e)
                self.running = False
        return

    def connect(self):
        if not self.name:
            raise ValueError("Server name cannot be 'None'")
        self.send({
            'type': 'server',
            'name': self.name,
            'password': self.password
        })
        data = self.poll()
        if 'address' in data:
            print("Server running @ {} on port {}.".format(*data['address']))
            return True
        return False

    def query(self, name):
        '''
        Get the hostname and port for a named Troop server withing the Hub Service
        '''
        self.send({
            'type': 'query',
            'name': name
        })
        data = self.poll()
        result = data.get('result')
        if result is None:
            sys.exit("Troop Hub Service | Error: '{}' not found".format(name))
        return result

    def poll(self):
        ''' Used when polling socket, handles errors '''
        data = self.recv()
        if not data:
            return self.handle_error("Broken pipe")
        elif 'error' in data:
            return self.handle_error(data['error'])
        return data

    def handle_error(self, message):
        print("Error: {}".format(message))
        self.running = False
        return {}

    def kill(self, message="", error=True):
        if error:
            self.handle_error(message)
        self.send({'kill': str(message)})

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
