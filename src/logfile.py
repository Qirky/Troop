### Experimental

from __future__ import absolute_import

from threading import Thread
from time import sleep
from .message import *

class Log:
    text = None
    def __init__(self, filename):
        self.time = []
        self.data = []
        with open(filename) as f:

            for line in f.readlines():

                time, message = line.split(" ", 1)

                time    = float(time)
                
                message = message.strip()[1:-1].decode('string_escape')

                message = NetworkMessage(message)[0]

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
            sleep(self.time[i])
            self.text.push_queue.put(self.data[i])

if __name__ == "__main__":

    l = Log("../logs/log_test.txt")


    
