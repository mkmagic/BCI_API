__author__ = 'Lotan'

import os, sys
from abc import ABCMeta, abstractmethod
from exceptions.ExceptionsBucket import ExceptionsBucket


class ServerInterface(metaclass=ABCMeta):
    """
    a class that serve as interface to all the Server objects.
    The class force the inheritor classes to implement some functions.
    """
    def __init__(self, id, sender, receivers, logDict):
        
        # server settings
        self._log = logDict
        self._serverId = id                                                 # The id of this server.
        self._errorsBucket = ExceptionsBucket(self.runningCondition,        # The server stopped when the exception bucket isn't empty.
                                                self.close, self._serverId, 
                                                self._log)
        self._stopRunning = False                                           #  When it true the server will stop to run.

        # communication components
        self._senderComponent = sender
        self._receiverComponents = receivers

    def runningCondition(self):
        """
        Return true if this server is still running
        """
        return not self._stopRunning

    def setComponentsRestartOption(self):
        self._senderComponent.setRestartListenerOption()
        for component in self._receiverComponents:
            component.setRestartListenerOption()

    def closeComponents(self):
        self._senderComponent.close(self._log)
        for component in self._receiverComponents:
            component.close(self._log)

    def startWelcomeListeners(self):
        for component in self._receiverComponents:
            component.restartListener(self._errorsBucket, self._log)
        self._senderComponent.restartListener(self._errorsBucket, self._log)


    @abstractmethod
    def sendData(self, data):
        """
        The method adds the given data to the messages container 
        in order to send this message to the receivers clients.
        """
        pass

    @abstractmethod
    def operate(self):
        """
        The main function of this object must been called in order to execute this server .
        """
        pass

    @abstractmethod
    def close(self):
        """
        close the server and all it's components.
        """
        pass