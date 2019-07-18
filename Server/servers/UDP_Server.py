#________________________________ imports ________________________________#


import os, sys
import socket
import errno 
import datetime

# project packages

from structure.Parser import Parser
from servers.Listener import Listener
from servers.ServerInterface import ServerInterface
from constants.ServerConstants import LogLevelTypes
from structure.StoppableThread import StoppableThread
from exceptions.ExceptionsBucket import ExceptionsBucket

"""
The UDP_Server class represents a server that gets a message from one client and 
immediately sends it to the other clients.
There is no mutex during the process of receiving data and sending it to the other clients, 
inorder to keep the process efficient.

Auther: Levy, Lotan
E-mail: lotan.levy@mail.huji.com
"""
class UDP_Server(ServerInterface):
    MESSAGE_BUF_SIZE = 1024
    TIMEOUT_TIME = 3

    def __init__(self, id, sender, receivers, logDict):
        """
        The class constructor. The constuctor calls the ServerInterface contructor, and enables all the 
        component's listeners to restart themselves.
        """
        ServerInterface.__init__(self, id, sender, receivers, logDict)

        self.logDict = logDict

        # Initiates a UDP server thread that will execute the server main function.
        self._UDPServer = StoppableThread(self.operateUDPServer)

        self.setComponentsRestartOption()


    #________________________________ Abstract Methods ________________________________#

    def operate(self):
        """
        overrides the ServerInterface abstarct method.
        """

        self._errorsBucket.start_error_checker()        # Starts the exception collector.               
        self.startWelcomeListeners()                    # Starts communication components listeners.

        self._UDPServer.start()                         # Starts UDPServer thread

        # self._log.logMethod(self._serverId, "server started", logLevel=LogLevelTypes.SERVER_STATUS.value)
        return self
    
    def sendData(self, data):
        """
        overrides the ServerInterface abstarct method.
        """
        stringServerTime = Parser.getStringFromDateTime(datetime.datetime.now())
        message = stringServerTime + ";" + str(data, "utf-8")
        self.sendMessageToClients("Manual", message)

    def close(self):
        """
        overrides the ServerInterface abstarct method.
        """

        # stop the UDP server and the exception bucket thread
        self._stopRunning = True 

        # close connection components (and their listeners)
        self.closeComponents()
        # self._log.logMethod(self._serverId, "All communication components were closed",  logLevel=LogLevelTypes.SERVER_STATUS.value)

        self._UDPServer.stop()
        self._UDPServer.join()
        # self._log.logMethod(self._serverId, "Server shutting down",  logLevel=LogLevelTypes.SERVER_STATUS.value)

    #________________________________ Class Methods ________________________________#


    def operateUDPServer(self):
        """
        The function that executed by the main class thread.
        The function waits for coming messages from the dender client and sends to the reciever clients.
        """
        try:
            self._senderComponent.joinToListener()
            while(not self._stopRunning):             
                # gets message
                messagesArr = self._senderComponent.recv()
                
                # Send the message to the connected clients
                for message in messagesArr:
                    self.sendMessageToClients(self._senderComponent.getName(), message)
        except BaseException as be:
            # adding the exception to the error bucket.
            self._errorsBucket.append(be)
            self._stopRunning = True


        
    def sendMessageToClients(self, senderId, message):
        """
        Sends the given messages to all the receiver clients that connected to their communication component.
        """
        t, m = Parser.splitMessage(message)
        # self._log.updateEvent(senderId, m, t)
        for component in self._receiverComponents:
            component.send(message)
            # self._log.logMethod(self._serverId, "message:{} was sent to {}".format(message, str(component.getListenerAddress())) , logLevel=LogLevelTypes.EXTENTED.value)
