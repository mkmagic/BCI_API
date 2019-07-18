__author__ = 'Lotan'


from enum import Enum

class Protocol(Enum):
    UDP  = "UDP"
    TCP = "TCP"

class LogLevelTypes(Enum):
    # For Displaying the messages content and status
    # MESSAGES_STATUS = 0
    # SERVER_STATUS = 0
    # LISTENER_STATUS = 1
    # CLIENT_CONNECTION_STATUS = 1

    EXTENTED = 1
    BEHAVIOUR = 2
    FLOW_EVENT = 3
    ALGORITHEM = 4

LINKED_LIST_CLOSE_MSG = "close" # a message that added to the container when the server need to be closed.

class MessageConst:
    MESSAGE_END = "$@$"
    CLOSE_MSG = "close"