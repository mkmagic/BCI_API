import os, sys
import socket
from structure.ShellInterface import ShellInterface
from backdoor.TwoWayCommunicator import TwoWayCommunicator
from backdoor.MessageProtocol import MessageProtocol
from structure.StoppableThread import StoppableThread
from structure.colors import colors

class Interface(ShellInterface):

    NAME = os.path.basename(__file__).split(".")[0] # Default is current file's name
    VERSION = "1.0.0.0"
    DESCRIPTION = 'A Remote Controller for Communication Server' # Interface Short Description

    BACKDOOR_PROTOCOL_FILE = r".\backdoor\KnownCommands.xml"
    BACKDOOR_PROTOCOL_SECTION = r"BackdoorMessageProtocol"

    STR_ACTIVE = "{}Active{}".format(colors.fg.green, colors.reset)
    STR_NOT_ACTIVE = "{}Not Active{}".format(colors.fg.red, colors.reset)
    STR_CONNECTED = "{}Connected{}".format(colors.fg.green, colors.reset)
    STR_NOT_CONNECTED = "{}Not Connected{}".format(colors.fg.red, colors.reset)

    def buildParser(self):
        """
        Builds the Interface's argument parser
        """
        self.parser.set_defaults(action=None)
        subparsers = self.parser.add_subparsers()

        with self.completer.branch_out("connect"):
            connectParser = subparsers.add_parser(self.completer.id(), help="Connect to a NMS Server")
            connectParser.set_defaults(action=self._connect)
            with self.completer.branch_out("host", keywords=self.completer.Keywords.ANY.value):
                connectParser.add_argument(self.completer.id(), help="Host address of the NMS Server")
                with self.completer.branch_out("port", keywords=self.completer.Keywords.ANY.value):
                    connectParser.add_argument(self.completer.id(), type=int, help="Port number the NMS Server is listening on")

        with self.completer.branch_out("disconnect"):
            disconnectParser = subparsers.add_parser(self.completer.id(), help="Disconnect from the connected NMS Server")
            disconnectParser.set_defaults(action=self._disconnect)
        
        with self.completer.branch_out("tap"):
            tapParser = subparsers.add_parser(self.completer.id(), help="Tap to a specific transmission")
            tapParser.set_defaults(action=self._tap)
            with self.completer.branch_out("transmissions", self.knownTransmissions, type=self.completer.BranchType.SET):
                tapParser.add_argument(self.completer.id(), nargs='+', choices=self.completer.keywords(), help="Names of the transmissions to tap, Space separated")

        with self.completer.branch_out("status"):
            statusParser = subparsers.add_parser(self.completer.id(), help="Show the status of all transmissions on the server")
            statusParser.set_defaults(action=self._status)
            with self.completer.branch_out("transmission", ["--transmission"]):
                with self.completer.branch_out("name", self.knownTransmissions):
                    statusParser.add_argument("--transmission", "-t", type=lambda x : x.upper(), choices=self.completer.keywords(), help="Transmission name to view it's status")

        self.parser.set_defaults(MEMORY={}) # list argument names (str) to keep their value in memory

    def __init__(self, statusUpdateMethod=None, serverDisconnectedMethod=None, serverReconnectedMethod=None):
        """
        Interface Constructor
        """
        self.onUpdate = statusUpdateMethod
        self.onDisconnect = serverDisconnectedMethod
        self.onReconnect =  serverReconnectedMethod
        self.connection = None
        self.serverHost = ""
        self.serverPort = 0
        self.knownTransmissions = {}
        self.communicator = None
        self.isConnected = False
        self.backdoorProtocol = MessageProtocol(Interface.BACKDOOR_PROTOCOL_FILE, Interface.BACKDOOR_PROTOCOL_SECTION)
        super(Interface, self).__init__(self.NAME, self.VERSION, description=self.DESCRIPTION)

    # Main Method
    def execute(self):
        """
        The main method of the Interface.
        It's called whenever a shell command is entered or Interface.run() is called with argv.

        @Return whether or not the execution was successful
        """

        # Use self.FLAGS to access the parsed arguments (argparse namespace)
        # Use self.input to access the given arguments (str list)
        return self.FLAGS.action()

    def _connect(self):
        return self.connect(self.FLAGS.host, self.FLAGS.port)

    def connect(self, host, port):
        if not self.isConnected:
            self.disconnect()
            if self.communicator is None or not self.communicator.isConnected:
                self.communicator = Interface.Communicator(host, port, self)
                print("Connecting to {} : {}".format(host, port))
                if self.communicator.open():
                    return True
                else:
                    self.communicator = None
                    print("Error: Could not open a connection on {} : {}".format(self.communicator.host, self.communicator.port))
            else:
                print("Error: You are already attempting to connect on {} : {}\n{}Try calling disconnect first".format(self.communicator.host, self.communicator.port, colors.fg.orange))
        else:
            print("Error: You are already connected at {} : {}".format(self.communicator.host, self.communicator.port))
        
        return False

    def getTapLog(self, transmission):
        tapLog = os.path.join(".", "logs", "TAP_{}.log".format(transmission))
        if not os.path.isfile(tapLog):
            open(tapLog, 'a').close()
        return tapLog
    
    def _tap(self):
        return self.tap(self.FLAGS.transmissions)

    def tap(self, transmissions):
        print("tapping {}".format(','.join(transmissions)))
        tapLogs = {}
        for transmission in transmissions:
            self.communicator.appendMessage(self.backdoorProtocol.createMessage("Tap", [transmission, "1"]))
            tapLogs[transmission] = self.getTapLog(transmission)
        inputHandler = None
        if len(transmissions) == 1:
            inputHandler = lambda message: self.sendTapMessage(message, transmissions[0])
        self.showLog([tapLogs[t] for t in tapLogs], online=True, inputHandler=inputHandler)
        for transmission in transmissions:
            self.communicator.appendMessage(self.backdoorProtocol.createMessage("Tap", [transmission, "0"]))
            if os.path.isfile(tapLogs[transmission]):
                os.remove(tapLogs[transmission])
        return True

    def sendTapMessage(self, message, transmission):
        self.communicator.appendMessage(self.backdoorProtocol.createMessage("Send", [transmission, message]))

    def printTransmission(self, transmission):
        if transmission in self.knownTransmissions:
            transmission = self.knownTransmissions[transmission]
            print("\n{}: {}".format(transmission.Name, self.STR_ACTIVE if transmission.Active else self.STR_NOT_ACTIVE))

            print("\tTX: {}{}- {}\n".format(transmission.Sender, ' ' * (transmission.maxClientName - len(transmission.Sender) + 1),
                                            self.STR_CONNECTED if transmission.SenderActive else self.STR_NOT_CONNECTED))
            for receiver in transmission.Receivers:
                print("\tRX: {}{}- {}".format(receiver[0], ' ' * (transmission.maxClientName - len(receiver[0]) + 1),
                                              self.STR_CONNECTED if self.backdoorProtocol.strtobool(receiver[1]) else self.STR_NOT_CONNECTED))

    def _status(self):
        return self.status(self.FLAGS.transmission)

    def status(self, transmission):
        for tranmissionName in self.knownTransmissions:
            if not transmission or tranmissionName == transmission:
                self.printTransmission(tranmissionName)
        return True

    def _disconnect(self):
        return self.disconnect()

    def disconnect(self):
        self.isConnected = False
        self.knownTransmissions.clear()
        if self.communicator is not None and self.communicator.isConnected:
            if not self.communicator.isConnected or self.communicator.close():
                print("Connection Closed")
                return True

    def close(self):
        """
        This method is called whenever the interface closes

        @Return whether or not the execution was successful
        """
        if self.keys is not None:
            self.keys.close()
        self.disconnect()

    class Communicator(TwoWayCommunicator):
        def __init__(self, host, port, controller):
            self.client = None
            self.controller = controller
            logMethod = lambda msg, error=False : self.controller.log(msg, logFile=".\logs\Conrtoller.log", error=error)
            super(Interface.Communicator, self).__init__((host, port), bind=False, logMethod=logMethod)
        
        def processMessage(self, message):
            message = self.controller.backdoorProtocol.translateMessage(message)
            if message._CODE == "Status":
                message.maxClientName = len(message.Sender)
                for receiver in message.Receivers:
                    if len(receiver[0]) > message.maxClientName:
                        message.maxClientName = len(receiver[0])
                self.controller.knownTransmissions[message.Name] = message
                if self.controller.onUpdate is not None:
                    self.controller.onUpdate()
            if message._CODE == "Event":
                self.controller.log(message.Event, id=message.Id, timestamp=message.Time, logFile=self.controller.getTapLog(message.Name))

        def connect(self):
            try:
                self.sock.connect((self.host, self.port))
                self.controller.isConnected = True
                print("Connected to server at {} : {}".format(self.host, self.port))
                if self.controller.onReconnect is not None:
                    self.controller.onReconnect()
                return True
            except socket.timeout as e:
                pass
            except socket.error as e:
                self.log("Failed to connect on port {}: {}".format(self.port, e))
            return False

        def handleDisconnection(self):
            ShellInterface.printError("The server has disconnected")
            self.isConnected = False
            self.controller.disconnect()
            if self.controller.onDisconnect is not None:
                    self.controller.onDisconnect()

if __name__ == "__main__":
    Interface().run(sys.argv)