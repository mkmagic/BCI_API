"""
The LinkedList class is intended to be a message container that enable threads to 
go on it and read messages simultaneously.
each node in this linked list contain a mutex that lock the option to get the next node,
until the node initiation is done.
After the initiation there is no restraint to get to the next node.
If all the linked list consumers read this message and the message contained in the head of this linked 
list, the messgae node will be removed by the last consumer.

The object of node class are the node of the linked list.

note: The messages timestamp are in the server time

Auther: Levy, Lotan
E-mail: lotan.levy@mail.huji.com
"""
import os, sys
import threading
from constants.ServerConstants import LogLevelTypes
from structure.Parser import Parser
from constants.ServerConstants import MessageConst



def debugPrint(msg):
    """
    This is a debugging method that created in order the deubug this class. 
    In order to follow the class flow change this method and print the given messge.
    """
    pass



class Node(object):

    def __init__(self, data, next, consumers_num, serverId, logDict):
        """
        The class contructor. initiates the class members:
        # _next_mutex: lock the option to get the next node until the node initiation is done
        # _counter_mutex: control access of multiple threads to the _entrances_counter.
        # _entrances_counter: counter that count the number of consumers that read the message in this node.

        # _data: The data of this node.
        # _next: a pointer to the next node.
        # _consumersNum: The number of consumers of this linked list. 
        """

        self._next_mutex = threading.Semaphore(0)   

        self._counter_mutex = threading.Semaphore(1) 
        self._entrances_counter = 0

        self._data = data
        self._next = next
        self._consumersNum = consumers_num
        self.logDict = logDict

    def get_data(self):
        """
        :@return the data of this node
        """
        return self._data

    def get_next(self):
        """
        :@return the next node of he linked list, 
        if the node initiation isn't done the consumer will wait here.
        """
        self._next_mutex.acquire()      
        return self._next

    def is_the_last_visitor(self):
        """
        Raise the node's consumers counter and check if this consumer is the last visitor.
        :@return: If this consumer is the last visitor, the function will return true and otherwise it'll return false.
        """
        self._counter_mutex.acquire()                
        self._entrances_counter += 1

        answer = (self._entrances_counter == self._consumersNum)

        self._counter_mutex.release()                   
        return answer

    def set_next(self, node):
        """
        set the next node and enable all the consumers thread to get to it.
        """
        self._next = node
        for i in range(self._consumersNum + 1):   # next node mutex release for all the consumers
            self._next_mutex.release()




class LinkedList():
    """
    The messages in this container are already decoded.
    """

    def __init__(self, clientsNum, serverId, logDict):
        """
        :param clientsNum: the number of clients that consumes messages from this linked list.
        """

        """
        The class contructor. initiates the class members:
        # _head_mutex: lock the option to get the the head of this linked list, until the node initiation is done.
        # _append_messges_mutex: control access of multiple threads to append a new messages to this linked list.

        # _head: The head of this linked list.
        # _tail: The tail of this linked list.
        # _serverId = the id of the server that this linked list belong to.
        # _consumersNum: The number of consumers of this linked list. 
        """
        self._head_mutex = threading.Semaphore(0)
        self._append_messges_mutex = threading.Semaphore(1)

        self._head = None
        self._tail = None
        self._serverId = serverId
        self._consumersNum = clientsNum
        self.logDict = logDict
        

    def get_head(self):
        """
        :return: the head of this linked list
        """
        self._head_mutex.acquire() 
        return self._head

    def append(self, senderName, data):
        """
        append the given data to the tail of this linked list.
        If this list was empty the data node will set as head and tail 
        and after the insetion it'll enable the consumers to get the head.
        """
        if(data !=MessageConst.CLOSE_MSG):
            self.logDict.logMethod(self._serverId, "Message {} got from {}".format(data, senderName), logLevel=LogLevelTypes.EXTENTED.value)     
            (t, m) = Parser.splitMessage(data)
            self.logDict.updateEvent(self._serverId, "[IN] : " + m, t)


        self._append_messges_mutex.acquire()
        node = Node(data, None, self._consumersNum, self._serverId, self.logDict)
        self._append_messges_mutex.release()

        if self._head is None: # The linked list is empty.
            self._head =  node
            for i in range(self._consumersNum + 1): # enable the consumers to get the head.
                self._head_mutex.release()
       
        else:
            self._tail.set_next(node) # The linked list is not empty.

        self.logDict.logMethod(self._serverId, "New node with message: {} added to the container".format(data), logLevel=LogLevelTypes.ALGORITHEM.value)     

        self._tail = node

    def remove_first(self):
        """
        check if the current consumer is last consumer of this node, 
        and if it is the last it'll remove the first node.
        """
        if(self._head.is_the_last_visitor()):

            data = self._head.get_data()

            next_node = self._head.get_next()
            self._head = next_node
            
            self.logDict.logMethod(self._serverId, "Node with message: {} removed from the container".format(data), logLevel=LogLevelTypes.ALGORITHEM.value)     
