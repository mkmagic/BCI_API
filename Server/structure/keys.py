import os, sys, io, msvcrt 
import threading
import time
from structure.terminalSize import get_terminal_size as consoleSize
from structure.colors import colors
consoleWidth = lambda : consoleSize()[0]
consoleHeight = lambda : consoleSize()[1]
import textwrap

from contextlib import redirect_stdout
from pyparsing import *

class Keys:
    
    LOGS_DIR = ".\.Keys"

    CONSOLE_LOCK = threading.Lock()

    TAB = 9
    BACKSPACE =  8
    ESC = 27
    ENTER = 13

    FLIP = {b'\xe0'}
    IGNORE = {b'\x00'}

    UP = -72
    DOWN = -80
    RIGHT = -77
    LEFT = -75

    HOME = -71
    END = -79
    PAGEUP = -73
    PAGEDOWN = -81
    INSERT = -82
    DEL = -83

    F = list(range(-70, -58))

    LINE_COLOR = colors.fg.yellow

    def __init__(self, historyName=None, intro=None):
        if not os.path.isdir(Keys.LOGS_DIR):
            os.makedirs(Keys.LOGS_DIR)
        self.marker = 0
        self.inputBuffer = ""
        self.prompt = "> "
        self.intro = intro
        self.console = sys.stdout
        self.stdoutRedirectFile = os.path.join(Keys.LOGS_DIR, '.output_{}'.format(time.time()))
        self.historyFile = None
        if historyName is not None:
            self.historyFile = os.path.join(Keys.LOGS_DIR, '.history_{}'.format(historyName))
        self.history = Keys.HistoryManager(self.historyFile)
        self.tempStdout = open(self.stdoutRedirectFile, 'w')
        sys.stdout = self.tempStdout
        self.prints = open(self.stdoutRedirectFile)
        
        self.isWorking = False
        self.printer = Keys.Printer(self)
        # self.console.write('\033[2J') # Enable to clear the screen


    def close(self):
        self.printer.stop()
        self.prints.close()
        sys.stdout = self.console
        self.tempStdout.close()
        try:
            if os.path.isfile(self.stdoutRedirectFile):
                os.remove(self.stdoutRedirectFile)
        except Exception as e:
            print(e)

    @staticmethod
    def readKey():
        keycode = msvcrt.getch()
        while keycode in Keys.IGNORE:
            keycode = msvcrt.getch()
        if keycode in Keys.FLIP:
            return -ord(msvcrt.getch())
        return ord(keycode)
    
    @staticmethod
    def getChar(key):
        return chr(key)

    def readInput(self, prompt="> ", completer=None, hideInputLine=False):
        self.printer.flush()
        self.prompt = prompt
        self.inputBuffer = ""
        self.marker = 0
        with Keys.CONSOLE_LOCK:
            self.refresh()
            self.console.flush()
        
        self.isWorking = True
        while True:
            keypress = Keys.readKey()
            with Keys.CONSOLE_LOCK:

                if keypress == Keys.ENTER:
                    input = self.inputBuffer
                    if len(self.inputBuffer) > 0:
                        self.history.append(input)
                    #self.inputBuffer = self.LINE_COLOR + input + colors.reset
                    #self.refresh()
                    if hideInputLine:
                        self.clearLine()
                    else:
                        self.console.write('\n')
                        self.markerHome()
                    self.isWorking = False
                    return input

                if keypress == Keys.UP:
                    self.historyPrev()
                elif keypress == Keys.DOWN:
                    self.historyNext()
                elif keypress == Keys.RIGHT:
                    self.markerRight()
                    self.refresh()
                elif keypress == Keys.LEFT:
                    self.markerLeft()
                    self.refresh()
                elif keypress == Keys.HOME:
                    self.markerHome()
                    self.refresh()
                elif keypress == Keys.END:
                    self.markerEnd()
                    self.refresh()

                elif completer is not None and keypress == Keys.TAB:
                    self.history.rewind()
                    self.complete(completer)

                elif keypress == Keys.BACKSPACE:
                    self.history.rewind()
                    self.erase()

                elif keypress == Keys.DEL:
                    self.delete()

                elif keypress == Keys.ESC:
                    self.history.rewind()
                    self.dropInput()

                elif keypress > 0:
                    self.history.rewind()
                    self.insertChar(Keys.getChar(keypress))
                
                self.console.flush()

    def historyNext(self):
        line = self.history.next()
        if line is not None:
            self.inputBuffer = line
        self.markerEnd()
        self.refresh()

    def historyPrev(self):
        line = self.history.prev()
        if line is not None:
            self.inputBuffer = line
        self.markerEnd()
        self.refresh()


    def printText(self, text):
        self.marker += self.ansiLen(text)
        self.console.write(text)
        
    
    def insertChar(self, char):
        self.inputBuffer = self.inputBuffer[:self.marker] +  char + self.inputBuffer[self.marker:]
        self.marker += 1
        self.markerRight(visualOnly=True)
        self.refresh()

    def erase(self):
        if len(self.inputBuffer) > 0 and self.marker > 0:
            targetMarker = self.marker - 1
            self.markerEnd()
            self.markerLeft()
            self.printText(" ")
            self.markerLeft(abs(self.marker - targetMarker))
            self.inputBuffer = ''.join(list(self.inputBuffer[:self.marker] + self.inputBuffer[self.marker+1:]))
            self.refresh()
    
    def delete(self):
        if self.marker < len(self.inputBuffer):
            self.marker += 1
            self.erase()

    def dropInput(self):
        self.inputBuffer = ""
        self.refresh()

    @staticmethod
    def completesAtEnd(container, contained):
        for c in range(len(container)):
            c = len(container) - 1 - c
            if len(container[c:]) > 0 and contained.upper().startswith(container[c:].upper()):
                return c
        return -1

    @staticmethod
    def containedAtEnd(container, contained):
        for c in range(len(container)):
            c = len(container) - 1 - c
            if len(container[c:]) > 0 and  container[c:].upper() in contained.upper():
                return c
        return -1
    
    def complete(self, completer):
        i = 0
        suggestions = []
        try:
            while True:
                suggestion = completer.complete(self.inputBuffer, i)
                if suggestion is not None:
                    suggestions.append(suggestion)
                else:
                    break
                i += 1
        except ValueError:
            pass
        lastword = "" if len(self.inputBuffer) == 0 or self.inputBuffer.endswith(' ') else self.inputBuffer.split(" ")[-1]
        if len(suggestions) >= 1:
            completed = os.path.commonprefix(suggestions)
            completed = completed if len(completed) > len(lastword) else lastword
            loc = Keys.completesAtEnd(container=self.inputBuffer, contained=completed)
            if loc >= 0:
                self.inputBuffer = self.inputBuffer[:loc] + completed
            elif Keys.containedAtEnd(container=completed, contained=self.inputBuffer.strip()) >= 0:
                pass
            else:
                self.inputBuffer += completed

            if len(suggestions) > 1:
                self.printText("\n{}\n{}".format('  '.join(suggestions), self.prompt + self.inputBuffer))
            self.markerEnd()
            self.refresh()
    
    def refresh(self):
        originalMarker = self.marker
        self.markerHome()
        self.clearLine()
        self.console.write("{}".format(self.prompt))
        self.printText(self.InputLine(originalMarker))
        self.markerHome()
        if originalMarker > 0:
            self.markerRight(originalMarker)

    def clearLine(self):
        self.console.write("\33[2K\33[{}D".format(self.ansiLen(self.prompt + self.inputBuffer)))

    def markerHome(self, visualOnly=False):
        if self.marker > 0:
            self.markerLeft(self.marker, visualOnly=visualOnly)

    def markerEnd(self, visualOnly=False):
        self.markerHome()
        self.markerRight(len(self.inputBuffer), visualOnly=visualOnly)

    def markerRight(self, amount=1, visualOnly=False):
        if visualOnly:
            self.console.write("\033[{}C".format(amount))

            return

        if self.marker < len(self.inputBuffer):
            oldMarker = self.marker
            self.marker = min(len(self.inputBuffer), self.marker + amount)
            amount = abs(self.marker - oldMarker)
            if amount > 0 or True:
                self.console.write("\033[{}C".format(amount))

    def markerLeft(self, amount=1, visualOnly=False):
        if visualOnly:
            self.console.write("\033[{}D".format(amount))

            return

        if self.marker > 0:
            oldMarker = self.marker
            self.marker = self.marker = max(0, self.marker - amount)
            amount = abs(self.marker - oldMarker)
            if amount > 0 or True:
                self.console.write("\033[{}D".format(amount))

    def removeAnsi(self, ansiText):
        ESC = '\x1b'
        integer = Word(nums)
        escapeSeq = Combine(ESC + '[' + Optional(delimitedList(integer,';')) + 
                        oneOf(list(alphas)))

        nonAnsiString = lambda s : Suppress(escapeSeq).transformString(s)
        return nonAnsiString(ansiText)
    
    def ansiLen(self, ansiText):
        return len(self.removeAnsi(ansiText))

    def InputLine(self, marker=None):
        p = marker is not None
        marker = marker if marker is not None else self.marker
        widthLimit = consoleWidth() - self.ansiLen(self.prompt) - 1
        displayedLine = self.inputBuffer
        if len(displayedLine) > widthLimit:
            if marker >= widthLimit:
                displayedLine = displayedLine[marker-widthLimit:marker]
            else:
                displayedLine = displayedLine[:widthLimit]
        return self.LINE_COLOR + displayedLine + colors.reset

    class Printer:
        def __init__(self, handler):
            self.handler = handler
            self.running = True
            self.worker = threading.Thread(target=self.handleConsolePrints, args=[])
            self.ready = False
            self.worker.start()
            self.prints = []

        def stop(self):
            self.running = False
            self.worker.join()

        def handleConsolePrints(self):
            while self.running:
                with Keys.CONSOLE_LOCK:
                    while self.running:
                        sys.stdout.flush() # flush new content to console
                        input = ""
                        while not input.endswith('\n'):
                            lastInput = input
                            input += self.handler.prints.readline()
                            if input == '':
                                break
                            if input == lastInput:
                                if len(input) > 0 and not input.endswith('\n'):
                                    input += '\n'
                                break
                        if len(input) > 0:
                            self.prints.append(input)
                            if self.handler.isWorking:
                                self.handler.clearLine()
                                restoredLine = self.handler.prompt + self.handler.InputLine()
                                self.handler.console.write("{}{}".format(input, restoredLine))
                            else:
                                self.handler.console.write(input)
                        else:
                            break
                        self.handler.console.flush()
        
        def flush(self):
            with Keys.CONSOLE_LOCK:
                while self.running:
                    sys.stdout.flush()
                    input = ""
                    while not input.endswith('\n'):
                        lastInput = input
                        input += self.handler.prints.readline()
                        if input == lastInput:
                            if len(input) > 0:
                                input += '\n'
                            break
                    if len(input) > 0:
                        self.handler.console.write(input)
                        self.handler.console.flush()
                    else:
                        break

    class HistoryManager:
        MAX_SIZE = 1000
        OVERFLOW = 100

        fileLocks = {}

        def __init__(self, file=None):
            self.index = 0
            self.history = []
            self.file = None
            if file:
                if file not in Keys.HistoryManager.fileLocks:
                    Keys.HistoryManager.fileLocks[file] = threading.Lock()
                with Keys.HistoryManager.fileLocks[file]:
                    open(file, 'a').close()
                    with open(file) as f:
                        self.history = [line.strip('\n') for line in f.readlines()]
                self.file = file
            self.rewind()
            self.isBrowsing = False
        
        def close(self):
            if self.file is not None:
                with open(self.file, 'w') as f:
                    f.write('\n'.join(self.history))

        def prev(self):
            if not self.isEmpty() and  self.index >= 0:
                self.index -= 1
                if self._onItem():
                    return self.history[self.index]
            self.isBrowsing = True
        
        def next(self):
            if not self.isEmpty() and self.index < len(self.history):
                self.index += 1
                if self._onItem():
                    return self.history[self.index]
            self.isBrowsing = True

        def append(self, item):
            if len(self.history) == 0 or (not self.isBrowsing and self.history[-1] != item):
                self.history.append(item)
                if self.file is not None:
                    with Keys.HistoryManager.fileLocks[self.file]:
                        with open(self.file, 'a') as f:
                            f.write(item + '\n')
                if len(self.history) > self.MAX_SIZE + self.OVERFLOW:
                    self.history = self.history[self.OVERFLOW:]
            self.rewind()
        
        def rewind(self):
            self.index = len(self.history)
            self.isBrowsing = False

        def isEmpty(self):
            return len(self.history) == 0

        def _onItem(self):
            return self.index >= 0 and self.index < len(self.history)

        

