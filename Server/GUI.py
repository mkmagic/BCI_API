from kivy.config import Config
from kivy.uix.label import Label
from kivy.app import App
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.textinput import TextInput
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.properties import ListProperty
from Controller.Controller import Interface
from kivy.uix.button import Button
from kivy.core.window import Window
from distutils.util import strtobool
from kivy.uix.popup import Popup
from structure.StoppableThread import StoppableThread
import threading
import itertools
import os
import time

MAX_PORT_VAL = 65535



# connect error messages
NO_PORT_ERROR = "can't connect without port"
TOO_BIG_PORT = "You must choose port less then " + str(MAX_PORT_VAL)
ILLEGAL_PORT =  "Illegal port number"
WRONG_PATH_NUM =  "Can send message for one path only"

MAIN_COLOR = "f9f8eb"
TITLE_COLOR = "415865"

SUNKEN_COLOR = "ffe1b6"
SUNKEN_FONT_COLOR = "415865"

BUTTON_COLOR = "7a9eb1"
BUTTON_FONT_COLOR = "f9f8eb"

FONT_COLOR = "415865"

TRUE_COLOR = "008b00"
FALSE_COLOR = "8b1a1a"

DROP_DOWN_BTN_NAME = "nameBtn"

MAX_LOG_SIZE = 100


interface = None
transmissions = {}
tappedPaths = []
tapPrinters = {}
dropdownInitiated = False

def closePrinters():
    for printer in tapPrinters:
        tapPrinters[printer].close()


class tapPrinter:
    def __init__(self, pathName, interfaceObj, screenManager):
        self._interface = interfaceObj
        self._pathName = pathName
        self._readerTread =  threading.Thread(target=self.readAndPrint)
        self._logFile = None
        self._manager = screenManager
        self.isWorking = False
        self.tapActive = False

    def readAndPrint(self):
        self._interface.communicator.appendMessage(self._interface.backdoorProtocol.createMessage("Tap", [self._pathName, "1"]))
        self._logFile = self._interface.getTapLog(self._pathName)
        with open(self._logFile, 'r') as log:
            while(self.isWorking):
                newLine = log.readline()
                if(newLine):
                    newLine = newLine.split("::")[1]
                    self._manager.addMessageToTapScreen(newLine)
    
    def start(self):
        print("start printer of " + self._pathName)
        self.isWorking = True
        self._readerTread.start()
        

    def close(self):
        print("close printer of " + self._pathName)
        self.isWorking = False
        if(self._readerTread.is_alive()):
            self._readerTread.join()

        self._interface.communicator.appendMessage(self._interface.backdoorProtocol.createMessage("Tap", [self._pathName, "0"]))
        if self._logFile is not None and os.path.isfile(self._logFile):
                os.remove(self._logFile)


class Message(Label):
    pass

class ConnectScreen(Screen):
    pass

class MangerScreen(Screen):
    color = ListProperty()
    color = [0, 0, 0, 1.0]

    def changeColor(self):
        self.color = [1, 1, 1, 1.0]
   

class ScreenManagement(ScreenManager):
    color = ListProperty()

    def __init__(self):
        global interface
        interface = Interface(self.setPaths, self.serverDisconnected, self.serverReconnected)
        self._mutex = threading.Semaphore(1)
        ScreenManager.__init__(self)
        self._interface = interface
        self._managerIsInit = False
        self._buttonsNamesToText={}
        self._managerMessages = []

    


    def connectServerAndChangeScreen(self, portNum):
        connScreen = self.get_screen("ConnectScreen")
        hostStr = connScreen.ids['hostInput'].text
        portStr = connScreen.ids['portInput'].text
        portNum = None
        try:
            portNum = int(portStr)
            if(portNum > MAX_PORT_VAL):
                connScreen.ids['connError'].text = TOO_BIG_PORT
                return
        except ValueError:
            connScreen.ids['connError'].text = ILLEGAL_PORT
            return

        self._interface.connect(hostStr, portNum)
        self.current = 'MangerScreen'
        Window.size = (1200, 640)
        self.get_screen("MangerScreen").ids[DROP_DOWN_BTN_NAME].rawText = None
        if not self._interface.isConnected:
            self.serverDisconnected()



    @staticmethod
    def getCircleChar(color):
        return "[color={}][size=24]•[/size][/color]".format(color)

    def setPaths(self):
        global dropdownInitiated
        global transmissions


        dropdownInitiated= True
        menagerScreen = self.get_screen("MangerScreen")

        transmissions = self._interface.knownTransmissions
        mainBtn = menagerScreen.ids[DROP_DOWN_BTN_NAME]
        dropDown = menagerScreen.ids['dropdown']
        maxLength = 0
        dropDown.clear_widgets()
        for path in transmissions:
            color = TRUE_COLOR if transmissions[path].Active else FALSE_COLOR
            btn = Button(id=path, valign="top", text="[b][size=14]{}[/size] {}[/b]".format(path, ScreenManagement.getCircleChar(color)), markup=True, size_hint_y= None, height=mainBtn.height, width=mainBtn.texture_size[0], on_press=self.setStatus)
            btn.rawText = path
            self._buttonsNamesToText[btn.id]=path
            dropDown.add_widget(btn)

            if(mainBtn.id in self._buttonsNamesToText and self._buttonsNamesToText[DROP_DOWN_BTN_NAME] == path):
                mainBtn.text = btn.text
                # self.setStatusOfPath(btn.id)
                if(menagerScreen.ids["tapCheckBox"].active):
                    menagerScreen.ids["tapCheckBox"].active = transmissions[path].Active
                    if(not transmissions[path].Active):
                        self.on_checkbox_active(menagerScreen.ids["tapCheckBox"], False)
                        menagerScreen.ids["tapCheckBox"].disabled = True
                    else:
                        menagerScreen.ids["tapCheckBox"].disabled = False


        if(mainBtn.id in self._buttonsNamesToText):
            choosenPath = self._buttonsNamesToText[DROP_DOWN_BTN_NAME]
            if(choosenPath in transmissions):
                self.setStatusOfPath(choosenPath)



    def setStatus(self, btn):
        global transmissions
        app = App.get_running_app()
        menagerScreen = app.root.get_screen("MangerScreen")

        dropDown = menagerScreen.ids['dropdown'].select(btn.text)

        self._buttonsNamesToText[DROP_DOWN_BTN_NAME]=btn.id
        menagerScreen.ids[DROP_DOWN_BTN_NAME].id = btn.id
  
        txt = btn.text.strip("[b]").strip("[/b]")
        if(btn.id not in tapPrinters):
            tapPrinters[btn.id] = tapPrinter(btn.id, self._interface, self)

        if(transmissions[btn.id].Active):
            menagerScreen.ids["tapCheckBox"].disabled = False

         
      
        menagerScreen.ids["tapCheckBox"].active = tapPrinters[btn.id].tapActive
        menagerScreen.ids["tapCheckBox"].bind(active=self.on_checkbox_active)

        self.setStatusOfPath(btn.id)




    def setStatusOfPath(self, pathName):

        menagerScreen = self.get_screen("MangerScreen")

        true = "[color=#{}]".format(TRUE_COLOR)
        false = "[color=#{}]".format(FALSE_COLOR)
        close = "[/color]"
        status = ""

        transmission = self._interface.knownTransmissions[pathName]

        status = status + "[b]Transmitter:[/b] {}{}{}\n\n[b]Receivers:[/b]\n".format(true if transmission.SenderActive else false, transmission.Sender, close)
        for receiver in transmission.Receivers:
            status = status + "{}{}{}\n".format(true if strtobool(receiver[1]) else false, receiver[0], close)
        
        menagerScreen.ids["statusField"].text = status


    def addMessageToTapScreen(self, message):   

        self._mutex.acquire() 

        self._firstDown = False

        app = App.get_running_app()
        grid = app.root.get_screen("MangerScreen").ids["messagesGrid"]
        gridScroller = app.root.get_screen("MangerScreen").ids["gridScroller"]

        messageRows = message.split('\n')[:-1]
        for msg in messageRows:
            MsgWidget = Message()
            MsgWidget.text = msg
            MsgWidget.id = msg
            self._managerMessages.append(msg)
            grid.add_widget(MsgWidget)
            if(not self._firstDown):
                gridScroller.scroll_to(MsgWidget)
            if(len(self._managerMessages) > MAX_LOG_SIZE):
                grid.remove_widget(grid.children[-1])
                self._managerMessages = self._managerMessages[1:]
                self._firstDown = True
        self._mutex.release() 

    def sendMessage(self):
        message = self.get_screen("MangerScreen").ids["sendMsgInp"].text
        for printer in tapPrinters:
            if(tapPrinters[printer].tapActive):
                activatePath = printer
                self._interface.sendTapMessage(message, activatePath)

        self.get_screen("MangerScreen").ids["sendMsgInp"].text = ""
        return True

    def cleanLogger(self):
        app = App.get_running_app()            
        app.root.get_screen("MangerScreen").ids["messagesGrid"].clear_widgets()
        app.root.get_screen("MangerScreen").l = 0

    def serverDisconnected(self):
        self.disableWidgets(True)
        self.get_screen("MangerScreen").ids['serverDisconectError'].text = "Server is disconnected"

    def serverReconnected(self):
        self.disableWidgets(False)
        self.get_screen("MangerScreen").ids['serverDisconectError'].text = ""


    def disableWidgets(self, disable):

        menagerScreen = self.get_screen("MangerScreen")
        menagerScreen.ids["sendMsgInp"].disabled = disable
        menagerScreen.ids["sendMsgBtn"].disabled = disable
        menagerScreen.ids["tapCheckBox"].disabled = disable
        menagerScreen.ids[DROP_DOWN_BTN_NAME].disabled = disable

        if not disable:
            self.setPaths()


            
            
        



    def on_checkbox_active(self, checkbox, value):
        global transmissions
        menagerScreen = self.get_screen("MangerScreen")
        pathName = self._buttonsNamesToText[DROP_DOWN_BTN_NAME]
        if(value):
            if((pathName in tapPrinters) and tapPrinters[pathName]._readerTread.is_alive()):
                tapPrinters[pathName].close()

            if(transmissions[pathName].Active):
                tapPrinters[pathName] = tapPrinter(pathName, self._interface, self)

                tapPrinters[pathName].tapActive = True
                    
                tapPrinters[pathName].start()
                
        else:
            if(pathName in tapPrinters and tapPrinters[pathName].tapActive == True):
                tapPrinters[pathName].close()
            tapPrinters[pathName].tapActive = False



presentation = Builder.load_file("Gui.kv")

class MainApp(App):
    def build(self):
        Window.size = (640, 240)
        return presentation

MainApp().run()
closePrinters()
if interface is not None:
    interface.close()