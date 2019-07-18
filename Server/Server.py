import os, sys
import socket
from enum import Enum
import socketserver, threading, time, socket
from datetime import datetime
from distutils.util import strtobool

from structure.ShellInterface import ShellInterface
from structure.colors import colors
from backdoor.TwoWayCommunicator import TwoWayCommunicator
from servers.TCP_Server import TCP_Server
from servers.UDP_Server import UDP_Server
from structure.Component import Component

from structure.StoppableThread import StoppableThread
from constants.ServerConstants import LogLevelTypes as LogLevels


from backdoor.MessageProtocol import MessageProtocol

class Empty:
    pass

class ComponentType(Enum):
    RECEIVE = "RX"
    TRANSMIT = "TX"

class Protocol(Enum):
    TCP = {"TYPE" : "TCP", "INIT" : TCP_Server}
    UDP = {"TYPE" : "UDP", "INIT" : TCP_Server}

class NmsServer(ShellInterface):

    NAME = os.path.basename(__file__).split(".")[0] # Default is current file's name
    VERSION = "1.0.0.0"
    DESCRIPTION = 'A Communication Server'
    CONF_XML_FILE = ".\servers\ServerConfiguration.xml"

    LOGS_DIR = "Logs"
    MAX_LOG_LEVEL = max(logLevel.value for logLevel in LogLevels)

    BACKDOOR_PROTOCOL_FILE = r".\backdoor\KnownCommands.xml"
    BACKDOOR_PROTOCOL_SECTION = r"BackdoorMessageProtocol"

    class Action():
        
        class Interface(Enum):
            NONE = "NONE"
        class ComponentType(Enum):
            TRANS = "TX"
            RECV = "RX"
        class List(Enum):
            LIST = "LIST"

        class Welcome(Enum):
            START = "START"
            STATUS = "STATUS"

    @staticmethod
    def getLogFile(name):
        if not os.path.exists(NmsServer.LOGS_DIR):
            os.makedirs(NmsServer.LOGS_DIR)
        return "{}.log".format(os.path.join(NmsServer.LOGS_DIR, name))

    def __init__(self):
        """
        Interface Constructor
        """
        self.transmissions = dict()
        self.ports = []
        self.logLocks = {}


        self.backdoorHandler = None
        self.tappedTransmissions = []

        self.backdoorProtocol = MessageProtocol(NmsServer.BACKDOOR_PROTOCOL_FILE, NmsServer.BACKDOOR_PROTOCOL_SECTION)


        super(NmsServer, self).__init__(self.NAME, self.VERSION, description=self.DESCRIPTION, xmlConfiguration=self.CONF_XML_FILE)

        self.hostname = self.CONF.Hostname
        self.maxLogLevel = self.CONF.MaxLogLevel

    def buildParser(self):
        """
        Builds the Interface's argument parser
        """
        self.parser.set_defaults(action=None)
        subparsers = self.parser.add_subparsers()

        with self.completer.branch_out("component"):
            parserComponent = subparsers.add_parser(self.completer.id(), help="Add a new component to the server structure")
            with self.completer.branch_out("name", []):
                parserComponent.add_argument(self.completer.id(), type=lambda x : x.upper(), help="The name of the component")
                subparsersComponent = parserComponent.add_subparsers()

                with self.completer.branch_out("TX", [self.Action.ComponentType.TRANS.value]) as branch:
                    parserTx = subparsersComponent.add_parser(self.completer.keywords()[0], help="A data transmitting component")
                    parserTx.set_defaults(action=self.addComponent, componentType=self.Action.ComponentType.TRANS)
                    with self.completer.branch_out("transmissionName", keywords=self.completer.Keywords.ANY.value):
                        parserTx.add_argument(self.completer.id(), type=lambda x : x.upper(), help="The name of the transmission")
                        with self.completer.branch_out("protocol", [Protocol.TCP.value["TYPE"], Protocol.UDP.value["TYPE"]]):
                            parserTx.add_argument(self.completer.id(), type=lambda x : x.upper(), choices=self.completer.keywords(), help="The network protocol of the component")
                            with self.completer.branch_out("port", keywords=self.completer.Keywords.ANY.value):
                                parserTx.add_argument(self.completer.id(), type=int, help="The port the component is transmitting to")

                with self.completer.branch_out("RX", [self.Action.ComponentType.RECV.value]):
                    parserRx = subparsersComponent.add_parser(self.completer.keywords()[0], help="A data receiving component")
                    parserRx.set_defaults(action=self.addComponent, componentType=self.Action.ComponentType.RECV)
                    with self.completer.branch_out("transmissionName", self.transmissions):
                        parserRx.add_argument(self.completer.id(), type=lambda x : x.upper(), choices=self.transmissions, help="The name of the transmission to receive data from")
                        with self.completer.branch_out("port", keywords=self.completer.Keywords.ANY.value):
                            parserRx.add_argument(self.completer.id(), type=int, help="The port the component is listening on")

        with self.completer.branch_out(".set"):
            parserSet = subparsers.add_parser(self.completer.id(), help="Control the settings")
            subparsersSettings = parserSet.add_subparsers()
            with self.completer.branch_out("logging"):
                parserLogging = subparsersSettings.add_parser(self.completer.id(), help="Setting: Server's maximum log level")
                parserLogging.set_defaults(action=self.setMaxLogging)
                with self.completer.branch_out("Max Level", range(-1, self.MAX_LOG_LEVEL + 1)):
                    parserLogging.add_argument("maxLogLevel", type=int, choices=self.completer.keywords(), nargs='?', metavar='[0 - {}] / -1 to turn off'.format(max(self.completer.keywords())),  help="set maximum log level value")

            with self.completer.branch_out("hostname"):
                parserHost = subparsersSettings.add_parser(self.completer.id(), help="Setting: Server's hostname")
                parserHost.set_defaults(action=self.setHostname)
                with self.completer.branch_out("Host Address" , []):
                    parserHost.add_argument("serverHostname", nargs='?', help="A Hostname value to set")

        with self.completer.branch_out("server"):
            parserServer = subparsers.add_parser(self.completer.id(), help="Operate the server")
            subparsersServer = parserServer.add_subparsers()

            with self.completer.branch_out("structure"):
                parserServerStructure = subparsersServer.add_parser(self.completer.id(), help="Display the configuration of all communication paths")
                parserServerStructure.set_defaults(action=self.structure)
                with self.completer.branch_out("--clear"):
                    parserServerStructure.add_argument(self.completer.id(), "-c", action='store_true', help="Clears the current communication paths configuration")

            with self.completer.branch_out("start"):
                parserServerStart = subparsersServer.add_parser(self.completer.id(), help="opens all transmissions, or a specific one if specified")
                parserServerStart.set_defaults(action=self.serverStart)
                with self.completer.branch_out("transmission", ["--transmission"]):
                    with self.completer.branch_out("name", self.transmissions):
                        parserServerStart.add_argument("--transmission", "-t", type=lambda x : x.upper(), choices=self.completer.keywords(), help="Transmission name to open")

            with self.completer.branch_out("restart"):
                parserServerRestart = subparsersServer.add_parser(self.completer.id(), help="restarts all transmissions, or a specific one if specified")
                parserServerRestart.set_defaults(action=self.serverRestart)
                with self.completer.branch_out("transmission", ["--transmission"]):
                    with self.completer.branch_out("name", self.transmissions):
                        parserServerRestart.add_argument("--transmission", "-t", type=lambda x : x.upper(), choices=self.completer.keywords(), help="Transmission name to open")

            with self.completer.branch_out("status"):
                parserServerStatus = subparsersServer.add_parser(self.completer.id(), help="show the log of a specific transmission")
                parserServerStatus.set_defaults(action=self.serverStatus)
                with self.completer.branch_out("transmission", self.transmissions):
                    parserServerStatus.add_argument(self.completer.id(), type=lambda x : x.upper(), choices=self.transmissions, help="Transmission name to show it's log")
                    with self.completer.branch_out("logLevel", ["--logLevel"]):
                        with self.completer.branch_out("level", range(self.MAX_LOG_LEVEL + 1)):
                            parserServerStatus.add_argument("--logLevel", "-l", type=int, choices=self.completer.keywords(), default=0, metavar='[0 - {}]'.format(max(self.completer.keywords())),  help="set log level value")

            with self.completer.branch_out("control"):
                parserServerControl = subparsersServer.add_parser(self.completer.id(), help="send messages through a specific transmission")
                parserServerControl.set_defaults(action=self.serverControl)
                with self.completer.branch_out("name", self.transmissions):
                    parserServerControl.add_argument("name", type=lambda x : x.upper(), choices=self.completer.keywords(), help="Transmission name to send a messages through")

            with self.completer.branch_out("close"):
                parserServerStop = subparsersServer.add_parser(self.completer.id(), help="stops and closes all opened transmissions, or a specific one if specified")
                parserServerStop.set_defaults(action=self.serverStop)
                with self.completer.branch_out("transmission", ["--transmission"]):
                    with self.completer.branch_out("name", self.transmissions):
                        parserServerStop.add_argument("--transmission", "-t", type=lambda x : x.upper(), choices=self.completer.keywords(), help="Transmission name to stop")

        with self.completer.branch_out("backdoor"):
            parserBackdoor = subparsers.add_parser(self.completer.id(), help="Manage a backdoor connection for a remote controller")
            subparsersBackdoor = parserBackdoor.add_subparsers()
            with self.completer.branch_out("open"):
                parserBackdoorOpen = subparsersBackdoor.add_parser(self.completer.id(), help="Opens the backdoor access")
                parserBackdoorOpen.set_defaults(action=self.backdoorOpen)
                with self.completer.branch_out("port", keywords=self.completer.Keywords.ANY.value):
                    parserBackdoorOpen.add_argument(self.completer.id(), type=int, help="Port for the backdoor")
            
            with self.completer.branch_out("close"):
                parserBackdoorClose = subparsersBackdoor.add_parser(self.completer.id(), help="Closes the backdoor access")
                parserBackdoorClose.set_defaults(action=self.backdoorClose)

        self.parser.set_defaults(MEMORY={"maxLogLevel" : self.CONF.MaxLogLevel,
                                         "serverHostname" : self.CONF.Hostname})



    def preprocessArguments(self):
        """
        Prepocesses the arguments that were passed to the Interface

        @Return whether or not the preprocessing was successful 
        """
        if self.FLAGS.action == self.addComponent:
            if self.FLAGS.componentType == self.Action.ComponentType.TRANS and self.FLAGS.transmissionName in self.transmissions:
                ShellInterface.printError("There already exists a transmission named '{}'. Transmission names are unique.".format(self.FLAGS.transmissionName))
                return False

            if self.FLAGS.port in self.ports:
                ShellInterface.printError("Port '{}' is already taken.".format(self.FLAGS.port))
                return False

        return True

    def manageUnparsed(self, unparsed):
        """
        Handles the arguments that couldn't be parsed by the Interface's arguments parser

          @unparsed list of unparsed arguments

        @Return whether or not the parsing was successful
        """

        # Handle unparsed arguments (str list)

        return super(NmsServer, self).manageUnparsed(unparsed) # Return parsing result (bool)

    def close(self):
        self.backdoorClose()
        self.serverStop()
        return super(NmsServer, self).close()

    def serverControl(self):
        try:
            while(True):
                if self.FLAGS.name in self.transmissions:
                    # inputHandler = lambda message: self.sendTapMessage(message, transmissions[0])
                    # self.showLog([tapLogs[t] for t in tapLogs], online=True, inputHandler=inputHandler)
                    msg = input("Send {}: ".format(self.FLAGS.name))
                    if msg in ShellInterface.END_CMDS:
                        break
                    data = bytes(msg, "utf-8")
                    self.transmissions[self.FLAGS.name].sendData(data)
                else:
                    self.printError("Cannot control an inactive transmission.")
                    return False
        except KeyboardInterrupt:
            pass
        return True

    @staticmethod
    def createComponent():
        return {NmsServer.Action.ComponentType.RECV : {} , NmsServer.Action.ComponentType.TRANS : {}}

    # Main Method
    def execute(self):
        """
        The main method of the Interface.
        It's called whenever a shell command is entered or Interface.run() is called with argv.

        @Return whether or not the execution was successful
        """
        if self.FLAGS.action:
            return self.FLAGS.action()
        return True

    def structure(self):
        if self.FLAGS.clear:
            for transmission in self.transmissions:
                if self.transmissions[transmission].isActive and not self.transmissions[transmission].close():
                    ShellInterface.printError("Cannot clear structure while a communication path is active ('{}')".format(transmission))
                    return False
            self.transmissions = dict()
            self.ports = []
        else:
            for transmission in self.transmissions:
                print(self.transmissions[transmission])
        return True

    def getComponentArgs(self, name, protocol, hostname, port):
        args = Empty()
        args.name = name
        args.protocol = protocol
        args.socket = (hostname, port)
        return args

    def addComponent(self):
        self.ports.append(self.FLAGS.port)
        if self.FLAGS.componentType == self.Action.ComponentType.TRANS:
            self.transmissions[self.FLAGS.transmissionName] = NmsServer.Transmission(self, self.FLAGS.transmissionName, Protocol[self.FLAGS.protocol])
            self.transmissions[self.FLAGS.transmissionName].defineSender(self.FLAGS.name, self.hostname, self.FLAGS.port)
            self.initLog(self.transmissions[self.FLAGS.transmissionName].logFile)
        else:
            self.transmissions[self.FLAGS.transmissionName].addReceiver(self.FLAGS.name, self.hostname, self.FLAGS.port)

        return True

    def setHostname(self):
        try:
            socket.gethostbyname(self.FLAGS.serverHostname)
        except socket.error:
            ShellInterface.printError("Could not resolve host '{}'.".format(self.FLAGS.serverHostname))
            return False
        self.hostname = self.FLAGS.serverHostname
        print(self.hostname)
        return True

    def serverStart(self):
        for tranmissionName in self.transmissions:
            if not self.FLAGS.transmission or tranmissionName == self.FLAGS.transmission:
                self.transmissions[tranmissionName].start()
        return True

    def setMaxLogging(self):
        self.maxLogLevel = self.FLAGS.maxLogLevel
        print(self.maxLogLevel)
        return True

    def serverStop(self):
        for tranmissionName in self.transmissions:
            if not hasattr(self.FLAGS, "transmission") or not self.FLAGS.transmission or tranmissionName == self.FLAGS.transmission:
                self.transmissions[tranmissionName].close()
        return True

    def serverRestart(self):
        if self.serverStop():
            return self.serverStart()

    def serverStatus(self):
        self.showLog([self.transmissions[self.FLAGS.transmission].logFile], logLevel=self.FLAGS.logLevel, online=True)
        return True

    def backdoorOpen(self):
        if self.backdoorHandler is None:
            self.backdoorHandler = NmsServer.BackDoor((self.hostname, self.FLAGS.port), self)
            if self.backdoorHandler.open():
                print("Backdoor is now opened on port {}".format(self.FLAGS.port))
            return True
        else:
            ShellInterface.printError("There's already an opened backdoor at port {}".format(self.backdoorHandler.port))
            return False

    def backdoorClose(self):
        if self.backdoorHandler is not None and self.backdoorHandler.close():
            self.backdoorHandler = None
            print("Backdoor is now closed")
        return True

    def updateTappedTransmission(self, transmission, active=True):
        if transmission in self.transmissions:
            if active and transmission not in self.tappedTransmissions:
                self.tappedTransmissions.append(transmission)
            elif not active and transmission in self.tappedTransmissions:
                self.tappedTransmissions.remove(transmission)

    def log(self, message, logFile=None, logLevel=0, error=False, id=None, timestamp=None, maxTries=1):
        if logLevel <= self.maxLogLevel:
            super(NmsServer, self).log(message, logFile=logFile, logLevel=logLevel, error=error, id=id, timestamp=timestamp, maxTries=maxTries)


    class Transmission:

        TAPPED_TRANSMISSION = ""

        def __init__(self, handler, name, protocol):
            self.isActive = False
            self.handler = handler
            self.name = name
            self.protocol = protocol
            self.sender = None
            self.receivers = {}
            self.server = None

            self.logFile = NmsServer.getLogFile(self.name)
            self.logDict = self.__createLogDict()

        def start(self):
            if self.server is None:
                self.sender.instance = Component(self.sender.id, self.protocol.value["TYPE"], (self.sender.host, self.sender.port), self.logDict)
                receiversList = []
                for receiver in self.receivers:
                    receiver = self.receivers[receiver]
                    receiver.instance = Component(receiver.id, self.protocol.value["TYPE"], (receiver.host, receiver.port), self.logDict)
                    receiversList.append(receiver.instance)
                self.server = self.protocol.value["INIT"](self.name, self.sender.instance, receiversList, logDict=self.logDict)
                self.server.operate()
                self.isActive = True
                print("Communication Path '{}' is now opened".format(self.name))
                self.updateStatus()

        def sendMessage(self, message):
            if self.server is not None:
                self.server.sendData(bytes(message, 'utf-8'))
            else:
                ShellInterface.printError("Cannot send '{}' over inactive transmission '{}'".format(message, self.name))

        def close(self):
            if self.server is not None:
                self.server.close()
                self.sender.isConnected = False
                for receiver in self.receivers:
                    self.receivers[receiver].isConnected = False
                self.server = None
                print("Transmission '{}' is now closed".format(self.name))
            self.isActive = False
            self.updateStatus()
            return True

        def getStatus(self, item):
            return "{} ({} : {}) - {}{}".format(item.id, item.host, item.port, 
                                                (colors.fg.green + "Connected") if item.isConnected else (colors.fg.red + "Not Connected"), colors.reset)

        def defineSender(self, id, host, port):
            sender = Empty()
            sender.isConnected = False
            sender.id = id
            sender.host = host
            sender.port = port
            sender.instance = None
            sender.status = lambda item=sender: self.getStatus(item)
            self.sender = sender

        def addReceiver(self, id, host, port):
            receiver = Empty()
            receiver.isConnected = False
            receiver.id = id
            receiver.host = host
            receiver.port = port
            receiver.instance = None
            receiver.status = lambda item=receiver: self.getStatus(item)
            self.receivers[id] = receiver

        def updateConnection(self, id, status):
            isValidId = False
            if id == self.sender.id:
                self.sender.isConnected = status
                isValidId = True
            elif id in self.receivers:
                self.receivers[id].isConnected = status
                isValidId = True
            else:
                raise KeyError("Tranmission '{}' has no client with ID '{}'".format(self.name, id))
            self.updateStatus()
        
        def updateStatus(self):
            if self.handler.backdoorHandler is not None:
                statusMessage = self.handler.backdoorProtocol.createMessage("Status", [
                    self.name, str(self.isActive),
                    self.sender.id, str(self.sender.isConnected), 
                    [' '.join([self.receivers[r].id, str(self.receivers[r].isConnected)]) for r in self.receivers]
                ])
                self.handler.backdoorHandler.appendMessage(statusMessage)
        
        def updateEvent(self, id, event, timestamp):
            if self.handler.backdoorHandler is not None:
                if self.name in self.handler.tappedTransmissions:
                    eventMessage = self.handler.backdoorProtocol.createMessage("Event", [self.name, id, event, timestamp])
                    self.handler.backdoorHandler.appendMessage(eventMessage)

        def __repr__(self):
            colPos = colors.fg.green
            colNeg = colors.fg.red
            rep = "{} ({}): {}{}\n".format(self.name, self.protocol.value["TYPE"], (colPos + "Active") if self.isActive else (colNeg + "Not Active"), colors.reset)
            rep += "Sender:\n\t{}\n".format(self.sender.status())
            rep += "Receivers:\n"
            for receiver in self.receivers:
                rep += "\t{}\n".format(self.receivers[receiver].status())
            return rep
        
        def __str__(self):
            return self.__repr__()

        def __createLogDict(self):
            logDict = Empty()
            logDict.logMethod = lambda id, msg, logLevel=0, error=False, logFile=self.logFile: self.handler.log(msg, logFile=logFile, logLevel=logLevel, error=error, id=id, timestamp=datetime.now(), maxTries=3)
            logDict.updateConnection = lambda id, status : self.updateConnection(id, status)
            logDict.updateEvent = lambda id, event, timestamp : self.updateEvent(id, event, timestamp)
            return logDict

        def __eq__(self, other):
            if isinstance(other, basestring):
                return self.name == other
            else:
                return self.name == other.name

        def __ne__(self, other):
            return not self.__eq__(other)


    class BackDoor(TwoWayCommunicator):
        def __init__(self, address, nmsServer):
            self.sock = None
            self.address = address
            self.nmsServer = nmsServer
            logMethod = lambda msg, error=False : self.nmsServer.log(msg, logFile=NmsServer.getLogFile("BackDoor"), error=error)
            super(NmsServer.BackDoor, self).__init__(self.address, logMethod=logMethod)
        
        def processMessage(self, message):
                message = self.nmsServer.backdoorProtocol.translateMessage(message)
                if message._CODE == "Tap":
                    self.nmsServer.updateTappedTransmission(message.Name, active=message.Active)
                elif message._CODE == "Send":
                    self.nmsServer.transmissions[message.Name].sendMessage(message.Message)

        def connect(self):
            try:
                self.sock.listen(1)
                self.sock, address = self.sock.accept()
                self.log("Connection to {} accepted".format(address))
                self.sock.settimeout(1)
                self.sendStatus()
                return True
            except socket.timeout as e:
                pass
            except socket.error as e:
                self.log("Failed to connect on port {}: {}".format(self.port, e))
            return False

        def sendStatus(self):
            transmissions = self.nmsServer.transmissions
            for transmission in self.nmsServer.transmissions:
                self.nmsServer.transmissions[transmission].updateStatus()

if __name__ == "__main__":
    NmsServer().run(sys.argv)


