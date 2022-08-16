from Input import Input
from Blimp import Blimp
from Connection import Connection
import pygame
from pygame.locals import *
#from SerialHelper import SerialHelper
from UDPMulticast import UDPHelper
import time
import easygui


class BlimpHandler:
    # Init =================================================================================
    def __init__(self):
        self.comms = UDPHelper() #SerialHelper() #UDPHelper()
        self.display = None
        self.comms.open()
        self.parameterMessages = []
        self.pCodes = {  #Parameter message codes
            "toggleABG": "e",    #toggle Active Ball Grabber
            "autoOn":    "A1",   #turn autonomous on
            "autoOff":   "A0"    #turn autonomous off
        }

        self.blimps = []
        """
        tempBlimp = Blimp(50)
        tempBlimp.lastHeartbeatDetected = 99999999999999
        self.blimps.append(tempBlimp)
        tempBlimp2 = Blimp(51)
        tempBlimp2.lastHeartbeatDetected = 99999999999999
        self.blimps.append(tempBlimp2)
        """

        self.lastBlimpAdded = 0
        self.blimpAddDelay = 5 #seconds

        self.initInputs()

        self.connections = []

    def close(self):
        print("Closing BlimpHandler")
        self.comms.close()
        print("Comms closed.")

    def initInputs(self):
        self.inputs = []

        #Init WASD Input
        input_WASD = Input("Keyboard", "WASD", (K_d, K_a, K_w, K_s, K_UP, K_DOWN, K_SPACE, K_e, K_q))
        self.inputs.append(input_WASD)
        """
        #Init IJKL Input
        input_IJKL = Input("Keyboard", "IJKL", (K_l, K_j, K_i, K_k, K_LEFTBRACKET, K_QUOTE, K_RETURN))
        self.inputs.append(input_IJKL)
        """

        #Check for joysticks
        self.joystickInstanceIDs = []
        self.joystickCount = pygame.joystick.get_count()
        for i in range(0,self.joystickCount):
            controller = pygame.joystick.Joystick(i)
            controller.init()
            self.printControllerData(controller)
            self.joystickInstanceIDs.append(controller.get_instance_id())
            controllerName = "Contrl " + str(controller.get_instance_id())
            input_Controller = Input("Controller",controllerName,controller)
            self.inputs.append(input_Controller)
        self.tempActiveController = len(self.inputs)-1
        if(self.display != None): self.display.activeController = self.tempActiveController

    def setDisplay(self,display):
        self.display = display
        display.activeController = self.tempActiveController

    #Loop ==================================================================================
    def update(self):
        self.checkJoystickCount()
        self.checkForDeadBlimps()
        self.listen()
        self.sendDataToBlimps()

    def checkJoystickCount(self):
        if (pygame.joystick.get_count() != self.joystickCount):
            print("Updating joysticks")
            self.initInputs()
            self.fixConnections()

    def checkForDeadBlimps(self):
        blimpsCorrect = False
        while not blimpsCorrect:
            blimpsCorrect = True
            for i in range(0, len(self.blimps)):
                blimp = self.blimps[i]
                blimp.lastHeartbeatDiff = time.time() - blimp.lastHeartbeatDetected
                #print(amount,";  ",blimp.heartbeatDisconnectDelay)
                if (blimp.lastHeartbeatDiff > blimp.heartbeatDisconnectDelay):
                    # Blimp heartbeat not received for too long; Remove it
                    print(blimp.name, "heartbeat not received; Removing...")
                    self.blimps.pop(i)
                    blimpsCorrect = False
                    self.fixConnections()
                    break

    def listen(self):
        readStrings = self.comms.getInputMessages()
        #readStrings = []
        while(len(readStrings)>0):
            string = readStrings[0]
            readStrings.pop(0)
            self.checkForNewBlimps(string)
            self.useMessage(string) #includes heartbeat

    def sendDataToBlimps(self):
        currentTime = time.time()
        if(len(self.parameterMessages) > 0):
            #print("Messages:",len(self.parameterMessages))
            while(len(self.parameterMessages)>0):
                message = self.parameterMessages[0]
                self.parameterMessages.pop(0)

                blimpID = message[0]
                data = message[1]
                self.comms.send(blimpID,"P",data)
                #print(blimpID,",0:P:",data,sep='')

        for inputIndex in range(0,len(self.inputs)):
            input = self.inputs[inputIndex]
            if(input.trigger_panicAuto()):
                input.notify(1)
                print("Auto panic!!!")
                for blimp in self.blimps:
                    blimp.auto = 1
            if(input.trigger_connectToBlimp()):
                if(len(self.blimps)==1 and len(self.connections) == 0):
                    self.updateConnection(inputIndex,0)
            connectedBlimpIDs = []
            for connection in self.connections:
                if(connection.inputIndex == inputIndex):
                    connectedBlimpIDs.append(self.blimps[connection.blimpIndex].ID)
            if(len(connectedBlimpIDs) > 0):
                inputData = input.getInput()

                numData = len(inputData)
                message = str(numData+2) + "="
                for i in range(0,numData):
                    message += str(inputData[i]) + ","

                updateGrab = False
                updateAuto = False
                updateShoot = False

                if(input.prevPressGrab != input.currentPressGrab):
                    #update required
                    input.prevPressGrab = input.currentPressGrab
                    if(input.currentPressGrab == 1):
                        updateGrab = True
                if (input.prevPressShoot != input.currentPressShoot):
                    # update required
                    input.prevPressShoot = input.currentPressShoot
                    if (input.currentPressShoot == 1):
                        updateShoot = True
                if(input.prevPressAuto != input.currentPressAuto):
                    input.prevPressAuto = input.currentPressAuto
                    if(input.currentPressAuto == 1):
                        updateAuto = True

                for blimpID in connectedBlimpIDs:
                    blimp = self.findBlimp(blimpID)
                    message += str(blimp.grabbing) + "," + str(blimp.shooting) + ","
                    if(currentTime - blimp.lastTimeInputDataSent > blimp.timeInputDelay):
                        blimp.lastTimeInputDataSent = currentTime
                        if(blimp.auto == 0):
                            self.comms.send(blimpID,"M",message)
                        else:
                            self.comms.send(blimpID,"A","")

                    if(input.trigger_kill()):
                        input.notify(3)
                        print("Killing blimp",blimpID)
                        self.comms.send(blimpID,"K","")

                    if(updateGrab):
                        self.parameterMessages.append((blimpID, self.pCodes["toggleABG"]))
                        print("toggled grabber")
                        if(blimp.grabbing == 0):
                            blimp.grabbing = 1
                        else:
                            blimp.grabbing = 0
                    if (updateShoot):
                        self.parameterMessages.append((blimpID, self.pCodes["toggleABG"]))
                        print("toggled shooter")
                        if (blimp.shooting == 0):
                            blimp.shooting = 1
                        else:
                            blimp.shooting = 0
                    if(updateAuto):
                        #print("Toggled auto")
                        if (blimp.auto == 0):
                            self.parameterMessages.append((blimpID, self.pCodes["autoOn"]))
                            blimp.auto = 1
                        else:
                            self.parameterMessages.append((blimpID, self.pCodes["autoOff"]))
                            blimp.auto = 0
                        input.notify(0.5)

        #Find non-connected blimps
        for blimp in self.blimps:
            blimp.connnected = False
        for connection in self.connections:
            blimpID = self.blimps[connection.blimpIndex].ID
            blimp = self.findBlimp(blimpID)
            blimp.connnected = True
        for blimp in self.blimps:
            if not blimp.connnected:
                if (currentTime - blimp.lastTimeInputDataSent > blimp.timeInputDelay):
                    blimp.lastTimeInputDataSent = currentTime
                    if blimp.auto:
                        self.comms.send(blimp.ID, "A", "")
                    else:
                        message = "6=0,0,0,0," + str(blimp.grabbing) + "," + str(blimp.shooting) + ","
                        self.comms.send(blimp.ID, "M", message)

    def requestRecording(self, blimpIDs):
        if (type(blimpIDs) != list):
            blimpIDs = (blimpIDs)
        for blimpID in blimpIDs:
            self.comms.send(blimpID, "P", "C300")

    #Helper functions ======================================================================
    def fixConnections(self):
        correctConnections = False
        while not correctConnections:
            correctConnections = True  # Assume true until proven incorrect
            for i in range(0, len(self.connections)):
                connection = self.connections[i]
                inputExist = self.inputExists(connection.inputName)
                blimpExist = self.blimpNameExists(connection.blimpName)
                if inputExist[0] and blimpExist[0]:
                    # Input and blimp exists; Update index
                    connection.inputIndex = inputExist[1]
                    connection.blimpIndex = blimpExist[1]
                else:
                    # Input or blimp doesn't exist; Remove it
                    self.connections.pop(i)
                    correctConnections = False
                    break

    def inputExists(self,inputName):
        for i in range(0,len(self.inputs)):
            if(inputName == self.inputs[i].name):
                return (True,i)
        return (False,0)

    def blimpNameExists(self,blimpName):
        for i in range(0,len(self.blimps)):
            if(blimpName == self.blimps[i].name):
                return (True,i)
        return (False,0)

    def blimpIDExists(self,blimpID):
        for blimp in self.blimps:
            if(blimpID == blimp.ID):
                return True
        return False

    def checkForNewBlimps(self, message):
        if (message == "0,N:N:N"):  # New Blimp
            currentTime = time.time()
            if(currentTime - self.lastBlimpAdded > self.blimpAddDelay):
                self.lastBlimpAdded = currentTime
                #Add new blimp!

                #Look for new ID ranging from 1 to len(blimps)+1
                newID = -1
                for checkID in range(1,len(self.blimps)+2):
                    print("Checking ID",checkID)
                    if not self.blimpIDExists(checkID):
                        #blimpID doesn't exist yet
                        newID = checkID
                        print("New Blimp",newID)
                        break

                if(newID != -1):
                    self.comms.send("N","N",str(newID))
                    newBlimp = Blimp(newID)
                    newBlimp.lastHeartbeatDetected = time.time()
                    self.blimps.append(newBlimp)
        else:
            comma = message.find(",")
            colon = message.find(":")
            if(comma == -1 or colon == -1): return
            checkID = message[comma+1:colon]
            if(self.isInt(checkID)):
                checkID = int(checkID)
                if not self.blimpIDExists(checkID):
                    newBlimp = Blimp(checkID)
                    newBlimp.lastHeartbeatDetected = time.time()
                    self.blimps.append(newBlimp)
                    print("Adding new blimp:",checkID)

    def useMessage(self, message):
        comma = message.find(",")
        colon = message.find(":")
        ID = message[comma+1:colon]
        if(self.isInt(ID)):
            ID = int(ID)
            blimp = self.findBlimp(ID)
            blimp.lastHeartbeatDetected = time.time()

            secondColon = message.find(":", colon+1)
            flag = message[colon+1:secondColon]
            if(flag == "P"):
                equal = message.find("=", secondColon+1)
                numFeedbackData = int(message[secondColon+1:equal])
                currentDataLength = len(blimp.data)
                for i in range(currentDataLength, numFeedbackData):
                    blimp.data.append(0.0)
                lastComma = equal
                for i in range(0,numFeedbackData):
                    nextComma = message.find(",",lastComma+1)
                    blimp.data[i] = float(message[lastComma+1:nextComma])
                    lastComma = nextComma
            #if(len(blimp.data)>1):
                #print(blimp.data[0])

            for blimp in self.blimps:
                if(blimp.ID == ID):
                    blimp.lastHeartbeatDetected = time.time()

    def updateConnection(self, inputIndex, blimpIndex):
        if(inputIndex >= len(self.inputs)): return
        if(blimpIndex >= len(self.blimps)): return
        inputName = self.inputs[inputIndex].name
        blimpName = self.blimps[blimpIndex].name
        newConnection = Connection(inputName,blimpName,inputIndex,blimpIndex)
        for i in range(0,len(self.connections)):
            connection = self.connections[i]
            if(newConnection.names==connection.names): #Connection exists; Remove it
                self.connections.pop(i)
                return
            elif(newConnection.blimpName==connection.blimpName): #Blimp already connected; Overwrite it
                self.connections.pop(i)
                self.connections.append(newConnection)
                return
        self.connections.append(newConnection)

    def pushMPB(self, blimpIDs):
        if(type(blimpIDs)!=list):
            blimpIDs = (blimpIDs)
        #Update parameter
        data = easygui.enterbox(msg="Enter parameter data",title="Parameter Update")
        if(data == None): return
        if(data[0] == "E"):
            if(data[1:]=="1"):
                self.display.exclusiveConnections = True
                print("Exclusive connections: TRUE")
            else:
                self.display.exclusiveConnections = False
                print("Exclusive connections: FALSE")
            return
        for blimpID in blimpIDs:
            self.parameterMessages.append((blimpID,data))
            blimp = self.findBlimp(blimpID)
            if(data == self.pCodes["autoOn"]):
                blimp.auto = 1
            elif(data == self.pCodes["autoOff"]):
                blimp.auto = 0

        def toggleAuto(self, blimpIDs):
            if(type(blimpIDs)!=list):
                blimpIDs = (blimpIDs)
            for blimpID in blimpIDs:
                blimp = self.findBlimp(blimpID)
                if(blimp.auto == 0):
                    self.parameterMessages.append((blimpID,self.pCodes["autoOn"]))
                    blimp.auto = 1
                else:
                    self.parameterMessages.append((blimpID,self.pCodes["autoOff"]))
                    blimp.auto = 0

    def updateGrabber(self, blimpIDs):
        if (type(blimpIDs) != list):
            blimpIDs = (blimpIDs)
        for blimpID in blimpIDs:
            self.parameterMessages.append((blimpID,self.pCodes["toggleABG"]))

    def findBlimp(self, blimpID):
        for blimp in self.blimps:
            if(blimp.ID == blimpID):
                return blimp

    def printControllerData(self, controller):
        print("Input")
        print("Name:", controller.get_name())
        print("Axes:", controller.get_numaxes())
        print("Trackballs:", controller.get_numballs())
        print("Buttons:", controller.get_numbuttons())
        print("Hats:", controller.get_numhats())

    def isInt(self, inputString):
        try:
            int(inputString)
            return True
        except ValueError:
            return False