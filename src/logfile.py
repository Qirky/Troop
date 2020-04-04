### Experimental

from __future__ import absolute_import

import time
from threading import Thread
from .message import *

class Timer:
    def __init__(self):
        self.start = time.time()

    def get_time(self):
        return time.time() - self.start

class Log:
    text = None
    def __init__(self, filename):
        self.time = []
        self.data = []
        self.reader = NetworkMessageReader()
        self.msg_id = 0
        with open(filename) as f:

            for line in f.readlines():

                time, message = line.split(" ", 1)

                time    = float(time)
                
                message = bytes(message.strip()[1:-1], "utf-8").decode('unicode_escape')

                message = self.reader.feed(message)[0]

                if len(self.time) == 0:
                
                    self.time.append(time)

                else:

                    self.time.append(time-last_time)

                last_time = time
                
                self.data.append(message)

        self.thread = None

    def __len__(self):
        return len(self.data)

    def set_marker(self, peer):
        """ Sets this thread to imitate the client """
        self.text = peer.root_parent
        for i in range(len(self.data)):
            self.data[i]['src_id'] = peer.id

    def recreate(self):
        """ Recreates the performance of the log """
        self.thread = Thread(target=self.__run)
        self.thread.start()

    def stop(self):
        """ Stops recreating a log """
        if self.thread.isAlive():
            self.thread.join(1)
        return 

    def __run(self):
        for i in range(len(self)):
            time.sleep(self.time[i])
            # Change names in future
            self.text.text.handle(self.data[i])

if __name__ == "__main__":

    l = Log("../logs/log_test.txt")


    
