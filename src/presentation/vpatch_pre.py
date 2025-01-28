import re
from PyQt5 import QtCore, QtGui,  QtWidgets
from h2tools.keyboard import KeyboardSupport
from h2tools.tools_qt import qt_str, updateStyle
from config.ver_cfg import Config
from config.messenger import msg
from config.gr_support import GraphicsSupport
from .scenario_mouse import MouseEventListener
#=================================
class VPatch_Presentation:
    def __init__(self, top_presentation):
        self.mTopPre = top_presentation

        self.mUICtrl  = (self.mTopPre.getEnv().getUIApp().
            getUIController("vpatch"))
        self.mUICtrl.setActionFunction(self.action)
        self.mSupportWindow = self.mUICtrl.getTopWidget()
        self.mPatchView = self.mUICtrl.getWidget("vpatch-image")
        self.mPatchNotes = self.mUICtrl.getWidget("vpatch-notes")
        self.mPatchParam =  self.mUICtrl.getWidget("vpatch-params")
        self.mPatchDial =  self.mUICtrl.getWidget("vpatch-dial")
        self.mPatchDialLabel =  self.mUICtrl.getWidget("vpatch-dial-label")
        self.mSupportWindow.setListeners(self.listenKey)
        self.mPatchNotes.setReadOnly(True)

        self.mScene = QtWidgets.QGraphicsScene()
        self.mScene.setSceneRect(0, 0,
            Config.PATCH_SIZE, Config.PATCH_SIZE)

        self.mPatchView.setScene(self.mScene)
        self.mPatchView.setRenderHint(QtGui.QPainter.Antialiasing)
        self.mPatchView.setBackgroundBrush(QtCore.Qt.lightGray)
        self.mPatchView.setCacheMode(QtWidgets.QGraphicsView.CacheNone)
        self.mPatchView.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)

        self.mPatchDial.setValue(0)
        self.mImgItem = QtWidgets.QGraphicsPixmapItem()
        self.mImgItem.setPos(0, 0)
        self.mImgItem.setOffset(0, 0)
        self.mImgItem.hide()
        self.mImgItem.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.mScene.addItem(self.mImgItem)

        self.mMarkupGroup = QtWidgets.QGraphicsItemGroup()
        self.mMarkupGroup.hide()
        self.mScene.addItem(self.mMarkupGroup)

        self.mScenario = _PatchViewScenario(self.mMarkupGroup)
        self.mPatchView.setMouseEventListener(self.mScenario);

        self.mRecalcAction = self.mUICtrl.getUIAction("vpatch-recalc")
        self.mCurPatchInfo = None
        self.setPatch(None)

    def raiseOnTop(self, sub_mode = None):
        if not self.mSupportWindow.isActiveWindow():
            self.mSupportWindow.show()
            self.mSupportWindow.activateWindow()
        if self.mSupportWindow.windowState() == QtCore.Qt.WindowMinimized:
            self.mSupportWindow.setWindowState(
                QtCore.Qt.WindowNoState)
        self.mSupportWindow.raise_()
        return None

    def exit(self):
        self.mSupportWindow.hide()

    def getProject(self):
        return self.mTopPre.getProject()

    def getEnv(self):
        return self.mTopPre.getEnv()

    def getWidget(self, name):
        return self.mUICtrl.getWidget(name)

    def getTopPre(self):
        return self.mTopPre

    def update(self):
        self._updateCtrl()
        patch = self.mTopPre.getImagePre().getCurPatch()
        if self.mCurPatchInfo is not patch:
            self.setPatch(patch)
        self.mRecalcAction.setDisabled(
            self.mCurPatchInfo is None or
            (self.mCurPatchInfo.getCropper().getAngle() ==
                self.getCurAngle() and
            self.mCurPatchInfo.getCropper().getParams() ==
                self.mPatchParam.text()))

    def _updateCtrl(self, full_update = False):
        rep = msg("vpatch.dial.value", self.mPatchDial.value())
        self.mPatchDialLabel.setText(qt_str(rep))
        if full_update:
            rep = ""
            if self.mCurPatchInfo is not None:
                rep = self.mCurPatchInfo.getCropper().getParams()
            self.mPatchParam.setText(qt_str(rep))

    def listenKey(self, evt):
        command = KeyboardSupport.processKeyEvent(evt)
        if command is not None:
            evt.accept()
            self.action(*command)

    def isOnDuty(self):
        return self.mSupportWindow.hasFocus()

    def action(self, command, cmd_descr = None):
        self.mTopPre.action(command, cmd_descr)

    def notifyStatus(self, text, is_error = False):
        self.mTopPre.notifyStatus(text, is_error)

    def userAction(self, act):
        if act.isAction("sup-raise"):
            self.raiseOnTop()
            act.done()
            return

        if act.isAction("check"):
            self.mTopPre.needsUpdate()
            act.done()
            return

        if act.isAction("recalc"):
            if self.mCurPatchInfo is not None:
                self._makePatch()
            act.done()
            return

    def setPatch(self, patch_info):
        if patch_info is None:
            self.mCurPatchInfo = None
            self.mPatchNotes.setText(qt_str(msg("vpatch.no.patch")))
            self.mImgItem.hide()
            self.mMarkupGroup.hide()
            self.mPatchNotes.setProperty("sclass", "red")
        else:
            self.mCurPatchInfo = patch_info
            self.mImgItem.setPixmap(self.mCurPatchInfo.getPixmap())
            self.mImgItem.show()
            if GraphicsSupport.readyPatchMarkup(self.mMarkupGroup,
                    self.mCurPatchInfo.getBoundEvents()):
                self.mMarkupGroup.show()
            else:
                self.mMarkupGroup.hide()
            self.mPatchNotes.setText(qt_str(self.mCurPatchInfo.getReport()))
            self.mPatchNotes.setProperty("sclass", "active")
            self.mPatchDial.setValue(self.mCurPatchInfo.getCropper().getAngle())
        updateStyle(self.mPatchNotes)
        self.mPatchParam.setProperty("sclass", "")
        updateStyle(self.mPatchParam)
        self.mScenario.activate(self.mCurPatchInfo is not None)
        self._updateCtrl(True)

    def getCurAngle(self):
        return self.mPatchDial.value()

    sParamReg = re.compile(r'^\((\d+)\,(\d+)\)/(\d+)$')

    def _makePatch(self):
        center, angle = None, None
        param_v = self.mPatchParam.text()
        if param_v != self.mCurPatchInfo.getCropper().getParams():
            param_match = self.sParamReg.match(param_v.replace(' ', ''))
            if param_match is not None:
                center = (int(param_match[1]), int(param_match[2]))
                angle = int(param_match[3])
            else:
                self.mPatchParam.setProperty("sclass", "red")
        if center is None:
            center = self.mCurPatchInfo.getCropper().getCenter()
        if angle is None:
            angle = self.getCurAngle()
        self.mTopPre.getImagePre().makePatch(center, angle)

class _PatchViewScenario(MouseEventListener):
    def __init__(self, markup_group):
        self.mMarkupGroup = markup_group
        self.mActive = False
        self.mHidden = False

    def activate(self, mode):
        self.mActive = mode
        self.mHidden = False

    def hide(self):
        if self.mActive and not self.mHidden:
            self.mHidden = True
            self.mMarkupGroup.hide()

    def show(self):
        if self.mActive and self.mHidden:
            self.mHidden = False
            self.mMarkupGroup.show()

    def mousePressEvent(self, event):
        self.hide()

    def mouseReleaseEvent(self, event):
        self.show()

    def leaveEvent(self, event):
        self.show()
