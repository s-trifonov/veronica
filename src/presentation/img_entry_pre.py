from h2tools.tools_qt import newQItem
from config.messenger import msg
from .markup_ctrl import MarkupPathController

#=================================
class ImageEntryPresentation:
    def __init__(self, top_pre):
        self.mTopPre = top_pre

        self.mTabBox = self.mTopPre.getEnv().getWidget("img-entry-tabbox")
        self.mTabs = {
            key: self.mTopPre.getEnv().getWidget("img-entry-tab-" + key)
            for key in ("info", "learn")
        }

        self.mRounds = {
            key: self.mTopPre.getProject().getRound(key)
            for key in ("info", "learn")
        }

        self.mInfoCtrl = {
            key: self.mTopPre.getEnv().getWidget("info-edit-" + key)
            for key in ("quality", "mark", "note")
        }

        self.mTableView = self.mTopPre.getEnv().getWidget(
            "markup-path-table")
        self.mTableView._setupSelectionChange(self.onChangeSelection)

        self.mActMarkupDone = self.mTopPre.getEnv().getUIAction(
            "img-entry-markup-done")

        self.mButtonMarkupDone = self.mTopPre.getEnv().getWidget(
            "markup-done")
        self.mButtonPathCreate = self.mTopPre.getEnv().getWidget(
            "markup-path-create")
        self.mComboPathType = self.mTopPre.getEnv().getWidget(
            "markup.path.type")

        self.mMarkupPathCtrl = MarkupPathController(self,
            self.mTopPre.getImagePre())

        self.mImageH = False
        self.mInfoData = None
        self.mLearnData = None
        self.mForwardLoc = None
        self.mPostNewPath = False
        self.mInUpdate = False

    def resetState(self):
        self.mInUpdate = True
        self.mImageH = self.mTopPre.getCurImage()
        if self.mImageH is not None:
            self.mInfoData = self.mImageH.getAnnotationData(
                self.mRounds["info"], {})
            self.mLearnData = self.mImageH.getAnnotationData(
                self.mRounds["learn"])
        else:
            self.mInfoData, self.mLearnData = {}, None

        self.mTabs["learn"].setDisabled(self.mLearnData is None)
        self.mTabs["info"].setDisabled(self.mImageH is None)

        forward_loc, self.mForwardLoc = self.mForwardLoc, None
        forward_idx = None
        if forward_loc is not None:
            if isinstance(forward_loc, str):
                tab_loc = forward_loc
            else:
                tab_loc, forward_idx = forward_loc
        else:
            if self.mLearnData is None:
                tab_loc = "info"
            elif (self.mLearnData is not None and
                    self.mTopPre.getCurRound() is not None and
                    self.mTopPre.getCurRound().getType() == "learn"):
                tab_loc = "learn"
        self.mTabs[tab_loc].setCurrent()

        self.mMarkupPathCtrl.reload(self._prepareMarkupInfo(), forward_idx)

        self.mInfoCtrl["quality"].setValue(self.mInfoData.get("quality", 0))
        self.mInfoCtrl["mark"].setValue(self.mInfoData.get("mark", "*"))
        self.mInfoCtrl["note"].setText(self.mInfoData.get("note", ""))

        self.mTableView.clearModel()

        if self.mLearnData is not None:
            _no = 1
            for type, points in self._prepareMarkupInfo():
                self.mTableView.model().appendRow([
                    newQItem(str(_no), align = "right"),
                    newQItem(self.mTopPre.getMarkupTypeName(type)),
                    newQItem(str(len(points)))])
                _no += 1
        self.mInUpdate = False

    def update(self):
        if self.mImageH is not self.mTopPre.getCurImage():
            self.resetState()
        self.mInUpdate = True

        if self._infoChanged():
            avail_op = ["save", "clear-changes"]
        elif self.mImageH is not None:
            avail_op = self.mImageH.getAvailableActions()
        else:
            avail_op = []
        for key in ("save", "clear-changes", "undo", "redo"):
            self.mTopPre.getEnv().disableAction("img-entry-" + key,
                key not in avail_op)
        self.mTopPre.getEnv().disableAction("img-entry-to-learn",
            self.mLearnData is not None)
        self.mTopPre.getEnv().disableAction("img-entry-out-of-learn",
            self.mLearnData is None)

        self.mTopPre.blockEntry("save" in avail_op)
        self.mButtonMarkupDone.setHidden(not self.mTabs["learn"].isCurrent())

        learn_mode = self.mTabs["learn"].isCurrent()
        if learn_mode:
            if not self.mMarkupPathCtrl.isActive():
                self.mTopPre.getImagePre().runMarkupCtrl(self.mMarkupPathCtrl)
            if self.mPostNewPath:
                self._startNewPath()
        elif self.mMarkupPathCtrl.isActive():
            self.mMarkupPathCtrl.clearNewPath()
            self.mTopPre.getImagePre().runMarkupCtrl(None)
        self.mPostNewPath = False

        cur_path = self.mMarkupPathCtrl.getCurPath()
        new_path = self.mMarkupPathCtrl.getNewPath()
        if cur_path is not None:
            self.mComboPathType.setValue(cur_path.getType())
            self.mTableView.selectRow(self.mMarkupPathCtrl.getCurPathIdx())
            self.mTableView.scrollToLine(self.mMarkupPathCtrl.getCurPathIdx())
        self.mTopPre.getEnv().disableAction("img-entry-path-create",
            not learn_mode)
        self.mTopPre.getEnv().disableAction("img-entry-path-delete",
            cur_path is None)
        self.mButtonPathCreate.setChecked(new_path is not None)
        self.mComboPathType.setDisabled(new_path is None or
            not new_path.canChangeType())
        self.mTableView.setDisabled(new_path is not None)

        self.mTopPre.getEnv().disableAction("img-entry-markup-done",
            self.mLearnData is None)
        self.mActMarkupDone.setDisabled(self.mLearnData is None)
        self.mActMarkupDone.setChecked(self.mLearnData is not None and
            self.mLearnData["status"] == "ready")

        self.mButtonMarkupDone.setHidden(self.mLearnData is None)
        self.mButtonMarkupDone.setChecked(self.mLearnData is not None and
            self.mLearnData["status"] == "ready")
        self.mInUpdate = False

    def _startNewPath(self):
        self.mMarkupPathCtrl.startNewPath(self.mComboPathType.getValue())

    def _infoChanged(self):
        if self.mImageH is None:
            return False
        if (self.mInfoCtrl["quality"].value() !=
                self.mInfoData.get("quality", 0)):
            return True
        if (self.mInfoCtrl["note"].text() !=
                self.mInfoData.get("note", "")):
            return True
        if (self.mInfoCtrl["mark"].getValue() !=
                self.mInfoData.get("mark", "*")):
            return self.mInfoCtrl["note"].text().strip() != ""
        return False

    def _makeChangedInfo(self):
        ret = {}
        quality = self.mInfoCtrl["quality"].value()
        if quality > 0:
            ret["quality"] = quality
        note = self.mInfoCtrl["note"].text().strip()
        if note != "":
            ret["note"] = note
            ret["mark"] = self.mInfoCtrl["mark"].getValue()
        if len(ret) > 0:
            return ret
        return None

    def onChangeSelection(self):
        if self.mMarkupPathCtrl.isActive() and not self.mInUpdate:
            index = self.mTableView.selectionModel().currentIndex()
            if index is not None:
                self.mMarkupPathCtrl.setCurPath(index.row(), True)
                self.needsUpdate()

    #=====================
    def _curLoc(self):
        if self.mTabs["learn"].isCurrent():
            return ("learn", self.mMarkupPathCtrl.getCurPathIdx())
        return "info"

    def _prepareMarkupInfo(self):
        if self.mLearnData is not None and "seq" in self.mLearnData:
            return self.mLearnData["seq"][:]
        return []

    def newPathCompleted(self, path_ctrl):
        data = self.mImageH.startAnnotationChange(
            self.mRounds["learn"], cur_loc = self._curLoc())
        if "seq" not in data:
            data["seq"] = []
        path_obj = path_ctrl.getPath()
        data["seq"].append([
            path_obj.getType(),
            [list(pp) for pp in path_obj.getPoints()]])
        self.mForwardLoc = ("learn", self.mMarkupPathCtrl.getPathCount())
        self.mImageH.finishAnnotationChange(self.mForwardLoc)
        self.mPostNewPath = True
        self._resetImage()

    def pathChanged(self, path_obj, path_idx):
        data = self.mImageH.startAnnotationChange(
            self.mRounds["learn"], cur_loc = self._curLoc())
        data["seq"][path_idx] = [
            path_obj.getType(),
            [list(pp) for pp in path_obj.getPoints()]]
        self.mImageH.finishAnnotationChange()
        self._resetImage()

    def pathDelete(self, path_idx):
        if path_idx is None or path_idx < 0:
            return
        data = self.mImageH.startAnnotationChange(
            self.mRounds["learn"], cur_loc = ("learn", path_idx))
        del data["seq"][path_idx]
        self.mForwardLoc = ("learn", max(path_idx - 1, 0))
        self.mImageH.finishAnnotationChange(self.mForwardLoc)
        self._resetImage()

    def needsUpdate(self):
        self.mTopPre.needsUpdate(check_guard=False)
        self.mTopPre.getEnv().postAction("relax")

    #=====================
    def _resetImage(self, forward_loc = None):
        if forward_loc is not None:
            self.mForwardLoc = forward_loc
        elif self.mForwardLoc is None:
            self.mForwardLoc = self._curLoc()
        self.mTopPre.updateImage(self.mImageH)
        self.resetState()
        self.needsUpdate()

    def userAction(self, act):
        if act.isAction("tab"):
            self.mTopPre.getEnv().needsUpdate()
            act.done()
            return

        if act.isAction("edit-info"):
            self.mTopPre.getEnv().needsUpdate()
            act.done()
            return

        if act.isAction("save"):
            if self._infoChanged():
                self.mImageH.startAnnotationChange(
                    self.mRounds["info"],
                    self._makeChangedInfo(),
                    cur_loc = self._curLoc())
                self.mImageH.finishAnnotationChange()
            self.mImageH.doSave()
            self._resetImage()
            act.done()
            return

        if act.isAction("clear-changes"):
            if not self._infoChanged() and self.mImageH is not None:
                self.mImageH.reset(True)
            self._resetImage()
            act.done()
            return

        if act.isAction("undo"):
            if (self.mImageH is not None and not self._infoChanged()
                    and "undo" in self.mImageH.getAvailableActions()):
                self.mForwardLoc = self.mImageH.undoChange()
                self._resetImage()
                act.done()
            return

        if act.isAction("redo"):
            if (self.mImageH is not None and not self._infoChanged()
                    and "redo" in self.mImageH.getAvailableActions()):
                self.mForwardLoc = self.mImageH.redoChange()
                self._resetImage()
                act.done()
            return

        if act.isAction("to-learn"):
            if self.mLearnData is None:
                self.mImageH.startAnnotationChange(
                    self.mRounds["learn"],
                    {"status": "process"},
                    cur_loc = self._curLoc())
                self.mImageH.finishAnnotationChange("learn")
                self.mImageH.doSave()
                self.mImageH.reset(True)
                self._resetImage(("learn", None))
                act.done()
            return

        if act.isAction("out-of-learn"):
            if self.mLearnData is not None:
                ret = self.mTopPre.getEnv().confirm(
                    msg("img.out-of-learn.confirm"),
                    (msg("img.out-of-learn.yes"), msg("img.out-of-learn.no")))
                if ret == 0:
                    self.mImageH.startAnnotationChange(
                        self.mRounds["learn"], None, cur_loc = self._curLoc())
                    self.mImageH.finishAnnotationChange("info")
                    self.mImageH.doSave()
                    self.mImageH.reset(True)
                    self._resetImage("info")
                act.done()
            return

        if act.isAction("markup-done"):
            if self.mLearnData is not None:
                data = self.mImageH.startAnnotationChange(
                    self.mRounds["learn"], cur_loc = self._curLoc())
                data["status"] = "ready" if data.get("status") != "ready" else "process"
                self.mImageH.finishAnnotationChange()
                self.mImageH.doSave()
                self.mImageH.reset(True)
                self._resetImage()
                act.done()
            return

        if act.isAction("path-create"):
            if self.mMarkupPathCtrl.isActive():
                if self.mMarkupPathCtrl.getNewPath() is None:
                    self.mTableView.clearSelection()
                    self._startNewPath()
                else:
                    self.mMarkupPathCtrl.clearNewPath()
                self.mTopPre.getEnv().needsUpdate()
            act.done()
            return

        if act.isAction("path-delete"):
            cur_path_idx = self.mMarkupPathCtrl.getCurPathIdx()
            if cur_path_idx is not None:
                self.pathDelete(cur_path_idx)
            act.done()
            return

        if act.isAction("markup-type"):
            new_path = self.mMarkupPathCtrl.getNewPath()
            if (new_path is not None and new_path.canChangeType()):
                self.mMarkupPathCtrl.subScenario().changePathType(
                    self.mComboPathType.getValue())
                self.mTopPre.getEnv().needsUpdate()
            act.done()
            return
