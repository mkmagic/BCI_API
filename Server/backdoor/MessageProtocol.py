import argparse
from structure.ShellInterface import ShellInterface
from distutils.util import strtobool as strtoboolMethod


class MessageProtocol:
    
    SEPARATOR = '@@'

    def __init__(self, protocolXml, section):
        xmlParser = ShellInterface.XMLParser("arg", "name", self.parseArgDescription)
        self.KnownMessages = xmlParser.loadXml(protocolXml, section)
    
    def parseArgDescription(self, valueElement):
        argDescription = argparse.Namespace()
        argDescription.type = valueElement.text
        argDescription.size = valueElement.attrib["size"] if "size" in valueElement.attrib else 1
        return argDescription

    def createMessage(self, code, arguments):
        message = code
        if not hasattr(self.KnownMessages, code): return None
        messageFormat = getattr(self.KnownMessages, code)
        for argName in messageFormat._ORDER:
            numOfItems = getattr(messageFormat, argName).size
            numOfItems = max(1, len(arguments)) if numOfItems == '+' else numOfItems
            args = arguments.pop(0)
            if type(args) != list:
                args = [args]
            for arg in args:
                try:
                    value = ShellInterface.XMLParser.castValue(arg, getattr(messageFormat, argName).type)
                    message += "{}{}".format(self.SEPARATOR, arg)
                except IndexError:
                    print("ERROR: Not enough arguments for message of type {}".format(code))
                    return None
                except Exception as e:
                    print("ERROR: Could not convert argumnet '{}' using '{}'\n".format(arg, getattr(messageFormat, argName).type))
                    raise
        return message + '\n'

    def translateMessage(self, message):
        message = message.strip('\n')
        message = message.split(self.SEPARATOR)
        type = message[0]
        if not hasattr(self.KnownMessages, type): return None
        translation = argparse.Namespace()
        translation._CODE = type
        if len(message) > 1:
            arguments = message[1:]
            messageFormat = getattr(self.KnownMessages, type)
            for i, argName in enumerate(messageFormat._ORDER):
                numOfItems = getattr(messageFormat, argName).size
                numOfItems = max(1, len(arguments)) if numOfItems == '+' else numOfItems
                values = []
                for j in range(numOfItems):
                    try:
                        arg = arguments.pop(0)
                        values.append(ShellInterface.XMLParser.castValue(arg, getattr(messageFormat, argName).type))
                    except IndexError:
                        print("ERROR: Not enough arguments for message of type {}".format(type))
                        return None
                    except:
                        print("ERROR: Could not convert argumnet '{}' using '{}'".format(arg, getattr(messageFormat, argName).type))
                        raise
                value = values if len(values) > 1 or getattr(messageFormat, argName).size != 1 else values[0]
                setattr(translation, argName, value)
        return translation

    @staticmethod
    def strtobool(string):
        return strtoboolMethod(string)
