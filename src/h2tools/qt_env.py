import sys

from PyQt5 import QtCore, QtWidgets
from config.messenger import msg
from .runtime import RuntimeEnvironment, RT_Guard
from .tools_qt import IdleStep, ActionEvent, loopEvents, qt_str
from .utils import runSpawnCmd
from .prefs import PreferenceHandler
from .xmlutils import parseXMLFile

#=========================================
class QT_Environment(QtCore.QObject):
    def __init__(self, ui_application, name, prefs_fname,
            in_http_app = None, prefs_no_save = False, prefs_default = None):
        QtCore.QObject.__init__(self, None)
        self.mName    = name
        self.mUIApp   = ui_application
        self.mInHttpApp = in_http_app
        if self.mInHttpApp is not None:
            self.mInHttpApp.activate(self)
        self.mUICtrl  = self.mUIApp.getUIController(self.mName)
        self.mUICtrl.setActionFunction(self.action)
        self.mPresentation = None
        RuntimeEnvironment.setup(self.postIdle,
            loopEvents, self.setRuntimeActive,
            self.checkUpdate)
        self.mStatusBar = None
        self.mProgressWidget = None
        self.mProgressRuntime = False
        self.mProgressStack = []
        self.mEnvStateHandlers = dict()
        self.mPostAlerts = []
        self.mPreferences = PreferenceHandler(self,
            prefs_fname, prefs_default, prefs_no_save)

    def _setupPresentation(self, presentation, status_label_id, progress_id):
        self.mPresentation = presentation
        self.mPmInHttpAppresentation = presentation
        self.mUICtrl.setActionFunction(self.mPresentation.action)
        if status_label_id:
            self.mStatusBar = self.getWidget(status_label_id)
        if progress_id:
            self.mProgressWidget = self.getWidget(progress_id)
            self._drawProgressStatus()
        self.mUIApp.getQTApp().aboutToQuit.connect(presentation.doExit)

    def regHttpAgent(self, name, agent):
        if self.mInHttpApp is not None:
            self.mInHttpApp.regAgent(name, agent)

    def getHttpUrl(self):
        return self.mInHttpApp.getBaseUrl()

    def regRqHandler(self, request, rq_h):
        self.mInHttpApp.regRqHandler(request, rq_h)

    def postIdle(self):
        IdleStep.ping(self.mUIApp.getQTApp(), self)

    def event(self, event):
        if ActionEvent.isOf(event):
            presentation = event.getPresentation(self.mPresentation)
            if presentation is not None:
                presentation.action(event.getCmd())
            else:
                self.action(event.getCmd())
            RuntimeEnvironment.dropIdleCount()
            return True
        if self.mInHttpApp:
            self.mInHttpApp.pushEvents()
        if IdleStep.pong(event):
            RuntimeEnvironment.idleEvent()
            return True
        print("Env: Lost event", event, file = sys.stderr)
        return False

    def postAction(self, command, presentation = None):
        self.mUIApp.getQTApp().postEvent(
            self, ActionEvent(command, presentation), 0)

    def getName(self):
        return self.mName

    def getUIApp(self):
        return self.mUIApp

    def getUICtrl(self):
        return self.mUICtrl

    def getPresentation(self):
        return self.mPresentation

    def getWidget(self, name):
        return self.mUICtrl.getWidget(name)

    def getUIAction(self, name):
        return self.mUICtrl.getUIAction(name)

    def getURL_ImageDir(self):
        return self.mUIApp.getURL_ImageDir()

    def disableAction(self, command, value = True):
        self.mUICtrl.disableAction(command, value)

    def actionIsDisabled(self, command):
        return self.mUICtrl.actionIsDisabled(command)

    def hideAction(self, command, value = True):
        self.mUICtrl.hideAction(command, value)

    def getSrcPath(self, fname, subdir = None, extension = None):
        return self.mUIApp.getSrcPath(fname, subdir = subdir,
            extension = extension)

    def start(self):
        RuntimeEnvironment.startSession(True)
        with RT_Guard():
            self.mUICtrl.show()
            if self.mPresentation:
                self.mPresentation.update()
            else:
                RuntimeEnvironment.doWaitEvents()
            self._drawProgressStatus()

    def action(self, command):
        print("Lost action:", command, file = sys.stderr)

    def notifyStatus(self, text, hint_mode = False):
        if self.mStatusBar is not None:
            if text is None:
                text, hint_mode = "", False
            self.mStatusBar.setText(qt_str(text))
            self.mStatusBar.setProperty("sclass", "hint" if hint_mode else "")

    def setRuntimeActive(self, value):
        if self.mProgressRuntime != value:
            self.mProgressRuntime = value
            self._drawProgressStatus()

    def startProgress(self, count):
        if len(self.mProgressStack) > 0:
            t_cur, t_delta, t_max = self.mProgressStack[-1]
            dt = t_delta / max(count, 1)
            self.mProgressStack.append(
                [t_cur, dt, min(t_max, t_cur + dt, 1.)])
        else:
            self.mProgressStack.append([0., 1./max(1, count,), 1.])
        self._drawProgressStatus()

    def stepProgress(self):
        self.mProgressStack[-1][0] += self.mProgressStack[-1][1]
        self._drawProgressStatus()

    def endProgress(self):
        del self.mProgressStack[-1]
        self._drawProgressStatus()

    def _drawProgressStatus(self):
        if self.mProgressWidget is None:
            return
        if len(self.mProgressStack) > 0:
            t_cur, t_delta, t_max = self.mProgressStack[-1]
            self.mProgressWidget.setProgressState(
                min(int(min(t_cur, t_max, 1.) * 100), 100))
        elif self.mProgressRuntime:
            self.mProgressWidget.setUndetermined()
        else:
            self.mProgressWidget.setInactive()

    def doParseXML(self, fname, ftype,
            validator = None, top_tag  = None):
        while True:
            doc, errors = parseXMLFile(fname, True)
            if not errors and validator is not None:
                top_nodes = doc.xpath("/*")
                if len(top_nodes) != 1 or top_nodes[0].tag != top_tag:
                    errors = [msg("xml.invalid.top", top_tag)]
                else:
                    val_error = validator.validate(top_nodes[0])
                    if val_error is not None:
                        line_no, err_msg = val_error
                        errors = [
                            msg("xml.at.line", line_no) + err_msg]
            if not errors:
                return doc

            if self.confirm("\n".join([fname + ":"] + errors),
                    (msg("confirm.retry"), msg("confirm.ignore")),
                    msg("xml.parse.problems", msg("xml.type." + ftype))) != 0:
                return None
        return None

    def postAlert(self, message, title = "", level = 0):
        self.mPostAlerts.append((message, title, level))

    def flushAlerts(self):
        while len(self.mPostAlerts):
            self.alert(*self.mPostAlerts.pop())

    #level: 0 - no status, 1 - information, 2 - warning, 3 - error
    def alert(self, message, title = "", level = 0):
        msg_box = QtWidgets.QMessageBox(level, title, message)
        msg_box.exec_()

    def confirm(self, message, labels,
            title = "", level = 0, idx_enter = 0, idx_escape = -1):
        msg_box = QtWidgets.QMessageBox(level, title, message)
        buttons = []
        for label in labels:
            buttons.append(msg_box.addButton(
                qt_str(label), QtWidgets.QMessageBox.ApplyRole))
        msg_box.setDefaultButton(buttons[idx_enter])
        msg_box.setEscapeButton(buttons[idx_escape])
        return msg_box.exec_()

    def needsUpdate(self, feature = None):
        if self.mPresentation is not None:
            self.mPresentation.needsUpdate(feature)

    def checkUpdate(self):
        if self.mPresentation:
            self.mPresentation.checkUpdate()

    def registerIdleHandler(self, idle_handler):
        RuntimeEnvironment.registerIdleHandler(idle_handler)

    def registerEnvStateHandler(self, key, handler):
        self.mEnvStateHandlers[key] = handler

    def raiseMainOnTop(self):
        main_window = self.mUICtrl.getTopWidget()
        main_window.activateWindow()
        if main_window.windowState() == QtCore.Qt.WindowMinimized:
            main_window.setWindowState(QtCore.Qt.WindowNoState)
        main_window.raise_()

    def getEnvState(self, key):
        handler = self.mEnvStateHandlers.get(key)
        if handler:
            return handler.getEnvState()
        print("No env-state for", key, file = sys.stderr)
        return ""

    def quit(self):
        if self.mInHttpApp is not None:
            self.mInHttpApp.stop()
        RuntimeEnvironment.goQuit()
        self.mUICtrl.getTopWidget().close()
        self.mUIApp.getQTApp().quit()

    def getPreference(self, name):
        return self.mPreferences.getProperty(name)

    def getPreferenceHandler(self):
        return self.mPreferences

    def runExtEdit(self, file_name):
        the_cmd = self.mPreferences.getProperty("ext-edit")
        if the_cmd.find("%s") >= 0:
            the_cmd = the_cmd % file_name
        else:
            the_cmd += " " + file_name
        runSpawnCmd(the_cmd)
