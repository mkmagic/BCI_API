from abc import ABCMeta, abstractmethod
import socket, threading

from structure.StoppableThread import StoppableThread

class TwoWayCommunicator():
    __metaclass__ = ABCMeta

    @abstractmethod
    def processMessage(self, message):
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def handleDisconnection(self):
        pass

    def __init__(self, address, bind=True, logMethod=None):
        self.host = address[0]
        self.port = address[1]
        self.isConnected = False
        self.bind = bind
        self._startSocket()
        self.messages = []
        self.messagesLock = threading.Lock()
        self.messagesSemaphore = threading.Semaphore()
        self.messagesSemaphore.acquire()
        self.log = logMethod if logMethod is not None else (lambda msg, err : print("Error: {}".format(msg) if err else msg))
        
    def _startSocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if self.bind:
            self.sock.bind((self.host, self.port))
        else:
            self.sock.bind(('', 0))
        self.sock.settimeout(1)

    def open(self):
        self.receiver = StoppableThread(self.receiveCommands)
        self.sender = StoppableThread(self.sendUpdates)
        self.connector = StoppableThread(self.listenConnection)
        if not self.isConnected:
            self.connector.start()
            return True
        return False
    
    def close(self):
        if not self.connector.stopped():
            self.connector.stop()
            if self.connector.isAlive() and threading.current_thread() != self.connector:
                self.connector.join()
        if self.isConnected:
            if not self.sender.stopped():
                self.sender.stop()
                if self.sender.isAlive() and threading.current_thread() != self.sender:
                    self.sender.join()
            if not self.receiver.stopped():
                self.receiver.stop()
                if self.receiver.isAlive() and threading.current_thread() != self.receiver:
                    self.receiver.join()
        self.isConnected = False
        self.sock.close()
        self._startSocket()
        return True

    def appendMessage(self, message):
        with self.messagesLock:
            self.messages.append(message)
            self.messagesSemaphore.release()

    def receiveMessage(self):
        if self.sock is not None:
            try:
                data = ""
                while not data.endswith('\n'):
                    data += str(self.sock.recv(4096), 'utf-8')
                    if len(data) == 0:
                        return False
                
                for message in data.split('\n'):
                    if message is not None and len(message) > 0:
                        self.processMessage(message)
                return True
            except ConnectionResetError:
                return False

    def receiveCommands(self):
        while not self.receiver.stopped():
            try:
                if not self.receiveMessage():
                    self.close()
                    self.handleDisconnection()
                    self.open()
                    break
            except socket.timeout as e:
                pass

    def sendUpdates(self):
        while not self.sender.stopped():
            if self.messagesSemaphore.acquire(timeout=1):
                with self.messagesLock:
                    try:
                        msg = self.messages[0]
                        self.sock.sendall(bytes(msg, 'utf-8'))
                        del self.messages[0]
                        self.log("Sent '{}'".format(msg))
                    except socket.error as e:
                        self.messagesSemaphore.release()
                        self.log("Unable to send '{}'".format(msg), error=True)
    
    def listenConnection(self):
        while not self.connector.stopped() and not self.isConnected:
            self.isConnected = self.connect()

        if self.isConnected:
            self.receiver.start()
            self.sender.start()