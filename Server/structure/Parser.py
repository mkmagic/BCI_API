__author__ = 'Lotan'

import re
import datetime
from constants.ServerConstants import MessageConst

class Parser:

    @staticmethod
    def splitMessage(message):
        message_with_no_time = ';'.join(message.split(';')[1:]) if len(message.split(';')) > 1 else None
        time = message.split(';')[0]
        return (time, message_with_no_time)

    @staticmethod
    def splitMessageStream(message):
        splittedMessage = message.split(MessageConst.MESSAGE_END)
        if(len(splittedMessage[len(splittedMessage)-1]) == 0):# The last substring is an empty string
            return splittedMessage[:-1] 
        return splittedMessage




    @staticmethod
    def changeMSGTime(newTime, message):
        _, message_with_no_time = Parser.splitMessage(message)
        new_message = Parser.getStringFromDateTime(newTime) + ';' + message_with_no_time
        return new_message

    @staticmethod
    def getMsgTime(message):
        """
        :param message:
        :return: a dateTime object represents the time that is given by the string argument
        """
        try:
            time, message = Parser.splitMessage(message)
            if message is None:
                return None
            time = datetime.datetime.strptime(time,"%Y-%m-%d %H:%M:%S.%f")
        except ValueError as e:
            print("message " + message + "gets None in parsing and except the exception: \n")
            print(e)
            return None
        return time

    @staticmethod
    def getStringFromDateTime(dateTimeObj):
        """
        :param message:
        :return: a dateTime object represents the time that is given by the string argument
        """
        try:
            time = datetime.datetime.strftime(dateTimeObj, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            return None
        return time

    @staticmethod
    def get_port_from_welcome_MSG(message):
        """
        message with the form <time>; <path_id>; <port>
        :param message: to be parsed
        :return: tuple of the path id and the port as int objects
        """
        try:
            address = int(message.split(';')[2])
        except ValueError:
            return None
        return address