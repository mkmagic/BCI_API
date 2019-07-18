"""
The Shell Interface module, utilizes Python's argparse module to create shell-like programs.
To create a shell-like program, copy the template Interface class provided in this file
and follow the instructions marked by # comments.

Auther: Hayun, Yoav
E-mail: yoavhayun@gmail.com
"""

from __future__ import print_function, with_statement

from abc import ABCMeta, abstractmethod

import os, sys
import xml.etree.ElementTree as ET
import argparse
import platform, traceback , shlex
from datetime import datetime
import threading, traceback
import importlib
import time
import codecs

from .Completer import Completer

try:
    import builtins
    __builtin__ = builtins
except:
    import __builtin__
# try:
#     try:
#         import readline
#     except:
#         import pyreadline as readline
# except:
#     try:
#         from pip import main as pipmain
#     except:
#         from pip._internal import main as pipmain
#     error = pipmain(['install', "pyreadline"])
#     if not error:
#         try:
#             import readline
#         except:
#             import pyreadline as readline
#     else:
#         sys.exit(error)

class ShellCompleter(Completer):
    def __init__(self, controllerInterface):
        self.controller = controllerInterface
        super(ShellCompleter, self).__init__()

    def delegateControl(self, subparsers, id, interface):
        self.enterId = id
        parser = subparsers.add_parser(id, add_help=False)
        parser.set_defaults(delegate=interface)
        interface.completer.head.id = id
        interface.completer.head.keywords = [id]
        self.cur.addCommand(interface.completer.head)
        return self

from structure.colors import colors
from structure.keys import Keys

class ShellInterface():
    __metaclass__ = ABCMeta

    LAST_EXECUTER_NAME = ["Shell Interface"]

    END_CMDS = set(["q", "quit", "exit"])
    READ_CMDS = set([".read", ".r"])

    FILE_COMMENT = '#'
    FILE_COLORS = {code + '#': color for code, color in [i for i in vars(colors.fg).items() if not i[0].startswith('_')]}

    @abstractmethod
    def buildParser(self):
        """
        Builds the Interface's argument parser
        """
        pass

    def preprocessArguments(self):
        """
        Prepocesses the arguments that were passed to the Interface

        @Return whether or not the preprocessing was successful 
        """
        return True

    def manageUnparsed(self, unparsed):
        """
        Handles the arguments that couldn't be parsed by the Interface's arguments parser

          @unparsed List of unparsed arguments

        @Return whether or not the parsing was successful
        """
        return len(unparsed) == 0

    def __init__(self, name, version=None, description=None, logFile="ShellInterface.log", xmlConfiguration=None):
        """
        Interface Constructor

            @name The name of the interface
            @version The current version of the interface
            @description A description of the interface
            @logFile The default log file of the interface
            @xmlConfiguration A path to an XML configuration file, content saved in self.CONF
        """
        self.parent = []
        self.FLAGS = argparse.Namespace()
        self.input = ''
        self.XMLParser = ShellInterface.XMLParser("value", "name", lambda v: ShellInterface.XMLParser.extractionCast(v, "type"))
        self.CONF = self.loadXmlConfiguration(xmlConfiguration, section=name) if xmlConfiguration else argparse.Namespace()
        self.isFile = False
        self.success = True
        self.logLocks = {}
        self.logFile = logFile
        self.initLog()
        self.keys = None

        self.name = name if name else os.path.basename(__file__).split(".")[0]
        self.version = version
        self.description = "{}{}{}".format(self.name, 
                                           ' v' + self.version if self.version else '', 
                                           ': ' + description if description else '')
        self.parser = argparse.ArgumentParser(description=self.description, add_help=False, formatter_class=argparse.RawTextHelpFormatter)
        self.parser.add_argument("-h", "--help", action='store_true')
        self.completer = ShellCompleter(self)
        self.buildParser()

        with self.completer.branch_out(".read"):
            self.completer.branch_out("path", type=self.completer.BranchType.PATH)
        
        self.completer.branch_out("--help")
        
        with self.completer.branch_out(self.FILE_COMMENT, complete=False):
            self.completer.branch_out("Line to print" , [])
        for colorCode in self.FILE_COLORS:
            with self.completer.branch_out(self.FILE_COMMENT + colorCode, hidden=True):
                self.completer.branch_out("Line to print", [])
        

    @abstractmethod
    def execute(self):
        """
        The main method of the Interface.
        It's called whenever a shell command is entered or Interface.run() is called with argv.

        @Return whether or not the execution was successful
        """
        return True

    def _close(self):
        """
        This method is called whenever the interface closes
        """
        self.close()

    @abstractmethod
    def close(self):
        """
        This method is called whenever the interface closes
        """
        pass

    def initLog(self, logFile=None):
        """
        Create an empty a log file. 
        If the file exists, this will overwrite it.

            @logFile If given, will init the given log file and not the default
        """
        logFile = logFile if logFile is not None else self.logFile
        if logFile is not None:
            if(os.path.isfile(logFile)):
                os.remove(logFile)
            open(logFile, "a").close()

    def deleteLog(self, logFile=None):
        """
        Deletes a logFile from the disk

            @logFile If given, will delete the given log file and not the default
        """
        logFile = logFile if logFile is not None else self.logFile
        if(os.path.isfile(self.logFile)):
            os.remove(self.logFile)

    def showLog(self, logFiles=[], logLevel=0, lineNumber=0, online=False, inputHandler=None):
        """
        Displays a log file on the screen

            @logFiles List of files, If given, will show the given files instead of the default log file
            @logLevel Show all log prints with (log level <= given log level)
            @lineNumber Display log from a given line number instead of the beginning
            @online Whether or not the keep displaying the log as it updates from an external source
                    until a KeyboardInterrupt event
            @inputHandler a handler function to handle incoming input
        
        @Return the last printed line number
        """
        logFiles = logFiles if len(logFiles) > 0 else [self.logFile]
        try:
            if inputHandler is not None:
                prompt = self.getPrompt()
                if len(logFiles) == 1:
                    prompt = colors.bold
                    prompt += os.path.split(logFiles[0])[-1].split('.')[0]
                    prompt += "> " + colors.reset
                inputHandler = ShellInterface.InputHandler(prompt, inputHandler, self.keys)

            printers = {}
            for logFile in logFiles:
                if online:
                    printers[logFile] = ShellInterface.LogPrinter(logFile, lineNumber)
                    printers[logFile].start(logLevel)
                else:
                    with open(logFile, 'r') as log:
                        [log.readline() for i in range(self.lineNumber)]
                        ShellInterface.LogPrinter.printLog(log, logLevel)

            while(True):
                if inputHandler is not None and not inputHandler.isWorking:
                    break
                time.sleep(0)
        except KeyboardInterrupt:
            pass
        finally:
            if inputHandler is not None:
                inputHandler.stop()
            for printer in printers:
                printers[printer].stop()

    @staticmethod
    def tryExecution(task, maxTries, expecting=Exception):
        tries = 0
        while(tries < maxTries):
            try:
                task()
                return True
            except expecting:
                tries += 1
        return False

    @staticmethod
    def _logMsgTask(logFile, descriptor, message):
        with open(logFile, 'a') as log:
            log.write("{} {}\n".format(descriptor, message))

    def log(self, message, logFile=None, logLevel=0, error=False, id=None, timestamp=None, maxTries=1):
        """
        This method prints a message to the log file

            @message The message to log
            @logFile If given, will print to the given file instead of the default log file 
            @logLevel The minimal logLevel needed to display this message
            @error Whether or not this message is an error message
            @id An id of what produced this message
            @timestamp Whether or not to include a timestamp in the log print
        """
        logFile = logFile if logFile is not None else self.logFile
        if logFile is not None:
            if logFile not in self.logLocks:
                self.logLocks[logFile] = threading.Lock()
            message = "{}".format(message) if error else message
            descriptor = "{}::".format(logLevel)
            descriptor = "{}[{}]".format(descriptor, timestamp) if timestamp is not None else descriptor
            descriptor = "{}[{}]".format(descriptor, id) if id is not None else descriptor
            descriptor = "{} ERROR: ".format(descriptor) if error else descriptor
            with self.logLocks[logFile]:
                logTask = lambda : ShellInterface._logMsgTask(logFile, descriptor, message)
                if not ShellInterface.tryExecution(logTask, maxTries, PermissionError):
                    self.log("Unable to log message in '{}': {}".format(logFile, message.strip()), error=True)

    def __str__(self):
        """
        @Return a description of the interface
        """
        return self.description

    def readCommands(self, file):
        """
        Executes argument lines from a file

          @file Path to file containing argument lines to be executed by the interface

        @Return whether or not the execution was successful
        """
        try:
            if os.path.isfile(file):
                lines = []
                with open(file, mode='r') as f:
                    lines = f.readlines()
                self.isFile = True
                self.__shell(inputLines=lines)
                self.isFile = False
            else:
                ShellInterface.printError("'{}' is not a file".format(file))
        except:
            ShellInterface.printError("Could not read file '{}'".format(file))
            self.isFile = False
            return False
        return self.success

    def __createFlags(self):
        """
        Creates self.FLAGS for the Interface

        @Return whether or not the creation of flags was successful
        """
        self.__unparsed = []
        try:
            mem = {}
            if hasattr(self.FLAGS, "MEMORY"):
                for arg in self.FLAGS.MEMORY:
                    if hasattr(self.FLAGS, arg):
                        mem[arg] = getattr(self.FLAGS, arg)
            self.FLAGS, self.__unparsed = self.parser.parse_known_args(args=self.input, namespace=self.FLAGS)
            for arg in self.FLAGS.MEMORY:
                if not arg in mem:
                    mem[arg] = self.FLAGS.MEMORY[arg]
                if arg in mem:
                    if not hasattr(self.FLAGS, arg) or getattr(self.FLAGS, arg) is None:
                        setattr(self.FLAGS, arg, mem[arg])
        except SystemExit:
            if int(str(sys.exc_info()[1])) != 0:
                self.success = False
            return False

        return True
    
    def __processArgs(self):
        if not self.manageUnparsed(self.__unparsed):
            ShellInterface.printError("The arguments {} are unknown".format(self.__unparsed))
            if self.isFile:
                self.success = False
            return False
        
        if not self.preprocessArguments():
            ShellInterface.printError("Failed in preprocessing of '{}'.".format(self.inputLine.strip()))
            if self.isFile:
                self.success = False
            return False

        return True

    def __resetFlags(self):
        """
        Resets self.FLAGS of the Interface
        """
        for arg in self.FLAGS.__dict__:
            if arg == 'MEMORY':
                continue
            if hasattr(self.FLAGS, 'MEMORY') and arg not in self.FLAGS.MEMORY:
                setattr(self.FLAGS, arg, None)

    def runLine(self, line):
        """
        Parse and execute a single argument line

          @line argument line to parse and execute

        @Return whether or not the execution was successful
        """
        ShellInterface.LAST_EXECUTER_NAME.append(self.name)

        isLastLine = False

        self.__resetFlags()
        self.inputLine = line
        self.input = shlex.split(line, posix=(platform.system()!='Windows'))
        if self.inputLine.startswith(self.FILE_COMMENT):
            toPrint = self.inputLine[1:].strip()
            availableColors = [k for k in vars(colors.fg).items() if not k[0].startswith('_')]
            for code in self.FILE_COLORS:
                if toPrint.lower().startswith(code):
                    toPrint = self.FILE_COLORS[code]  + toPrint[len(code):].strip() + colors.reset
                    break
            print(toPrint)
        elif len(self.input) > 0:
            if self.input[0] in ShellInterface.END_CMDS and not self.isFile:
                isLastLine = True
            elif self.input[0] in ShellInterface.READ_CMDS:
                expArgs = 2
                if len(self.input) < expArgs:
                    ShellInterface.printError("Read command accepts a path as an argument.")
                else:
                    self.readCommands(' '.join(self.input[1:]))
            else:
                if self.__createFlags():
                    if hasattr(self.FLAGS, "delegate") and self.FLAGS.delegate:
                        hasKeys = self.keys is not None
                        if hasKeys: self.keys.close()
                        self.callOtherInterface(self.FLAGS.delegate ,self.input[1:])
                        #if hasKeys: self.keys = Keys(self.name, intro=self.getUsage())
                    elif self.FLAGS.help:
                        self.parser.print_help()
                    else:
                        if self.__processArgs():
                            self.success = self.execute()
        return isLastLine

    def getUsage(self):
        usage = ''
        usage += colors.fg.yellow + '\n'
        usage += self.description + '\n'
        usage += colors.reset
        usage += "\tTo exit, enter one of the following {}\n".format([cmd for cmd in ShellInterface.END_CMDS])
        usage += "\tto read commands from a file, enter one of the following {}\n".format([cmd for cmd in ShellInterface.READ_CMDS])
        usage += colors.bold + '\n'
        usage += "\tTip: At any time, add '-h' flag to the command for help.\n"
        usage += colors.reset
        return usage

    def printUsage(self):
        """
        Prints the welcome usage information of the interface
        """
        print(self.getUsage())

    def setMarkerView(self):
        sys.stdout.write("\033[2A")
        sys.stdout.flush()

    def unsetMarkerView(self):
        sys.stdout.write("\033[2B")
        sys.stdout.flush()

    def getPrompt(self, parent=[]):
        shellPromptMsg = "{}> ".format('\\'.join(parent + [self.name]))
        return colors.bold + shellPromptMsg + colors.reset

    def __shell(self, inputLines=None):
        """
        Runs the Interface as a shell program

          @parent the name of the parent Interface
          @inputLines a pre set list of input lines

        @Return whether or not the last input line was successful
        """
        if not self.isFile:
            self.keys = Keys(self.name, intro=self.getUsage())
            self.printUsage()
        try:
            shellPromptMsg = self.getPrompt(self.parent)
            while inputLines is None or len(inputLines) > 0:
                if inputLines is None:
                    print()
                try:
                    inputLine = inputLines.pop(0) if inputLines else self.keys.readInput(shellPromptMsg, self.completer)
                except EOFError:
                    break
                try:
                    lastLine = self.runLine(inputLine)
                    if lastLine:
                        break
                    if not self.success:
                        if self.isFile:
                            ShellInterface.printError("Command Failed, Aborting execution from file")
                            break
                        else:
                            ShellInterface.printError("Command Failed")
                            self.success = True
                except SystemExit:
                    if int(str(sys.exc_info()[1])) != 0:
                        raise
                except:
                    traceback.print_exc()
                    sys.exit(1)
        finally:

            if not self.isFile:
                self.keys.close()
        
        return self.success

    def loadXmlConfiguration(self, xml, section=None):
        """
        Loads an XML configuration file into the interface.

            @xml A path to an XML file
            @section Specify to load a specific section in the XML only

        @Return an argparse Namespace containing the values extracted from XML

        XML Structure:
            section : Groups arguments together
                name      - name of the section
                [Content] - 'import', 'value' and 'group' elements
            import  : Includes another section in the current section
                section   - section name to import
                [Content] - None
            value   : Holds a value for the interface to use
                name      - Access name for the value
                type      - A casting method to apply on the given string value
                [Content] - The value to store
            group   : groups several values together
                name      - Access name for the group
                [Content] - 'value' elements

        XML Example:
            <root>
                <section name="A">
                    <group name="A_Group1">
                        <value name="Arg1">value for A.A_Group1.Arg1</value>
                        <value name="Arg2">value for A.A_Group1.Arg2</value>
                    </group>
                </section>
                <section name="B">
                    <import section="A"/> <!--Access 'B.A.A_Group1.Arg1' and 'B.A.A_Group1.Arg2'-->
                    <value name="Arg1">value for B.Arg1</value>
                </section>
            </root>
        """
        return self.XMLParser.loadXml(xml, section)

    def run(self, argv=None, parent=[]):
        """
        Runs the Interface

          @argv include argv list to be executed by the given Interface
                omit argv list to pass control to the given Interface
                  # First arg is expected to be the call command
          @parent the name of the parent Interface

        @Return whether or not the parsing was successful
        """
        try:
            self.parent = parent
            if argv and len(argv) > 1:
                self.runLine(' '.join(argv))
                return self.success
            else:
                retValue = self.__shell()
                self._close()
                return retValue
        except SystemExit:
            self._close()
            if int(str(sys.exc_info()[1])) != 0:
                raise
    
    def callOtherInterface(self, other, argv=None):
        """
        Calls another Interface

          @other An Interface instance
          @argv argv list as expected by the Interface's run method

        @Return whether or not the call returned success
        """
        return other.run(argv, self.parent + [self.name])

    @staticmethod
    def printError(error):
        """
        Prints an error

          @argv error error message
        """
        executer = ShellInterface.LAST_EXECUTER_NAME.pop() if len(ShellInterface.LAST_EXECUTER_NAME) > 0 else "Shell Interface"
        print(colors.fg.lightred + "\n[{}] Error: {}".format(executer, error) + colors.reset)

    class LogPrinter:
        def __init__(self, log, lineNumber):
            self.log = log
            self.lineNumber = lineNumber

        def start(self, logLevel=0):
            self.isWorking = True
            self.worker = threading.Thread(target=self.run, args=[logLevel])
            self.worker.start()

        def stop(self):
            self.isWorking = False
            self.worker.join()

        def run(self, logLevel):
            with open(self.log, 'r') as log:
                [log.readline() for i in range(self.lineNumber)]
                while(self.isWorking):
                    ShellInterface.LogPrinter.printLog(log, logLevel=logLevel)
        
        @staticmethod
        def printLog(logFile, logLevel=0):
            content = logFile.readline()
            if content:
                content = content.split("::")
                if len(content) == 2:
                    level, content = content[0], content[1]
                    if logLevel >= int(level):
                        print(content, end='')

    class InputHandler:
        def __init__(self, prompt, handlerFunction, keys):
            self.prompt = prompt
            self.handlerFunction = handlerFunction
            self.keys = keys
            self.isWorking = True
            self.worker = threading.Thread(target=self.run, args=[])
            self.worker.start()

        def stop(self):
            self.isWorking = False
            self.worker.join()

        def run(self):
            print()
            while(self.isWorking):
                inputline = self.keys.readInput(self.prompt, hideInputLine=True)
                if inputline.strip() in ShellInterface.END_CMDS:
                    self.isWorking = False
                    break
                self.handlerFunction(inputline)


    class XMLParser():

        XML = argparse.Namespace(
            section = argparse.Namespace(tag="section", id="name"),
            include = argparse.Namespace(tag="import", id="section"),
            group = argparse.Namespace(tag="group", id="name")
        )

        def __init__(self, valueTitle, valueId, valueExtractMethod=None):
            if valueExtractMethod is None:
                valueExtractMethod = lambda value: value.text
            self.value = argparse.Namespace(title=valueTitle,
                                            id=valueId,
                                            extractMethod=valueExtractMethod)

        @staticmethod
        def castValue(value, castDescription):
            module = __builtin__
            if '.' in castDescription:
                modulePath = '.'.join(castDescription.split('.')[0:-1])
                try:
                    module = importlib.import_module(modulePath)
                except:
                    modulePath = modulePath.split('.')
                    for i in range(0, len(modulePath)):
                        module = getattr(module, modulePath[i])
            method = castDescription.split('.')[-1]
            return getattr(module, method)(value)

        @staticmethod
        def extractionCast(valueElement, castId):
            """
            Casts a value in a given XML element to it's specified type

                @valueElement XML element that has a text value and a 'type' attribute

            @Return the casting of the text value to it's specified type
            """ 
            if castId in valueElement.attrib:
                return ShellInterface.XMLParser.castValue(valueElement.text, valueElement.attrib[castId])

            return valueElement.text

        def _appendNamespace(self, namespace, id, value):
            namespace._ORDER.append(id)
            setattr(namespace, id, value)
            return namespace

        def _createNamespaceFromXmlRoot(self, xml, root, history):
            """
            Creates a new namespace containing values specified under a given XML root elemment

                @xml A path to an XML file
                @root The XML element containing values to parse out
                @history Holds already visited sections

            @Return an argparse Namespace containing the values extracted from XML
            """
            namespace = argparse.Namespace(_ORDER=[])

            for section in root.findall(self.XML.include.tag):
                id = section.attrib[self.XML.include.id]
                namespace = self._appendNamespace(namespace, id, self._loadXml(xml, id, history))

            for value in root.findall(self.value.title):
                id = value.attrib[self.value.id]
                namespace = self._appendNamespace(namespace, id, self.value.extractMethod(value))

            for group in root.findall(self.XML.group.tag):
                groupId = group.attrib[self.XML.group.id]
                namespace = self._appendNamespace(namespace, groupId, OrderedDict())
                for value in group.findall(self.value.title):
                    groupValues = getattr(namespace, groupId)
                    groupValues[value.attrib[self.value.id]] = self.value.extractMethod(value)
            return namespace

        def _loadXml(self, xml, section=None, history=[]):
            """
            Loads an XML configuration file into the interface.

                @xml A path to an XML file
                @section Specify to load a specific section in the XML only
                @history Holds already visited sections

            @Return an argparse Namespace containing the values extracted from XML
            """
            tree = ET.parse(xml)
            root = tree.getroot()
            if section:
                if section not in history:
                    history.append(section)
                    for sec in root.findall(self.XML.section.tag):
                        if sec.attrib[self.XML.section.id].upper() == section.upper():
                            return self._createNamespaceFromXmlRoot(xml, sec, history[:])
                else:
                    print("ERROR: Found a circular import in XML file: '{}'".format(xml))
                    return None
            else:
                return self._createNamespaceFromXmlRoot(xml, root, history)
            
            # We got a non existing section to read
            return argparse.Namespace()
        
        def loadXml(self, xml, section):
            """
            Loads an XML file as an argparse.Namespace

                @xml A path to an XML file
                @section Specify to load a specific section in the XML only

            @Return an argparse Namespace containing the values extracted from XML

            XML Structure:
                section : Groups arguments together
                    name      - name of the section
                    [Content] - 'import', 'value' and 'group' elements
                import  : Includes another section in the current section
                    section   - section name to import
                    [Content] - None
                value   : Holds a value for the interface to use
                    name      - Access name for the value
                    type      - A casting method to apply on the given string value
                    [Content] - The value to store
                group   : groups several values together
                    name      - Access name for the group
                    [Content] - 'value' elements

            XML Example:
                <root>
                    <section name="A">
                        <group name="A_Group1">
                            <value name="Arg1">value for A.A_Group1.Arg1</value>
                            <value name="Arg2">value for A.A_Group1.Arg2</value>
                        </group>
                    </section>
                    <section name="B">
                        <import section="A"/> <!--Access 'B.A.A_Group1.Arg1' and 'B.A.A_Group1.Arg2'-->
                        <value name="Arg1">value for B.Arg1</value>
                    </section>
                </root>
            """
            return self._loadXml(xml, section, history=[])

"""
Interface Template Class
"""
###############################################################################
### Copy the entire code found below to start a new Shell Interface program ###
###############################################################################

import os, sys
from structure.ShellInterface import ShellInterface

class Interface(ShellInterface):

    NAME = os.path.basename(__file__).split(".")[0] # Default is current file's name
    VERSION = "1.0.0.0"
    DESCRIPTION = 'A template Interface class' # Interface Short Description

    def buildParser(self):
        """
        Builds the Interface's argument parser
        """

        # Add the arguments to self.parser (argparse.ArgumentParser type)

        # use to keep values of arguments saved between commands at runtime.
        self.parser.set_defaults(MEMORY={}) # dict: {[argument dest name] : [default value]}.

    def __init__(self):
        """
        Interface Constructor
        """
        super(Interface, self).__init__(self.NAME, self.VERSION, description=self.DESCRIPTION)

    def preprocessArguments(self):
        """
        Prepocesses the arguments that were passed to the Interface

        @Return whether or not the preprocessing was successful 
        """

        # Preprocess received arguments, stored in self.FLAGS (argparse namespace)
        return super(Interface, self).preprocessArguments() # Return preprocessing result (bool)

    def manageUnparsed(self, unparsed):
        """
        Handles the arguments that couldn't be parsed by the Interface's arguments parser

          @unparsed list of unparsed arguments

        @Return whether or not the parsing was successful
        """

        # Handle unparsed arguments (str list)
        return super(Interface, self).manageUnparsed(unparsed) # Return parsing result (bool)

    # Main Method
    def execute(self):
        """
        The main method of the Interface.
        It's called whenever a shell command is entered or Interface.run() is called with argv.

        @Return whether or not the execution was successful
        """

        # Use self.FLAGS to access the parsed arguments (argparse namespace)
        # Use self.input to access the given arguments (str list)

        return True # Return execution result (bool)

    def close(self):
        """
        This method is called whenever the interface closes

        @Return whether or not the execution was successful
        """

if __name__ == "__main__":
    Interface().run(sys.argv)