

#________________________________ imports ________________________________#

import threading
import socket

# project packages

from constants.ServerConstants import Protocol
from constants.ServerConstants import MessageConst
from constants.ServerConstants import LogLevelTypes
from servers.Listener import Listener
from structure.StoppableThread import StoppableThread
from structure.Parser import Parser

"""
This class represents a communication component between this server and one client. 
The class hold a listener that waits for connection message from a client and stores 
the connection properties in this object variables.
When a listener gets the connection message it stores the TCP socket that sends the message
as welcome socket. 
Also if this client is with TCP protocol type, the welcome socket will also store 
as the connection socket that will handle the coming messages.
If this client is with UDP protocol type the Component object will creates a new UDP socket 
with the same address as the listener socket.
Auther: Levy, Lotan
E-mail: lotan.levy@mail.huji.com
"""

class Component():
    def __init__(self, name, protocol, listenerConnAddr, logDict):
        """
        The class constructor. The constuctor sets the communication properties and  
        initiates a new listener with the given listenerConnAddr address.
        The protocol type of this communication component will set as the given protocol type.
        """
 
        # communication settings
        self._name = name
        self._protocolType = protocol                    # The communication protocol.
        self.logDict = logDict

        self._connectionSock = None                      # The connection socket, will
                                                         # handle the coming messages after the client connection.       
        self._welcomeSock = None                         # The welcome socket. Stores the socket the send the connection request.
        self._address = None                             # The address of the connection socket.
        self._connected = False                          # The connection status. true if the client is connected and false otherwise.

        # listener properties
        self._listenerConnAdress  = listenerConnAddr     # Listener Address
        self._listener = None                            # Stores the Listener objects.
        self._listenerThread = None                      # Thread that will excecutethe main Listener method.
        self._listenerWithRestartOption = False          # Listener property, ehwn it's true the listener thread will restart itself after 
                                                         # connect client to this component
        

        # Time synchronization variables
        self._connectionTimeInClientTime = None          # Stores the time of client in the connection 
        self._connectionTimeInServerTime = None          # Stores the time of server when the client connect to it. 
      
        self._connectionMutex = threading.Semaphore(1)   # Mutex on the connection properties

    def close(self, logDict):
        self.stopListener(logDict)
        self.disconnect(True)


       
    #________________________________ get methods ________________________________#

    def getName(self): return self._name

    def getListenerAddress(self): return self._listenerConnAdress 

    def getType(self): return self._protocolType


    #_____________________________ connection methods _____________________________#

    def is_connected(self):
        """
        The function return the connection status of this component. 
        true if the componnet is connected to some client and false otherwise.

        """
        self._connectionMutex.acquire()
        answer = self._connected
        self._connectionMutex.release()
        return answer

    def has_connection(self):
        """
        The function return true if the component holds a socket 
        that handle the coming messages and false otherwise. 
        """
        self._connectionMutex.acquire()
        answer = (self._connectionSock is not None)
        self._connectionMutex.release()
        return answer


    def connect(self, sock, address):
        """
        This function must benn called when the listener gets a connection request.
        The class change the comonent connection status and sets the welcome and the connection sockets.
        """
        self._connectionMutex.acquire()
        self._connected = True                          # Sets the connection statuse to connected.

        if(self._welcomeSock != None):                  # Store the welcome socket
            self._welcomeSock.close()
        self._welcomeSock = sock

        if(self._protocolType == Protocol.TCP.value):   # If the component protocol type is TCP, the 
                                                        # connection socket is the same as the welcome socket. 
            self._connectionSock = sock
        
        if(self._protocolType == Protocol.UDP.value):   # If the component protocol type is UDP, the class open a 
                                                        # new UDP socket with the same address as the listener socket.
            if(self._connectionSock == None):
                self._connectionSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
                self._connectionSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._connectionSock.bind(self._listenerConnAdress)

        self._address = address

        # Update log dictionary
        self.logDict.updateConnection(self.getName(), True)
        self.logDict.logMethod(self.getName(), "client {} is connected".format(self._name))

        self._connectionMutex.release()


    def disconnect(self, closeSocket):
        """
        This function changes the component connetion statuse to not connected
        Also if closeSocket is true this method close all the component sockets, 
        and deletes all the connection settings.
        """
        self._connectionMutex.acquire()
        if(closeSocket):
            # close sockets
            if(self._connectionSock != None): 
                self._connectionSock.close()
            if(self._protocolType == Protocol.UDP.value and self._welcomeSock != None):
                self._welcomeSock.close()
            # delete connection settings.
            self._welcomeSock = None
            self._connectionSock = None
            self._address = None

        self._connected = False # change the connection status

        # Update log dictionary
        #self.logDict.updateConnection(self.getName(), False)
        if self._address is not None:
            self.logDict.logMethod(self.getName(), "client {} is disconnected".format(self._name))

        self._connectionMutex.release()


    def recv(self):
        """
        This function checks if the connection socket send a new meesage.
        If the connection socket is None or there is no message the function will return None, 
        otherwise it'll return the socket message converted to string.
        """
        dataArr = []
        if(self._connectionSock == None):
            return dataArr
        data = ""
        while not data.endswith(MessageConst.MESSAGE_END):
            new_data = None
            try:
                if(self._protocolType == Protocol.TCP.value):
                    new_data  = self._connectionSock.recv(1024)

                if(self._protocolType == Protocol.UDP.value):
                    new_data, addr = self._connectionSock.recvfrom(1024)
            except OSError: # Solves the problem when the client disconnect
                self.disconnect(False)
                self.logDict.updateConnection(self.getName(), False)

            if(new_data != None and new_data != b''):
                data = data + str(new_data, "utf-8")

            if(len(data) == 0):# no data to receive
                return dataArr
        
        # splitting concatenated messages
        dataArr = Parser.splitMessageStream(data)

        dataArrWithTS = []

        # Converts the messages timestemp to the server timestemp.
        for message in dataArr:
            messageTimeStamp = Parser.getMsgTime(message)
            timestampInServerTS = self.getTimeInServerTime(messageTimeStamp) 
            convertedMsg = Parser.changeMSGTime(timestampInServerTS, message)

            dataArrWithTS.append(convertedMsg)
        return dataArrWithTS 


    def send(self, data):
        """
        This function send the given string data to the client that is connected to this component.
        The function return None if the component has no connection socket and otherwise it'll return 
        the connection socket response.
        """

        if(self._connectionSock == None):
            return None
        response = None

        # Converts the message timestemp to the client timestemp.
        messageTimeStamp = Parser.getMsgTime(data)

        timestampInClientTS = self.getTimeInClientTime(messageTimeStamp) 
        messageWithClientTS = Parser.changeMSGTime(timestampInClientTS, data) + MessageConst.MESSAGE_END

        # Sends message
        if(self._protocolType == Protocol.TCP.value):
            response = self._connectionSock.send(bytes(messageWithClientTS, "utf-8"))

        if(self._protocolType == Protocol.UDP.value):
            self._connectionSock.sendto(bytes(messageWithClientTS, "utf-8"), self._address)
        return response          

    #_____________________________ Listener methods _____________________________#

    def restartListener(self, errorsBucket, logDict):
        """
        This function set the component status to not connected 
        in order to enable running of a new listener.
        also the function start a new listener.
        """
        self.disconnect(False)

        if(self._listener == None):
            self._listener = Listener(self._listenerConnAdress , self, errorsBucket, logDict)     
            self._listenerThread = StoppableThread(self._listener.listen)
            if(self._listenerWithRestartOption):
                self._listener.setRestartOption()                          

        if(not self._listenerThread.stopped()):
            self._listenerThread.stop()
            self._listenerThread = StoppableThread(self._listener.listen) # threads can only be started once
        
        # start listening
        self._listenerThread.start()

    def setRestartListenerOption(self):
        """
        This function enables the Listener thread to restart a new listener thread when it finish.
        """
        self._listenerWithRestartOption = True
   
    def joinToListener(self):
        if(self._listenerThread != None):
            self._listenerThread.join()

    def stopListener(self, logDict):
        if(self._listener is not None):
            self._listener.close()
        if(self._listenerThread != None):
            self._listenerThread.stop()
            self._listenerThread.join()

        logDict.logMethod(self.getName(), "component's listener stopped", logLevel=LogLevelTypes.FLOW_EVENT.value)

    #_____________________________ Time synchronization methods _____________________________#

    def setStartTime(self, connectionTimeInClientTime, connectionTimeInServerTime):
        """
        :param startTime: dateTime object represents the client start time
        """
        self._connectionTimeInClientTime = connectionTimeInClientTime
        self._connectionTimeInServerTime = connectionTimeInServerTime

    def getTimeInServerTime(self, timeInClientTime):
        """
        Converts the given timestamp to the correspond server timestamp.
        """
        assert(self._connectionTimeInServerTime != None)
        assert(self._connectionTimeInClientTime != None)
        assert(timeInClientTime != None)

        return self._connectionTimeInServerTime + (timeInClientTime - self._connectionTimeInClientTime)

    def getTimeInClientTime(self, timeInServerTime):
        """
        Converts the given timestamp to the correspond component's client timestamp.
        """

        assert(self._connectionTimeInServerTime != None)
        assert(self._connectionTimeInClientTime != None)
        assert(timeInServerTime != None)

        return self._connectionTimeInClientTime + (timeInServerTime - self._connectionTimeInServerTime)