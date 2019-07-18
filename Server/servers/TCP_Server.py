
#________________________________ imports ________________________________#

import os, sys
import datetime

# project packages

from exceptions.ExceptionsBucket import ExceptionsBucket
from servers.LinkedList_Writer import LinkedList_Writer
from servers.LinkedList import LinkedList
from servers.LinkedList_Reader import LinkedList_Reader
from constants.ServerConstants import LogLevelTypes
from constants.ServerConstants import MessageConst
from servers.ServerInterface import ServerInterface
from structure.Parser import Parser


"""
The TCP_Server class represents a server with a linked list messages container.
For each comunication component that sends messages from this server to a client, 
the server opens a messsges reader that reads messages from the container and sends them to 
the client that connected to this component.
Also for the component that receives messages from the sender client, the server opens a messages writer that 
ask for messages from that component and adds them to the messages container.

Auther: Levy, Lotan
E-mail: lotan.levy@mail.huji.com
"""

class TCP_Server(ServerInterface):

    def __init__(self, id, sender, receivers, logDict):
        """
        The class contructor. The constuctor calls the ServerInterface contructor, 
        creates a linkedList container and initiate the writer and readers.
        """

        ServerInterface.__init__(self, id, sender, receivers, logDict)

        # creates a server messages container       
        self._container = LinkedList(len(receivers), self._serverId, logDict)       

        self.logDict = logDict
        # Initiates a messages writer that gets messages from the sender client and adds them to the container   
        
        self.logDict.logMethod(self._serverId, "Initiates container's writer", logLevel=LogLevelTypes.FLOW_EVENT.value)     
        self._writer = LinkedList_Writer(self._container, sender, self._errorsBucket, self._log)


        # initiate  messages readers that get messages from the container and send them to their client
        self.logDict.logMethod(self._serverId, "Initiates container's readers", logLevel=LogLevelTypes.FLOW_EVENT.value)     
        self._readers = []
        for client in receivers:
            assert(client.getListenerAddress() != None)
            new_reader = LinkedList_Reader(self._container, client, sender,self._errorsBucket, self._log)
            self._readers.append(new_reader)

        self.setComponentsRestartOption()

    #________________________________ Abstract Methods ________________________________#

    def operate(self):
        """
        overrides the ServerInterface abstarct method.
        """

        self._errorsBucket.start_error_checker()    # Starts the exception collector. 
        self.startWelcomeListeners()                # Starts communication components listeners.

        self._writer.start()                        # Start writer
        for reader in self._readers:                # Start readers
            reader.start()

        self.logDict.logMethod(self._serverId, "Communication path is started")     
        return self

    def sendData(self, data):
        """
        overrides the ServerInterface abstarct method.
        """
        stringServerTime = Parser.getStringFromDateTime(datetime.datetime.now())
        messageWithTime = stringServerTime + ";" + str(data, "utf-8")
        self._container.append("Manual", messageWithTime)
        # self.logDict.updateEvent("Manual", str(data, "utf-8"), stringServerTime)

    def close(self):
        """
        overrides the ServerInterface asendstarct method.
        """
        # sends a close messages to the messages container in order to release the writer and reader thread.
        self._container.append("server", MessageConst.CLOSE_MSG) 
        self.logDict.logMethod(self._serverId, "Close message added to the container", logLevel=LogLevelTypes.ALGORITHEM.value)     

        # close connection components (and their listeners)
        self.closeComponents()      

        # close reader and writer object
        for reader in self._readers:
            reader.close()
        self.logDict.logMethod(self._serverId, "Container's readers are closed", logLevel=LogLevelTypes.FLOW_EVENT.value)     

        self._writer.close()
        self.logDict.logMethod(self._serverId, "Container's writer is closed", logLevel=LogLevelTypes.FLOW_EVENT.value)     


        # stop the exception bucket thread
        self._stopRunning = True

        self.logDict.logMethod(self._serverId, "path is closed") 

































