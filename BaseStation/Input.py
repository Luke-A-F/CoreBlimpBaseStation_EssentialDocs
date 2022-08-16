import pygame
from pygame.locals import *
from Text import getTextSurface
import time

class Input:
    def __init__(self, type, name, data):
        self.type = type
        self.name = name
        self.nameSurface = getTextSurface(self.name,30)
        if(type=="Keyboard"):
            self.keys = data #Key constants
        elif(type=="Controller"):
            self.controller = data #Controller object

        self.controllerMapping = {"Xbox 360 Wireless Receiver":  #in use
                                      {"JS_LEFT_X":"A0",
                                       "JS_LEFT_Y":"A1",
                                       "TRIGGER_LEFT":"A2",
                                       "JS_RIGHT_X":"A3",
                                       "JS_RIGHT_Y":"A4",
                                       "TRIGGER_RIGHT":"A5",
                                       "A":"B0",
                                       "B":"B1",
                                       "X":"B2",
                                       "Y":"B3",
                                       "BUMPER_LEFT":"B4",
                                       "BUMPER_RIGHT":"B5",
                                       "BACK":"B6",
                                       "START":"B7",
                                       "HOME":"B8",
                                       "JS_LEFT_BUTTON":"B9",
                                       "JS_RIGHT_BUTTON":"B10",
                                       "DPAD_LEFT":"B11",
                                       "DPAD_RIGHT":"B12",
                                       "DPAD_UP":"B13",
                                       "DPAD_DOWN":"B14"},
                                  "Xbox Series X Controller":
                                      {"JS_LEFT_X":"A0",
                                       "JS_LEFT_Y":"A1",
                                       "TRIGGER_LEFT":"A2",
                                       "JS_RIGHT_X":"A3",
                                       "JS_RIGHT_Y":"A4",
                                       "TRIGGER_RIGHT":"A5",
                                       "A":"B0",
                                       "B":"B1",
                                       "X":"B2",
                                       "Y":"B3",
                                       "BUMPER_LEFT":"B4",
                                       "BUMPER_RIGHT":"B5",
                                       "BACK":"B10",
                                       "START":"B11",
                                       "JS_LEFT_BUTTON":"B13",
                                       "JS_RIGHT_BUTTON":"B14",
                                       "DPAD_LEFT":"H00-",
                                       "DPAD_RIGHT":"H00+",
                                       "DPAD_UP":"H01+",
                                       "DPAD_DOWN":"H01-"}
                                  }

        self.prevPressGrab = 0
        self.currentPressGrab = 0
        self.prevPressAuto = 0
        self.currentPressAuto = 0
        self.currentPressConnect = 0
        self.prevPressShoot = 0
        self.currentPressShoot = 0

        self.pressingPanicAuto = False
        self.pressPanicAutoStartTime = 0
        self.panicTriggerTime = 1

        self.pressingKill = False
        self.pressKillStartTime = 0
        self.killTriggerTime = 3

        self.vibrateUntilTime = 0

    def getNameSurface(self):
        return self.nameSurface

    def getInput(self):
        if(self.type == "Keyboard"):
            return self.getInputKeyboard()
        elif(self.type == "Controller"):
            return self.getInputController()

    def getInputKeyboard(self):
        keys = self.keys #KeyConstants=[right,left,forward,backward,up,down,morePower,grab,auto]
        powerNormal = 0.3
        powerAdd = 0.2
        power = powerNormal + powerAdd * self.getKey(keys[6])

        leftX = self.getKey(keys[0]) - self.getKey(keys[1])
        leftY = self.getKey(keys[2]) - self.getKey(keys[3])
        rightX = self.getKey(keys[3]) - self.getKey(keys[4])
        rightY = self.getKey(keys[4]) - self.getKey(keys[5])

        leftX *= (power+0.3)
        leftY *= (power+0.3)
        rightX *= power
        rightY *= (power+0.5)

        # Enforce deadzones
        leftX = fixInput(leftX)
        rightX = fixInput(rightX)
        leftY = fixInput(leftY)
        rightY = fixInput(rightY)

        #Other Input
        self.currentPressGrab = self.getKey(keys[7])
        self.currentPressAuto = self.getKey(keys[8])

        return (leftX, leftY, rightX, rightY)

    def getInputController(self):
        controller = self.controller
        leftX = self.getControllerInput("JS_LEFT_X")
        leftY = -1 * self.getControllerInput("JS_LEFT_Y")
        #rightX = controller.get_axis(2) 2=left js; 5=right trigger
        rightX = self.getControllerInput("JS_RIGHT_X")
        rightY = -1 * self.getControllerInput("JS_RIGHT_Y")

        # Enforce deadzones
        leftX = fixInput(leftX)
        rightX = fixInput(rightX)
        leftY = fixInput(leftY)
        rightY = fixInput(rightY)

        self.currentPressGrab = 1 if self.getControllerInput("BUMPER_RIGHT") > 0.5 else 0
        self.currentPressAuto = 1 if self.getControllerInput("TRIGGER_RIGHT") > 0.5 else 0
        self.currentPressConnect = 1 if self.getControllerInput("DPAD_DOWN") > 0.5 else 0
        self.currentPressShoot = 1 if self.getControllerInput("BUMPER_LEFT") > 0.5 else 0
        #right/left, forward/backward, 0, up/down
        """
        if(controller.get_name() == "Xbox Series X Controller"):
            keys = self.controllerMapping["Xbox Series X Controller"].keys()
            for key in keys:
                print(key,": ",self.getControllerInput(key),sep="",end="  ")
            print()
        """

        # print("0: ", self.controller.get_button(0))
        # print("1: ", self.controller.get_button(1))
        # print("2: ", self.controller.get_button(2))
        # print("3: ", self.controller.get_button(3))
        # print("4 ", self.controller.get_button(4))
        # print("5 ", self.controller.get_button(5))
        # print("6 ", self.controller.get_button(6))
        # print("7 ", self.controller.get_button(7))
        # print("8 ", self.controller.get_button(8))

        #Panic Auto
        if(self.getControllerInput("Y") == 1):
            if(not self.pressingPanicAuto):
                self.pressingPanicAuto = True
                self.pressPanicAutoStartTime = time.time()
        elif(self.pressingPanicAuto):
            self.pressingPanicAuto = False

        #Kill
        if(self.getControllerInput("X") == 1):
            if not self.pressingKill:
                self.pressingKill = True
                self.pressKillStartTime = time.time()
        elif self.pressingKill:
            self.pressingKill = False


        #Kill program

        #Vibration
        if(self.vibrateUntilTime > time.time()):
            controller.rumble(1, 1, 0)
        else:
            controller.stop_rumble()

        #controller.rumble(10,20,2)

        mode = 1
        if(mode == 1):
            return (leftX, leftY, rightX, rightY)
        elif(mode == 2):
            return (leftX, rightY, rightX, leftY)

    def getKey(self, key):
        return pygame.key.get_pressed()[key]

    def getControllerInput(self,inputName):
        controllerName = self.controller.get_name()
        inputSource = self.controllerMapping[controllerName][inputName]
        if(inputSource[0] == "A"):
            axisNum = int(inputSource[1:])
            return self.controller.get_axis(axisNum)
        elif(inputSource[0] == "B"):
            buttonNum = int(inputSource[1:])
            return self.controller.get_button(buttonNum)
        elif(inputSource[0] == "H"):
            hatNum = int(inputSource[1])
            hatIndex = int(inputSource[2])
            retCondition = inputSource[3]
            inputValue = self.controller.get_hat(hatNum)[hatIndex]
            if(retCondition == "+" and inputValue == 1):
                return 1
            elif(retCondition == "-" and inputValue == -1):
                return 1
        return 0

    def notify(self, timeDuration):
        if(self.type == "Controller"):
            #print("Notify")
            self.vibrateUntilTime = time.time() + timeDuration

    def trigger_panicAuto(self):
        return self.pressingPanicAuto and time.time() - self.pressPanicAutoStartTime > self.panicTriggerTime

    def trigger_kill(self):
        return self.pressingKill and time.time() - self.pressKillStartTime > self.killTriggerTime

    def trigger_connectToBlimp(self):
        return self.currentPressConnect

def fixInput(x, deadZero=0.1, deadOne=0.01, decimals=2):
    if (abs(x) < deadZero): return 0
    if (x > 1 - deadOne): return 1
    if (x < -1 + deadOne): return -1
    return round(x, decimals)
