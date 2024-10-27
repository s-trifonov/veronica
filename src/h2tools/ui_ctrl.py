#import sys
from collections import defaultdict
from PyQt5 import QtCore

from .ui_xult import UI_XultActivator

#=========================================
class QT_UIController(QtCore.QObject):
    def __init__(self, ui_application, name):
        QtCore.QObject.__init__(self)
        self.mUIapp       = ui_application
        self.mName        = name
        self.mWidgets     = dict()
        self.mCtrlCounter = 0
        self.mSMapper = QtCore.QSignalMapper(self)
        self.mSMapper.mapped[str].connect(self.action)
        self.mActionsCtrls = defaultdict(list)
        self.mActionF   = None
        self.mTopWidget = UI_XultActivator(self).getTop()

    def setActionFunction(self, action_f):
        self.mActionF = action_f

    def getTopWidget(self):
        return self.mTopWidget

    def getName(self):
        return self.mName

    def getWidget(self, name):
        return self.mWidgets[name]

    def getUIAction(self, name):
        return self.mActionsCtrls[name][0]

    def show(self):
        self.mTopWidget.show()

    def exec_(self):
        return self.mTopWidget.exec_()

    def getSrcPath(self, fname, subdir = None, extension = None):
        return self.mUIapp.getSrcPath(fname, subdir = subdir,
            extension = extension)

    def getURL_ImageDir(self):
        return self.mUIapp.getURL_ImageDir()

    def getURL_BaseDir(self):
        return self.mUIapp.getURL_BaseDir()

    def _getTechWidgetId(self, kind):
        ret = "-%s-%s-%d" % (self.mName, kind, self.mCtrlCounter)
        self.mCtrlCounter += 1
        return ret

    def _regPersistentProperties(self, ctrl, persist):
        pp_handler = self.mUIapp.getPPHandler()
        if pp_handler is not None:
            pp_handler.register(ctrl, persist)

    def _mapAction(self, ctrl, command, kind):
        self.mSMapper.setMapping(ctrl, command)
        if kind == "triggered":
            ctrl.triggered.connect(self.mSMapper.map)
        elif kind == "pressed":
            ctrl.pressed.connect(self.mSMapper.map)
        elif kind == "toggled":
            ctrl.toggled.connect(self.mSMapper.map)
        elif kind == "activated":
            ctrl.activated.connect(self.mSMapper.map)
        elif kind == "textChanged":
            ctrl.textChanged.connect(self.mSMapper.map)
        elif kind == "stateChanged":
            ctrl.stateChanged.connect(self.mSMapper.map)
        elif kind == "valueChanged":
            ctrl.valueChanged.connect(self.mSMapper.map)
        elif kind == "currentChanged":
            ctrl.currentChanged.connect(self.mSMapper.map)
        elif kind == "textChanged":
            ctrl.textChanged.connect(self.mSMapper.map)
        elif kind == "editTextChanged":
            ctrl.editTextChanged.connect(self.mSMapper.map)
        elif kind == "textEdited":
            ctrl.textEdited.connect(self.mSMapper.map)
        elif kind == "returnPressed":
            ctrl.returnPressed.connect(self.mSMapper.map)
        elif kind == "editingFinished":
            ctrl.editingFinished.connect(self.mSMapper.map)
        elif kind == "currentItemChanged":
            ctrl.currentItemChanged.connect(self.mSMapper.map)
        elif kind == "currentTextChanged":
            ctrl.currentTextChanged.connect(self.mSMapper.map)
        elif kind == "itemActivated":
            ctrl.itemActivated.connect(self.mSMapper.map)
        else:
            assert False
        if command.startswith('!'):
            command = command[1:]
        self.mActionsCtrls[command].append(ctrl)

    def action(self, command):
        if self.mActionF:
            self.mActionF(command)

    def disableAction(self, command, value = True):
        for ctrl in self.mActionsCtrls.get(command):
            ctrl.setDisabled(value)

    def hideAction(self, command, value = True):
        for ctrl in self.mActionsCtrls.get(command):
            ctrl.setHidden(value)

    def actionIsDisabled(self, command):
        for ctrl in self.mActionsCtrls.get(command):
            return not ctrl.isEnabled()
        return True

    def getIcon(self, fname):
        return self.mUIapp.getIcon(fname)

    def getPixmap(self, fname):
        return self.mUIapp.getPixmap(fname)

    def checkPersistentProperties(self, env):
        pp_handler = self.mUIapp.getPPHandler()
        if pp_handler is not None:
            pp_handler.keepState(env)
