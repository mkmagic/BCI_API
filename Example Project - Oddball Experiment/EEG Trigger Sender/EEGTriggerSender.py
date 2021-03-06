import sys
import os
sys.path.insert(0, '/'.join(os.getcwd().split('\\')[:-2])) # Add 'BCI_API' to the PATH

from Python_Client.Client import Receiver
from psychopy import core
from psychopy import parallel


SERVER_HOST = '10.0.0.1'
SERVER_PORT = 8012


HIGH_BEEP_TRIGGER = 20
LOW_BEEP_TRIGGER = 10
STIMULUS_TRIGGER = 30
TRIGGER_LEN = 1.0 / 256
TRIGGER_PORT = 53504

triggerPort = parallel.ParallelPort(TRIGGER_PORT)


class EEGTriggerSender:

    def __init__(self, serverHost, serverPort):
        self._listener = Receiver(serverHost, serverPort, 'EEGTriggerSender', 'UDP')
        self._listener.connect(True)



    def listen(self):
        print("Listening")
        self._listener.listen(self.sendTrigger)



    def sendTrigger(self, data):
        triggerPort.setData(int(data[1]))
        print('sent '+ data[1])
        core.wait(TRIGGER_LEN)
        triggerPort.setData(0)

    def close(self):
        self._listener.close()







if __name__ == '__main__':
    sender = EEGTriggerSender(SERVER_HOST, SERVER_PORT)
    sender.listen()

    try:
        while(True): pass
    finally:
        sender.close()