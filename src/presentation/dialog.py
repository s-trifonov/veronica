import sys
from h2tools.ui_action import UI_Action
#=================================
class DialogPresentation:
    def __init__(self, top_presentation, name):
        self.mTopPre = top_presentation
        self.mName   = name

        self.mUICtrl  = (self.mTopPre.getEnv().getUIApp().
            getUIController(self.mName))
        self.mUICtrl.setActionFunction(self.__action)
        self.mDialogWidget = self.mUICtrl.getTopWidget()
        self.mInAction = False

    def getTopPre(self):
        return self.mTopPre

    def getEnv(self):
        return self.mTopPre.getEnv()

    def getDialogWidget(self):
        return self.mDialogWidget

    def getWidget(self, name):
        return self.mUICtrl.getWidget(name)

    def _execute(self):
        return self.mDialogWidget.exec_()

    def __action(self, command):
        if command.startswith('!'):
            if self.isCheckedIn():
                return
            command = command[1:]
        assert not self.mInAction
        act = UI_Action(command)
        self.checkin()
        self.userAction(act)
        self.checkout()

    def isCheckedIn(self):
        return self.mInAction

    def checkin(self):
        assert not self.mInAction
        self.mInAction = True

    def checkout(self):
        assert self.mInAction
        self.mInAction = False

    def userAction(self, act):
        self.doAction(act)
        if act.isLost():
            print(("Dialog %s" % self.mName)
                + (" lost action %s (%s)" % act.getNames()),
                file = sys.stderr)
        elif act.isFailed():
            print(("Dialog %s" % self.mName)
                + (" failed action %s (%s)" % act.getNames()),
                file = sys.stderr)
