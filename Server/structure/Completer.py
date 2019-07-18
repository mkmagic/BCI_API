from enum import Enum
import os, shlex, platform, glob
from abc import ABCMeta, abstractmethod

class BranchType(Enum):
    VAR = "var"
    LIST = "list"
    SET = "set"
    PATH = "path"

class Keywords(Enum):
    ID = None
    ANY = []

class Completer:
    """
    A Tab completer class for the ShellInterface
    """

    def __init__(self):
        """
        Completer Constructure
        """
        self.words = []
        self.prefix = None
        self.head = self.CommandNode("HEAD", ["HEAD"])
        self.head.parent = self.head
        self.cur = self.head
        self.curID = None
        self.BranchType = BranchType
        self.Keywords = Keywords

    @staticmethod
    def _checkWord(word, description):
        for i in range(len(description)):
            if word.upper().startswith(' '.join(description[i:]).upper()):
                return True
        return False

    def complete(self, word, index):
        """
        This method completes the given prefix input
        
            @word The current user input
            @index The index of the completion from all the completions found

        @Return the completion suggestion found at the given index or None if index > len(completions)
        """
        # Check if we are completing a new word
        prefix = word
        newWord = (prefix == "" or prefix.endswith(" "))

        if prefix != self.prefix:
            # get word completions for current prefix
            self.words, description, self.curID = self.head.findCommands(shlex.split(prefix, posix=(platform.system()!='Windows')), newWord=newWord)
            # find matching words 
            self.matching_words = self.words if newWord else [w for w in self.words if Completer._checkWord(w, description)]
            self.prefix = prefix
        try:
            if newWord and len(self.matching_words) == 0 and self.curID is not None:
                self.matching_words = ["Expecting:", "[{}]".format(self.curID)]
            return self.matching_words[index]
        except IndexError:
            return None

    def branch_out(self, id, keywords=Keywords.ID.value, type=BranchType.VAR, hidden=False, complete=True):
        """
        This methods creates a new command branch
        Use with statment on this method to change context to the created branch
        """
        if not self.cur.canBranchOut():
            raise Exception("Cannot branch out from '{}'".format(self.cur))
        if not complete:
            hidden = True
        self.enterId = id
        commandCreator = None
        if type == BranchType.VAR:
            commandCreator = self.CommandNode
        elif type == BranchType.PATH:
            commandCreator = self.PathNode
            keywords = keywords if keywords is not None else []
        elif type == BranchType.LIST:
            commandCreator = self.ListNode
        elif type == BranchType.SET:
            commandCreator = self.SetNode
            
        keywords = keywords if keywords is not None else [id]
        self.cur.addCommand(commandCreator(id, keywords, isHidden=hidden, toComplete=complete))
        return self
    
    def keywords(self):
        """
        This method returns the list of possible keywords in the current 'with' scope
        """
        return self.cur.keywords

    def id(self):
        """
        This methods returns the id of the current 'with' scope
        """
        return self.cur.id

    def printTree(self):
        """
        Prints the built command tree
        """
        self.head.printTree()

    def __enter__(self):
        self.cur = self.cur.get(self.enterId)
        return self

    def __exit__(self ,type, keyword, traceback):
        self.cur = self.cur.parent
        self.maxDepthReached = False
        return True

    class CommandNode:
        """
        A Node in the Completer class's commands tree
        """

        __metaclass__ = ABCMeta

        def __init__(self, id, keywords, isHidden=False, toComplete=True):
            """
            Constructs a new CommandNode object

                @id The name of the command
                @keywords A list of keywords the command accepts
            """
            self.id = id
            self.keywords = keywords
            self.parent = None
            self.tree = {}
            self.isHidden = isHidden
            self.toComplete = toComplete

        @abstractmethod
        def alwaysEnter(self): return False

        @abstractmethod
        def canBranchOut(self): return True
        
        def addCommand(self, node):
            """
            Adds a new command to this node's commands tree

                @node A new CommandNode to add to the tree
            """
            self.tree[node.id] = node
            node.parent = self

        def get(self, id): return self.tree[id]

        def printTree(self, level=0):
            """
            Prints the tree held by this Node

                @level The number of indents at the current level
            """
            for node in self.tree:
                for i in range(level):
                    print('\t', end="")
                print("{}({})".format(self.tree[node].id, self.tree[node].keywords))
                self.tree[node].printTree(level + 1)

        def isPrefix(self, prefix):
            for keyword in self.keywords:
                if keyword.startswith(prefix):
                    return True
            return False

        def knownCommands(self, description, command, newWord):
            """
            @Return the list of all commands of all children nodes
            """
            if self.isWildcard() and len(description) == 0 and not newWord:
                return [command]
            else:
                return [str(keyword) for keywords in [self.tree[node].keywords for node in self.tree if 
                        self.tree[node].toComplete and
                        (not self.tree[node].isHidden or 
                        (not newWord and self.tree[node].isPrefix(description[-1])))
                        ] for keyword in keywords]

        def isWildcard(self):
            """
            @Return whether or not this node accepts any command
            """
            return len(self.keywords) == 0

        def getCommand(self, command):
            """
            Checks if a given command is accepted by this node

                @command The command to check

            @Return the command that is accepted by this node, if exists, else None
            """
            if self.isWildcard():
                return command
            for keyword in self.keywords:
                if str(command).upper() == str(keyword).upper():
                    return keyword
        
        def nextExpectedId(self):
            for node in self.tree:
                return self.tree[node].id
            return self.id

        def findCommands(self, description, command=None, newWord=False):
            """
            Find all available commands from a given path description

                @description A list of commands, in order, to search this node's commands tree
            
            @Return a list of available completions
            """
            ### print("ENTER:", self.id, description, command, newWord)
            #self.printTree()
            # Recursion return condition
            if len(description) == 0 or not self.canBranchOut():
                id = None
                if len(self.tree) > 0 or (len(description) == 0 and self.canBranchOut()):
                    id = self.nextExpectedId()
                commands = self.knownCommands(description, command, newWord)
                return commands, description, id

            # Search the tree
            for node in self.tree:
                node = self.get(node)
                cmd = node.getCommand(description[0])
                ### print(node.id, cmd, node.alwaysEnter(), newWord, len(description) > 1)
                if cmd is not None and (node.alwaysEnter() or newWord or len(description) > 1):
                    commands, desc, id = node.findCommands(description[1:], cmd, newWord=newWord)
                    return commands, [cmd] + desc, id

            if len(description) >= 1 and description[0].upper() in [v.upper() for v in self.keywords]:
                return self.findCommands(description[1:], "{} {}".format(command, description[0]), newWord=newWord)

            #Check if we are completing a word with a prefix
            matches = [cmd for cmd in self.knownCommands(description, command, newWord) if cmd.upper().startswith(description[0].upper())]
            if len(description) == 1 and len(matches) > 0:
                return self.knownCommands(description, command, newWord), description, self.nextExpectedId()
            
            # Cannot find a suitable branch
            return [], description, None

    class ListNode(CommandNode):
        def knownCommands(self, description, command, newWord):
            childCommands = super(Completer.ListNode, self).knownCommands(description, command, newWord)
            return [val for val in self.keywords] + childCommands
    
    class SetNode(ListNode):
        
        def knownCommands(self, description, command, newWord):
            childCommands = super(Completer.ListNode, self).knownCommands(description, command, newWord)
            options = [val for val in self.keywords] + childCommands
            return [opt for opt in options if opt not in description + command.split(' ')]

    class PathNode(CommandNode):

        def __init__(self, id, keywords, isHidden=False, toComplete=True):
            super(Completer.PathNode, self).__init__(id, keywords, isHidden=isHidden, toComplete=toComplete)

        def alwaysEnter(self): return True

        def canBranchOut(self): return False

        def knownCommands(self, description, command, newWord):
            if newWord:
                description.append('')
            command = ' '.join([command] + description)
            splitted = [c.strip("'").strip('"') for c in shlex.split(command, posix=(platform.system()!='Windows'))]
            content = self.getDirContent(command)
            return content

        def getDirContent(self, description):
            """
            @Return the content of of the current directory
            """
            dirContent = glob.glob(description + '*')
            dirs = [dir + os.path.sep for dir in dirContent if os.path.isdir(dir)]
            files = [file for file in dirContent if os.path.isfile(file)]
            return dirs + files