"""
The Listener class creates an object that can listen to it's client and waiting for a connection request.
when it receives a connection request it updates the component object that represent it's client: 
1. it change the component status to connect.
2. it save the the time that is given in the message request, as the first client time. 

Auther: Levy, Lotan
E-mail: lotan.levy@mail.huji.com
"""

import socket
from structure.Parser import Parser
import datetime
from constants.ServerConstants import LogLevelTypes


class Listener:
    def __init__(self, address, client, errorsBucket, logDict):
        """
        The class contructor. initiates the class members:
        # _client: The component object that represent the listener client
        # _port: The listening port.
        # _sock: The listening socket.
        # isRunning: The listener runing status.
        # _client: a Component object that represent the client to receive the messages from.
        # _errorsBacket: an ExceptionBucket object represents the server exception bucket, 
                        the server stopped when the bucket isn't empty.
        # log: A logger object of the server
        """

        self.logDict = logDict
        self.log = logDict.logMethod if logDict is not None else print
        self.updateConnection = logDict.updateConnection if logDict is not None else None

        self._client = client
        self._addr = address
        self._errorsBucket = errorsBucket

        # init the listener socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(self._addr)

        self.isRunning = False 
        self.restartListener = False

    def setRestartOption(self):
        self.restartListener = True

    def running(self):
        """
        :@return the listener runing status.
        """
        return self.isRunning


    def close(self):
        """
        :@ this method stop the listener.
        """
        self.isRunning = False
        self.restartListener = False
        self._client.joinToListener()
        self._sock.close()
        self.logDict.logMethod(self._client.getName(), "listener of {} closed".format(self._addr), logLevel=LogLevelTypes.FLOW_EVENT.value)     

    def listen(self):
        """
        This function must been called in order to listen the client. 
        """
        # waiting for the first connection with the client
        
        self.logDict.logMethod(self._client.getName(), "listener of {} start running".format(self._addr), logLevel=LogLevelTypes.FLOW_EVENT.value)     

        try:
            self.isRunning = True
            while self.running():
                try:
                    self._sock.settimeout(0.2) 
                    self._sock.listen(1) # 1 is the number of clients to listen to
                    sock, address = self._sock.accept()
           
                    clientIsConnected = self.listen_to_client(sock, address)
                    # checks if the connection succeeded
                    if(clientIsConnected):
                        self.isRunning = False

                except socket.timeout:
                    pass
            
            self.logDict.logMethod(self._client.getName(), "listener of {} stopped".format(self._addr), logLevel=LogLevelTypes.FLOW_EVENT.value)     

            if(self.restartListener):
                self._client.restartListener(self._errorsBucket, self.logDict)

        except BaseException as be:
            self._errorsBucket.append(be)
            self.logDict.logMethod(self._client.getName(), "listener of {} stopped by exception: Error:{}".format(self._addr, be), logLevel=LogLevelTypes.FLOW_EVENT.value)     


    def listen_to_client(self, sock, address):
        """
        This function read the connection message from the client
        and initiate the client time and connection status
        :param conn: new socket object usable to send and receive data on the connection from the client.
        :param conn: The address of the client(port and host)
        :return: true if the connection message is in the right format
        """

        # gets the connection message
        request = str(sock.recv(1024), "utf-8")
        self.logDict.logMethod(self._client.getName(), "welcome msg: {} accepted by listener of {}".format(request, self._addr), logLevel=LogLevelTypes.FLOW_EVENT.value)

        #checks if the connection message is valid
        if(len(request) > 0):
            #init component parameters according to the connection request
            valid_conn_msg = self.init_client_time(sock, address, request)
            return valid_conn_msg
        return False


    def init_client_time(self, sock, address, connection_message):
        """
        This function must been called when the client connect to that reader in order to initiate its time and connection status.
        :param conn: new socket object usable to send and receive data on the connection from the client.
        :param conn: The address of the client(port and host)
        :param connection_message: the client connection message.
        """
        
        # Parse the message
        time = Parser.getMsgTime(connection_message)
        if(time == None):
            return False
  
        # connect the client
        self._client.setStartTime(time, datetime.datetime.now()) # set time
        self._client.connect(sock, address) # set connection socket and address

        # sending connection succeeded to the sender client.
        response = bytes(Parser.getStringFromDateTime(datetime.datetime.now())+ "; connection succeeded", 'ascii')
        sock.send(response)
        self.logDict.updateConnection(self._client.getName(), True)

        return True