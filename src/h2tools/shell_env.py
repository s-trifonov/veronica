import sys

from config.messenger import msg
from tools.utils import raiseRuntimeError, getExceptionValue
from markup.xmlutils import parseXMLFile

#=========================================
class Shell_Environment:
    sProgressDelta = .05

    def __init__(self, name, src_path, use_stdout = True):
        self.mName    = name
        self.mSrcPath = src_path
        self.mStatusBar = None
        self.mProgressStack = []
        self.mProgressReported = None
        self.mEnvStateHandlers = dict()
        self.mHardAlert = False
        self.mIsAlerted = False
        self.mUseStdOut = use_stdout
        self.mCurProcStage = None
        self.mFinalState = "FAILED"

    def _setupPresentation(self, presentation, status_label_id, progress_id):
        self.mPresentation = presentation
        self.mUICtrl.setActionFunction(self.mPresentation.action)
        if status_label_id:
            self.mStatusBar = self.getWidget(status_label_id)
        if progress_id:
            self.mProgressWidget = self.getWidget(progress_id)
            self._drawProgressStatus()
        self.mUIApp.getQTApp().aboutToQuit.connect(presentation.doExit)

    def regHttpAgent(self, name, agent):
        pass

    def postAction(self, command):
        assert False

    def getName(self):
        return self.mName

    def setProgressDelta(self, val):
        self.sProgressDelta = val

    def notifyStatus(self, text):
        print("===NOTE: " + text)

    def startProgress(self, count):
        if len(self.mProgressStack) > 0:
            t_cur, t_delta, t_max = self.mProgressStack[-1]
            dt = t_delta / max(count, 1)
            self.mProgressStack.append(
                [t_cur, dt, min(t_max, t_cur + dt, 1.)])
            self._reportProgressStatus()
        else:
            self.mProgressStack.append([0., 1./max(1, count,), 1.])
            if self.mUseStdOut:
                sys.stdout.write("===PROGRESS: 0%\r")
                sys.stdout.flush()
            self.mProgressReported = 0.

    def stepProgress(self):
        self.mProgressStack[-1][0] += self.mProgressStack[-1][1]
        self._reportProgressStatus()

    def endProgress(self):
        del self.mProgressStack[-1]
        if self.mUseStdOut:
            print("===PROGRESS: done")
        if len(self.mProgressStack):
            self._reportProgressStatus()
        else:
            self.mProgressReported = None

    def _reportProgressStatus(self):
        if len(self.mProgressStack) == 0:
            return
        assert self.mProgressReported is not None
        t_cur, t_delta, t_max = self.mProgressStack[-1]
        if t_cur >= self.mProgressReported + self.sProgressDelta:
            self.mProgressReported = t_cur
            if self.mUseStdOut:
                sys.stdout.write("===PROGRESS: %.01f%s\r" % (t_cur * 100, '%'))
                sys.stdout.flush()

    def doParseXML(self, fname, ftype,
            validator = None, top_tag  = None):
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
        self._report("===ERROR: "
            + msg("xml.parse.problems", msg("xml.type." + ftype)))
        raiseRuntimeError("XML parse")
        return None

    def postAlert(self, message, title = "", level = 0):
        self.alert(message, title, level)

    def flushAlerts(self):
        pass

    sAlertLevels = {0: "no-status", 1: "info", 2: "warning", 3: "error"}

    def alert(self, message, title = "", level = 0):
        if self.mHardAlert:
            level = 3
        self._report(("===ALERT[%s]: " % self.sAlertLevels[level]) + message)
        if level >= 2:
            self.mIsAlerted = True
            raiseRuntimeError("Alert")

    def confirm(self, message, labels,
            title = "", level = 0, idx_enter = 0, idx_escape = -1):
        self._report("===CONFIRMED: " + message + " -> " + labels[idx_enter])
        return idx_enter

    def needsUpdate(self, feature = None):
        pass

    def checkUpdate(self):
        pass

    def registerEnvStateHandler(self, key, handler):
        self.mEnvStateHandlers[key] = handler

    def getEnvState(self, key):
        handler = self.mEnvStateHandlers.get(key)
        if handler:
            return handler.getEnvState()
        self.notifyStatus("No env-state for %s" % key)
        return ""

    def getSrcPath(self, fname, subdir = None, extension = None):
        ret = self.mSrcPath + "/"
        if subdir:
            ret += subdir + "/"
        ret += fname
        if extension:
            ret += "." + extension
        return ret

    #=========================================
    def _report(self, text):
        if self.mUseStdOut:
            print(text, file = sys.stdout)
            sys.stdout.flush()
        else:
            print(text, file = sys.stderr)
            sys.stderr.flush()

    def setHardAlert(self, value = True):
        self.mHardAlert = value

    def isAlerted(self):
        return self.mIsAlerted

    def getFinalState(self):
        return self.mFinalState

    def setFinalState(self, state):
        self.mFinalState = state

    def getCurProcessStage(self):
        return self.mCurProcStage

    def report(self, message, start_process_stage = False):
        if start_process_stage:
            self.mCurProcStage = start_process_stage
            text = "===STAGE:" + message
        else:
            text = message
        self._report(text)

    def handleException(self):
        if not self.mIsAlerted:
            getExceptionValue()
