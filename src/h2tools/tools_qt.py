from PyQt5 import QtCore, QtGui, QtWidgets
from .qt_conv import convAlignment
#===================================
try:
    qt_str = QtCore.QString.fromUtf8
except AttributeError:
    def qt_str(s):
        return s

def updateStyle(widget):
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()

#===================================
class IdleEvent(QtCore.QEvent):
    sEventType = QtCore.QEvent.registerEventType()

    @classmethod
    def isOf(cls, event):
        return event.type() == cls.sEventType

    def __init__(self):
        QtCore.QEvent.__init__(self, self.sEventType)

#===================================
class IdleStep:
    sInUse = False

    @classmethod
    def ping(cls, app, obj):
        if not cls.sInUse:
            cls.sInUse = True
            app.postEvent(obj, IdleEvent(), -2)

    @classmethod
    def pong(cls, event):
        if IdleEvent.isOf(event):
            cls.sInUse = False
            return True
        return False

#===================================
class ActionEvent(QtCore.QEvent):
    sEventType = QtCore.QEvent.registerEventType()

    @classmethod
    def isOf(cls, event):
        return event.type() == cls.sEventType

    def __init__(self, command, presentation = None):
        QtCore.QEvent.__init__(self, self.sEventType)
        self.mCmd = command
        self.mPre = presentation

    def getCmd(self):
        return self.mCmd

    def getPresentation(self, default):
        if self.mPre is None:
            return default
        return self.mPre

#===================================
def loopEvents():
    loop = QtCore.QEventLoop()
    loop.processEvents()

#===================================
def setFormRowHidden(field, value):
    field.setHidden(value)
    field.parent().layout().labelForField(field).setHidden(value)

#===================================
def setFormRowSClass(field, sclass):
    label_ctrl = field.parent().layout().labelForField(field)
    label_ctrl.setProperty("sclass", sclass)
    updateStyle(label_ctrl)

#===================================
def newQItem(text, icon = None, tooltip = None,
        align = None, disabled = False, checkable = False,
        data = None, checked = None):
    if icon is None:
        ret = QtGui.QStandardItem(qt_str(text))
    else:
        ret = QtGui.QStandardItem(icon, qt_str(text))
    if tooltip is not None:
        ret.setToolTip(qt_str(tooltip))
    if data is not None:
        ret.setData(data, QtCore.Qt.UserRole)
    if checkable:
        ret.setCheckable(True)
    if checked is not None:
        ret.setCheckState(QtCore.Qt.Checked
            if checked else QtCore.Qt.Unchecked)
    if disabled:
        ret.setFlags(ret.flags() & (~QtCore.Qt.ItemIsEnabled))
    if align is not None:
        ret.setTextAlignment(convAlignment(align))
    return ret

#===================================
def __showContextMenu(app, widget, press_event):
    app.postEvent(widget, QtGui.QContextMenuEvent(0,
        press_event.pos()))
    press_event.accept()

def setupPressContextMenu(env, widget):
    widget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
    qt_app = env.getUIApp().getQTApp()
    widget._setMousePressFunc(
        lambda event: __showContextMenu(qt_app, widget, event))

def addContextMenuAction(widget, label_text, func, param, icon = None):
    if icon is not None:
        action = QtWidgets.QAction(icon, qt_str(label_text), widget)
    else:
        action = QtWidgets.QAction(qt_str(label_text), widget)
    action.triggered.connect(lambda: func(param))
    widget.addAction(action)
    return action

#===================================
