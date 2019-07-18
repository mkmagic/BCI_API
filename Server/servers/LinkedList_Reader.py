#________________________________ imports ________________________________#

import threading
import socket

# project packages
from servers.ContainerComponent import ContainerComponent
from constants.ServerConstants import LINKED_LIST_CLOSE_MSG
from constants.ServerConstants import LogLevelTypes


"""
The LinkedList_Reader class is intended to get messages from the container and sends them to the class client.
Each LinkedList_Reader object listen to a single client. 

Auther: Levy, Lotan
E-mail: lotan.levy@mail.huji.com
"""
class LinkedList_Reader(ContainerComponent):
    def __init__(self, container, client, sender, errorsBucket, logDict):
        """
        The class contructor. Creates a reader thread that will get messages from the container and 
        sends them to the receiver client.
        """
        ContainerComponent.__init__(self, container, client, errorsBucket, logDict, False)

        self._containerCurNode = None                       # The current container node

    def getComponentType(self):
        return "Reader of {}".format(self._component.getName())


    def messagesHandler(self):
        """
        Receives message from the client and appends it into the messages container.
        """

        if(self._containerCurNode == None):
            self._containerCurNode = self._container.get_head()

        # Reads data from the container
        data = self._containerCurNode.get_data()
        if(data == LINKED_LIST_CLOSE_MSG):        
            self.isRunning = False
            return 
        
        #send data
        try:
            if (data != None):
                response = self._component.send(data)

        except socket.error as error: 
            pass

        #Gets the next node
        self._containerCurNode = self._containerCurNode.get_next()

        # If all the readers read this message, it removing the first message of the container.
        self._container.remove_first() 
        return 
            

