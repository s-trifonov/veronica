import os

from config.ver_cfg import Config
from .cmd_h import AnnotationChangeCommand

#=========================================
class ImageHandler:

    def __init__(self, dir_h, fpath):
        self.mDir = dir_h
        self.mViewId = self.mDir.getProject()._regObject(self)

        self.mStatusMsg = ""
        self.mFPath = fpath
        self.mName, _, self.mFExt = os.path.basename(self.mFPath).rpartition('.')
        self.mLongName = self.mDir.getViewPath() + self.mName

        if self.mFExt != "tif":
            self.mStatusMsg = f"Bad ext:{self.mFExt}"
        self.reset()
        self.mInAction = False

    def reset(self, force_reload=False):
        self.mRoundAnnotations = {}
        for round_h in self.mDir.getProject().iterRounds():
            annotation = round_h.getAnnotation(self.mLongName)
            if annotation is not None:
                self.mRoundAnnotations[round_h.getName()] = annotation
                if force_reload:
                    annotation.reload()

        self.mCmdStack = []
        self.mCurStackPos = 0

    def getDir(self):
        return self.mDir

    def getViewId(self):
        return self.mViewId

    def isOK(self):
        return self.mStatusMsg == ""

    def getName(self):
        return self.mName

    def getImagePath(self):
        return self.mFPath

    def getStatusMsg(self):
        return self.mStatusMsg

    def getLongName(self):
        return self.mLongName

    def hasErrors(self):
        return False

    def getAnnotation(self, round_h, force_create = False):
        if force_create and round_h.getName() not in self.mRoundAnnotations:
            self.mRoundAnnotations[round_h.getName()] = (
                round_h.getAnnotation(self.mLongName, True))

        return self.mRoundAnnotations.get(round_h.getName())

    def getAnnotationData(self, round_h, default=None):
        it = self.getAnnotation(round_h)
        if it is None:
            return default
        ret = it.getData()
        if ret is None:
            return default
        return ret

    def hasAnnotation(self, round_h):
        if (round_h is not None and round_h.getType() == "learn"
                and self.mDir.getSmpSupport().canAddToLearn(self)):
            return True
        return (round_h is None or
            round_h.getName() in self.mRoundAnnotations)

    def startAnnotationChange(self, round_h, new_data = False, cur_loc = None):
        assert not self.mInAction
        if self.mCurStackPos < len(self.mCmdStack):
            self.mCmdStack = self.mCmdStack[:self.mCurStackPos]
        assert len(self.mCmdStack) == self.mCurStackPos
        self.mCmdStack.append(AnnotationChangeCommand(
            self, round_h, new_data, cur_loc))
        self.mCurStackPos += 1
        self.mInAction = True
        return self.mCmdStack[-1].dataToUpdate()

    def finishAnnotationChange(self, post_loc = None):
        assert self.mInAction
        self.mInAction = False
        self.getAnnotation(self.mCmdStack[-1].getRoundH(), True)
        self.mCmdStack[-1].doIt()
        if post_loc is not None:
            self.mCmdStack[-1].postLoc(post_loc)
        self._cleanUp()

    def undoChange(self):
        assert not self.mInAction
        assert self.mCurStackPos > 0
        self.mCurStackPos -= 1
        return self.mCmdStack[self.mCurStackPos].undoIt()

    def redoChange(self):
        assert not self.mInAction
        assert self.mCurStackPos < len(self.mCmdStack)
        self.mCurStackPos += 1
        return self.mCmdStack[self.mCurStackPos - 1].doIt()

    def doSave(self):
        for annotation in self.mRoundAnnotations.values():
            if annotation.needsSave():
                annotation.doSave()
        self._cleanUp()

    def getAvailableActions(self):
        ret = []
        if any(annotation.needsSave()
                for annotation in self.mRoundAnnotations.values()):
            ret += ["save", "clear-changes"]
        if self.mCurStackPos > 0:
            ret.append("undo")
        if self.mCurStackPos < len(self.mCmdStack):
            ret.append("redo")
        return ret

    def _cleanUp(self):
        dd = len(self.mCmdStack) - Config.MAX_STORING_EDIT_STEPS
        if dd > 0 and self.mCurStackPos >= len(self.mCmdStack):
            self.mCmdStack = self.mCmdStack[dd:]
            self.mCurStackPos -= dd
