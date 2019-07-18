#________________________________ imports ________________________________#

import os, sys
import threading
import socket

# project packages
from servers.ContainerComponent import ContainerComponent
from constants.ServerConstants import LogLevelTypes

from structure.Parser import Parser


"""
The LinkedList_Writer class is intended to get client messages and add them to the class container.
Each LinkedList_Writer object listen to a single client. 

Auther: Levy, Lotan
E-mail: lotan.levy@mail.huji.com
"""
class LinkedList_Writer(ContainerComponent):

    def __init__(self, container, client, errorsBucket, logDict):
        """
        The class contructor. Creates a writer thread that will get messages from the sender client and 
        append them into the messages container.
        """
        ContainerComponent.__init__(self, container, client, errorsBucket, logDict, True)

    def getComponentType(self):
        return "Writer of {}".format(self._component.getName())

    
    def messagesHandler(self):
        """
        Receives message from the client and appends it into the messages container.
        """
        try:
            messageArr = self._component.recv()
            for message in messageArr:
                if(message is not None):
                    t, m = Parser.splitMessage(message)
                    self._container.append(self._component.getName(), message)

        except socket.error as error: # Error that happends when TCP client disconect.
            pass 





    
