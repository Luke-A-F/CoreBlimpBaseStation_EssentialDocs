from Text import getTextSurface

class Blimp:
    def __init__(self,ID):
        self.ID = ID
        self.auto = 0
        self.grabbing = 0
        self.shooting = 0
        self.connnected = False

        self.receivedAuto = "Null"
        self.receivedStatus = "Null"

        self.receivedAuto_Surface = getTextSurface(self.receivedAuto,25)
        self.receievedStatus_Surface = getTextSurface(self.receivedStatus,25)

        self.surfaces = {}

        self.name = "Blimp " + str(ID)
        self.nameSurface = getTextSurface(self.name, int(40 - len(self.name)))
        self.lastHeartbeatDetected = 0
        self.lastHeartbeatDiff = 0
        self.heartbeatDisconnectDelay = 5 #seconds
        self.lastTimeInputDataSent = 0
        self.timeInputDelay = 0.05 #seconds

        self.data = []

    def getNameSurface(self):
        return self.nameSurface

    def toggleIMU(self):
        self.IMUEnabled = 1 - self.IMUEnabled