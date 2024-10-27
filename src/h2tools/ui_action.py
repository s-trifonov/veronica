#import sys
#=========================================
class UI_Action:
    def __init__(self, command, descr = None):
        self.mFullName = command
        self.mOpName = command
        self.mActStatus = None
        self.mMessage = None
        self.mDescr = descr

    def isAction(self, name):
        assert self.mActStatus is None
        if self.mOpName == name:
            self.mActStatus = False
            return True
        return False

    def hasPrefix(self, head):
        return self.mFullName.startswith(head)

    def isGroup(self, head):
        assert self.mActStatus is None
        if self.mOpName.startswith(head):
            self.mOpName = self.mOpName[len(head):]
            return True
        return False

    def isInSet(self, names):
        assert self.mActStatus is None
        if self.mOpName in names:
            self.mActStatus = False
            return True
        return False

    def done(self):
        self.mActStatus = True

    def failed(self, message = None):
        self.mActStatus = False
        self.mMessage = message

    def isFailed(self):
        return self.mActStatus is False

    def isLost(self):
        return self.mActStatus is None

    def getOpName(self):
        return self.mOpName

    def getDescr(self):
        if self.mDescr:
            return self.mDescr
        return self.mFullName

    def getNames(self):
        return (self.mFullName, self.mOpName)

    def getMessage(self):
        return self.mMessage
