

import threading
import socket

from structure.StoppableThread import StoppableThread
from constants.ServerConstants import LogLevelTypes
from abc import ABCMeta, abstractmethod



class ContainerComponent(metaclass=ABCMeta):

    def __init__(self, container, client, errorsBucket, logDict, waitForComponent):
        """
        The class contructor. Creates Container component object 
        with thread that run and operate some action on the container.
        """
        self._errorsBucket = errorsBucket                     # The server that own this bucket stopped when the exception bucket isn't empty.
        self.logDict = logDict                                 # A logger object of the server.

        self._containerThread = StoppableThread(self.run)     # Thread that appends messages into the container 

        self._container = container                           # The messages container
        self._component = client                              # The client communication component that gets messages from the sender client.
        self._waitForComponent = waitForComponent             # Boolean determines if to wait for connection before starting to run.
        self._compnentListenerAddr = self._component.getListenerAddress()   # The component listener address (for logger messages)

    #_____________________________ Abstract methods _____________________________#

    @abstractmethod
    def messagesHandler(self):
        """
        container componnent message handler. Enable the component to implement it's own actions on the container
        """
        pass

    @abstractmethod
    def getComponentType(self):
        """
        container componnent message handler. Enable the component to implement it's own actions on the container
        """
        pass

    #_____________________________ Class methods _____________________________#

    def running(self):
        """
        return true if this object is still running
        """
        return self.isRunning


    def start(self):
        """
        Start the writer object.
        """
        self.isRunning = True              # Sets running status.
        self._containerThread.start()         # Starts the writer thread


    def close(self):
        """
        Close the writer object.
        """
        self.isRunning = False
        self._containerThread.stop()
        self._containerThread.join()
        self.logDict.logMethod(self._component.getName(), "Container component: {} stopped".format(self.getComponentType()), logLevel=LogLevelTypes.FLOW_EVENT.value)


    def run(self):
        """
        The main function of this object. Must been called in order handle coming messages. 

        """
        # logger starting message
        threadId = threading.get_ident()
        print("Container component:  started")
        self.logDict.logMethod(self._component.getName(), "Container component: {} started".format(self.getComponentType()), logLevel=LogLevelTypes.FLOW_EVENT.value)

        try:
            if(self._waitForComponent):          
                self._component.joinToListener()  
            while(self.running()):                  
                self.messagesHandler()

        except BaseException as be:
            self._errorsBucket.append(be)
        








