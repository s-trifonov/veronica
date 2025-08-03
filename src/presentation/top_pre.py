import sys

from PyQt5 import QtWidgets
from config.ver_cfg import Config
from config.messenger import msg
from h2tools.runtime import RT_Guard
from h2tools.tools_qt import qt_str
from h2tools.ui_action import UI_Action
from h2tools.keyboard import KeyboardSupport
from h2tools.img_pool import ImagePool
from .dir_pre import DirImagesPresentation
from .img_entry_pre import ImageEntryPresentation
from .image_pre import ImagePresentation
from .vpatch_pre import VPatch_Presentation
from presentation.preferences import Preferences_Dialog
#============================
class TopPresentation:
    def __init__(self, env, project):
        self.mEnv = env
        self.mProject = project
        self.mTopWidget = self.mEnv.getWidget("Top")

        self.mButton_Changing = self.mEnv.getWidget("mode-changing")
        self.mImgPool = ImagePool(Config.IMG_CACHE_SIZE)

        self.mCombo_Zoom    = self.getEnv().getWidget("img-zoom")
        self.mCombo_Opacity = self.getEnv().getWidget("img-opacity")

        self.mNeedsUpdate = True
        self.mFeaturesToUpdate = set()

        self.mDialog_Preferences = Preferences_Dialog(self)

        self.mDirPre = DirImagesPresentation(self)
        self.mImagePre = ImagePresentation(self)
        self.mImgEntryPre = ImageEntryPresentation(self)

        self.mEnv._setupPresentation(self, "menu-status", "menu-progress")
        self.mExitReady = False

        self.mEnv.getUICtrl().getTopWidget().setListeners(
            self.listenKey, self.doExit)

        self.mCurImage = None

        self.mVPatchPre = VPatch_Presentation(self)
        self.mEnv.getUIAction("vpatch-sup-raise").setDisabled(
            not self.mProject.hasAdvancedMode())

    def start(self):
        self.mEnv.start()

    def getProject(self):
        return self.mProject

    def getEnv(self):
        return self.mEnv

    def getDirPre(self):
        return self.mDirPre

    def getImgEntryPre(self):
        return self.mImgEntryPre

    def getImagePre(self):
        return self.mImagePre

    def getVPatchPre(self):
        return self.mVPatchPre

    def listenKey(self, evt):
        command = KeyboardSupport.processKeyEvent(evt)
        if command is not None:
            evt.accept()
            self.action(*command)

    def action(self, command, cmd_descr = None):
        if command == "cmd-test-errors":
            self.doTest()
            return
        if command.startswith('!'):
            if not RT_Guard.isFree():
                return
            command = command[1:]
        # self.mEnv.notifyStatus("")
        act = UI_Action(command, cmd_descr)
        with RT_Guard():
            self.userAction(act)
        message = None
        if act.isFailed():
            message = act.getMessage()
            if message is None:
                message = msg("action.failed", act.getDescr())
        elif act.isLost():
            print("Lost Action: %s (%s)" % act.getNames(), file = sys.stderr)
            message = msg("action.lost", act.getDescr())
        if message:
            self.mEnv.notifyStatus(message)
        if self.mExitReady:
            self.mEnv.quit()

    def userAction(self, act):
        for key, ctrl in (("dir-", self.mDirPre), ("img-entry-", self.mImgEntryPre),
                ("img-", self.mImagePre), ("vpatch-", self.mVPatchPre)):
            if act.isGroup(key):
                ctrl.userAction(act)
                return
        if act.isAction("menu-preferences"):
            self.mDialog_Preferences.execute()
            act.done()
            return
        if act.isAction("menu-exit"):
            self.doExit(True)
            act.done()
            return
        if act.isAction("menu-about"):
            self.dialogAbout()
            act.done()
            return
        if act.isGroup("menu-report-"):
            self.mProject.makeReport(act.getOpName())
            act.done()
            return
        if act.isAction("all-save"):
            # Nothing to do
            act.done()
            return
        if act.isAction("relax"):
            act.done()
            return
        if act.isAction("update"):
            self.mEnv.needsUpdate()
            act.done()
            return
        if act.isAction("veronica-raise"):
            self.getEnv().raiseMainOnTop()
            act.done()
            return
        if act.isAction("image-zoom-in"):
            if self.mCombo_Zoom.sibbling(-1):
                self.mImagePre.checkZoom()
                self.getEnv().needsUpdate()
            act.done()
            return
        if act.isAction("image-zoom-out"):
            if self.mCombo_Zoom.sibbling(1):
                self.mImagePre.checkZoom()
                self.getEnv().needsUpdate()
            act.done()
            return

    def needsUpdate(self, feature=None, check_guard=True):
        if check_guard:
            assert not RT_Guard.isFree()
        self.mNeedsUpdate = True
        if feature:
            self.mFeaturesToUpdate.add(feature)

    def forceUpdate(self):
        self.needsUpdate(check_guard=False)
        self.getEnv().postAction("relax")

    def checkUpdate(self):
        if self.mNeedsUpdate:
            self.update()
        if self.mExitReady:
            self.mEnv.quit()

    def update(self):
        assert not RT_Guard.isFree()
        self.mNeedsUpdate = False
        self.mDirPre.update()
        self.mImagePre.update()
        self.mImgEntryPre.update()
        self.mVPatchPre.update()
        self.mEnv.flushAlerts()

    def getImagePixmapHandler(self, image_h):
        if image_h is None:
            return None
        img_path = image_h.getImagePath()
        if not img_path:
            return False
        return self.mImgPool.getPixmapHandler(img_path)

    def dialogAbout(self):
        message = "\n".join([
            msg("menu.title"),
            msg("menu.version", Config.VERSION),
            msg("menu.vendor")])
        msg_box = QtWidgets.QMessageBox(0,
            qt_str(msg("menu.about")), qt_str(message))
        msg_box.setIconPixmap(
            self.mEnv.getUIApp().getPixmap("veronica.png"))
        msg_box.exec_()

    def doExit(self, can_return = False):
        if self.mExitReady:
            self.mEnv.quit()
            return True
        self.mEnv.getUICtrl().checkPersistentProperties(self.mEnv)
        self.mExitReady = True
        self.mVPatchPre.exit()
        return True

    def getCurZoom(self):
        return int(self.mCombo_Zoom.getValue().partition('%')[0])

    def getCurOpacity(self):
        return int(self.mCombo_Opacity.getValue())

    def _imgZoomChange(self, par, pos):
        if par == 0.:
            return
        with RT_Guard():
            if self.mCombo_Zoom.sibbling(par):
                self.mImagePre.checkZoom()
                self.getEnv().needsUpdate()

    def getCurImage(self):
        return self.mCurImage

    def setCurImage(self, image_h):
        self.mCurImage = image_h
        self.getEnv().needsUpdate()

    def updateImage(self, image_h):
        self.mDirPre.updateImage(image_h)

    def blockEntry(self, value):
        self.mDirPre.setDisabled(value)

    def getCurRound(self):
        return self.mDirPre.getCurRound()
