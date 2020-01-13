from Server.constants.ServerConstants import Protocol, MessageConst
from Server.structure.StoppableThread import StoppableThread
from .Parser import Parser
import socket
import datetime

bytesToStr = lambda bytes : str(bytes, 'utf-8')
strToBytes = lambda string : bytes(string, 'utf-8')
try:
    bytesToStr(b"test")
except Exception as e:
    bytesToStr = str
    strToBytes = bytes






class Client:

    """
    class constructor. If the getInput argument is true it'll initiate a thread that will receive messages from the user.
    """
    def __init__(self, serverHost, serverPort, clientName, protocol):
        self._serverPort = serverPort
        self._serverHost = serverHost
        self._name = clientName
        self._isConnect = False
        self._connSocket = None

        if protocol == "UDP":
            self._protocol = Protocol.UDP.value
        elif protocol == "TCP":
            self._protocol = Protocol.TCP.value




    def setUp(self):
        # Init the socket for creating connection with the server
        self._connSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._connSocket.bind(("", 0))

        # Init the socket for sending\ receiving messages
        self._messagesSocket = self._connSocket
        if self._protocol == Protocol.UDP.value:
            self._messagesSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._messagesSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            socketName = self._connSocket.getsockname()[1]
            self._messagesSocket.bind(("", self._connSocket.getsockname()[1]))


    """
    Trying to send close message to the server and then close the input thread and all the sockets
    """
    def close(self):

        # try:
        #     if self._isConnect:
        #         self._messagesSocket.send(bytes("close", 'utf-8'))
        # except OSError:
        #     pass

        self._isConnect = False


        try:
            self._connSocket.close()
            self._messagesSocket.close()
        except BaseException as e:
            print("closing some socket failed - socket is already close")


    """
    Connects this object to the server.
    """
    def connect(self, printMsgs=True):
        self.setUp()
        welcomeMsg = "{};{}".format(str(datetime.datetime.now()), self._name)

        try:
            # Connect to server and send data
            self._connSocket.connect((self._serverHost, self._serverPort))
            self._connSocket.sendall(strToBytes(welcomeMsg + "\n"))
            if printMsgs:
                print("Sent:     {}".format(welcomeMsg))

            # Waiting for succeed connection message
            while True:
                received = bytesToStr(self._connSocket.recv(1024))
                if received and printMsgs:
                    print("Received: {}".format(received))
                    break

            self._isConnect = True
            print("Connected to {} : {}".format(self._serverHost, self._serverPort))
            self._messagesSocket.settimeout(1)

        except BaseException as e:
            print("Connector for ({}, {}) stopped by an error".format(self._serverHost, self._serverPort))
            print(e)
            self.close()
            raise

class Transmitter(Client): 
    def __init__(self, serverHost, serverPort, clientName, protocol):
        Client.__init__(self, serverHost, serverPort, clientName, protocol)  

    """
    Sends messages from the messages socket (not for the connection messages) to the server
    """
    def send(self, data):
        if data:
            response = 0

            if not self._isConnect:
                return response

            message = "{};{}".format(datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d %H:%M:%S.%f"), data)+MessageConst.MESSAGE_END
            try:
                if self._protocol == Protocol.TCP.value:
                    response = self._messagesSocket.send(strToBytes(message))
                if self._protocol == Protocol.UDP.value:
                    response = self._messagesSocket.sendto(strToBytes(message), (self._serverHost, self._serverPort))
            except BaseException as e:
                print(e)
                raise

class Receiver(Client):

    def __init__(self, serverHost, serverPort, clientName, protocol):
        Client.__init__(self, serverHost, serverPort, clientName, protocol)
        self._listenerThread = None


    def listen(self, msgHandlerFunc):
        self._listenerThread = StoppableThread(lambda func=msgHandlerFunc: self._listen(func))
        self._listenerThread.start()

    """
    Listens to the server and handles it's messages with the given msgHandlerFunc function.
    If this is a close message the listener will close this object.
    The function returns tuple of the message's time as string and the message
    """
    def _listen(self, msgHandlerFunc):

        dataArr = []
        if(self._messagesSocket == None):
            return dataArr
        try:
            while self._isConnect and not self._listenerThread.stopped():
                data = ""
                while not data.endswith(MessageConst.MESSAGE_END):

                    if(not self._isConnect or self._listenerThread.stopped()):
                        break
                    new_data = None
                    try:
                        if(self._protocol == Protocol.TCP.value):
                            new_data  = bytesToStr(self._messagesSocket.recv(1024))
                        if(self._protocol == Protocol.UDP.value):
                            new_data = self._messagesSocket.recvfrom(1024)
                            if isinstance(new_data, tuple):
                                new_data = bytesToStr(new_data[0])
                            else:
                                new_data = bytesToStr(new_data)
 
                    except socket.timeout:
                        continue
                    except OSError as e: # Solves the problem when the client disconnect
                        pass

                    if(new_data != None and new_data != b''):
                        data = data + new_data 

                    if(len(data) == 0):# no data to receive
                        return dataArr
                
                # splitting concatenated messages
                dataArr = Parser.splitMessageStream(data)

                dataArrWithTS = []

                # Converts the messages timestemp to the server timestemp.
                for message in dataArr:
                    time, data = Parser.splitMessage(data)
                    data = data.split(MessageConst.MESSAGE_END)[0] # Removes message ending
                    if data == 'close':
                        print("Receive close message - client is shutting down\n")
                        self.close()
                        break
                    else:
                        msgHandlerFunc((time, data))

        except BaseException as e:
            print("Listener for ({}, {}) stopped by an error".format(self._serverHost, self._serverPort))
            print(e)
            raise


    """
    Trying to send close message to the server and then close the input thread and all the sockets
    """
    def close(self):

        # try:
        #     if self._isConnect:
        #         self._messagesSocket.send(bytes("close", 'utf-8'))
        # except OSError:
        #     pass

        self._isConnect = False

        if self._listenerThread is not None:
            self._listenerThread.stop()
            self._listenerThread.join()

        try:
            self._connSocket.close()
            self._messagesSocket.close()
        except BaseException as e:
            print("closing some socket failed - socket is already close")












