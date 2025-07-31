from h2tools.tools_qt import newQItem, qt_str
from config.messenger import msg
from model.v_types import VType
from model.metrics import evalMetrics
from .markup_ctrl import MarkupPathController
from .detect_ctrl import DetectController

#=================================
class ImageEntryPresentation:
    def __init__(self, top_pre):
        self.mTopPre = top_pre

        self.mTabBox = self.mTopPre.getEnv().getWidget("img-entry-tabbox")
        self.mTabs = {
            key: self.mTopPre.getEnv().getWidget("img-entry-tab-" + key)
            for key in ("info", "learn", "detect", "metrics")
        }

        self.mRounds = {
            key: self.mTopPre.getProject().getRound(key)
            for key in ("info", "learn")
        }

        self.mInfoCtrl = {
            key: self.mTopPre.getEnv().getWidget("info-edit-" + key)
            for key in ("quality", "mark", "note", "smp-no")
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

        self.mDetectParamsLine = self.mTopPre.getEnv().getWidget(
            "detect-line-params")
        self.mDetectCtrl = DetectController(self,
            self.mTopPre.getImagePre(), self.mDetectParamsLine)

        self.mMetricsReport = self.mTopPre.getEnv().getWidget(
            "img-metrics-report")

        if not self.mTopPre.getProject().hasAdvancedMode():
            self.mDetectCtrl = None
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
            if (self.mLearnData is None and self.mImageH.hasAnnotation(
                    self.mRounds["learn"])):
                self.mLearnData = {"status": None}
        else:
            self.mInfoData, self.mLearnData = {}, None

        self.mTabs["learn"].setDisabled(self.mLearnData is None)
        self.mTabs["info"].setDisabled(self.mImageH is None)
        self.mTabs["detect"].setDisabled(self.mImageH is None
            or self.mDetectCtrl is None)

        if self.mDetectCtrl is not None:
            self.mDetectCtrl.updateImage(self.mImageH)

        forward_loc, self.mForwardLoc = self.mForwardLoc, None
        forward_idx = None
        if forward_loc is not None:
            if isinstance(forward_loc, str):
                tab_loc = forward_loc
            else:
                tab_loc, forward_idx = forward_loc
        else:
            tab_loc = "info"
            if (self.mLearnData is not None and
                    self.mTopPre.getCurRound() is not None and
                    self.mTopPre.getCurRound().getType() == "learn"):
                tab_loc = "learn"
        self.mTabs[tab_loc].setCurrent()

        self.mMarkupPathCtrl.reload(self._prepareMarkupInfo(), forward_idx)

        self.mInfoCtrl["quality"].setValue(self.mInfoData.get("quality", 0))
        self.mInfoCtrl["mark"].setValue(self.mInfoData.get("mark", "*"))
        self.mInfoCtrl["note"].setText(self.mInfoData.get("note", ""))
        self.mInfoCtrl["smp-no"].setText(
            str(self.mImageH.getDir().getSmpSupport().getImageNo(self.mImageH))
            if self.mImageH is not None else "")

        self.mTableView.clearModel()

        if self.mLearnData is not None:
            _no = 1
            for type, points in self._prepareMarkupInfo():
                self.mTableView.model().appendRow([
                    newQItem(str(_no), align = "right"),
                    newQItem(VType.getTypeDescr(type).getName()),
                    newQItem(str(len(points)))])
                _no += 1
        self.mInUpdate = False

        if (self.mImageH is not None and
                self.mImageH.getDir().getSmpSupport().
                getImageStatus(self.mImageH) is True):
            self.mTabs["metrics"].setDisabled(False)
            self.mMetricsReport.setText(qt_str(
                evalMetrics(self.mImageH.getName(),
                    self.mLearnData["seq"], report_mode=True)))
        else:
            self.mTabs["metrics"].setDisabled(True)

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
        #self.mTopPre.getEnv().disableAction("img-entry-to-learn",
        #    self.mImageH is None or not self.mImageH.getDir().
        #        getSmpSupport().canAddToLearn(self.mImageH))
        self.mTopPre.getEnv().disableAction("img-entry-out-of-learn",
            self.mImageH is None or self.mImageH.getDir().
                getSmpSupport().getImageStatus(self.mImageH) is None)

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
            self.mTopPre.getImagePre().runMarkupCtrl(
                self.mDetectCtrl if self.mTabs["detect"].isCurrent() else None)
        self.mPostNewPath = False

        cur_path = self.mMarkupPathCtrl.getCurPath()
        if cur_path is not None:
            self.mComboPathType.setValue(cur_path.getType())
            self.mTableView.selectRow(self.mMarkupPathCtrl.getCurPathIdx())
            self.mTableView.scrollToLine(self.mMarkupPathCtrl.getCurPathIdx())
        self.mTopPre.getEnv().disableAction("img-entry-path-create",
            not learn_mode)
        self.mTopPre.getEnv().disableAction("img-entry-path-delete",
            cur_path is None)

        new_path = self.mMarkupPathCtrl.getNewPath()
        self.mButtonPathCreate.setChecked(new_path is not None)
        can_change_type = cur_path is None and new_path is None
        enable_all_types = True
        if new_path is not None:
            can_change_type = new_path.canChangeType()
            if not can_change_type:
                compatible_types = new_path.getCompatibleTypes()
                if len(compatible_types) > 1:
                    self.mComboPathType.setEnabledItems(
                        compatible_types, new_path.getType())
                    can_change_type = True
                    enable_all_types = False
        elif cur_path is not None:
            compatible_types = cur_path.getCompatibleTypes()
            if len(compatible_types) > 1:
                self.mComboPathType.setEnabledItems(
                    compatible_types, cur_path.getType())
                can_change_type = True
                enable_all_types = False
        if enable_all_types:
            self.mComboPathType.makeAllEnabled()
        self.mComboPathType.setDisabled(not can_change_type)

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
        if self.mLearnData["status"] is None:
            self.mImageH.startAnnotationChange(
                self.mRounds["learn"],
                {"status": "process"},
                cur_loc = self._curLoc())
            self.mImageH.finishAnnotationChange("learn")

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
        self.mTopPre.forceUpdate()

    #=====================
    def _resetImage(self, forward_loc = None):
        if forward_loc is not None:
            self.mForwardLoc = forward_loc
        elif self.mForwardLoc is None:
            self.mForwardLoc = self._curLoc()
        self.mTopPre.updateImage(self.mImageH)
        self.resetState()
        self.needsUpdate()

#    def keepTrainPack(self):
#        self.mTopPre.getEnv().notifyStatus(msg("train.pack.work"))
#        pixmap_h = self.mTopPre.getImagePixmapHandler(
#            self.mImageH).getPixmap()
#        train_pack = TrainStrokePack(self.mTopPre.getEnv(),
#            self.mImageH, pixmap_h.width(), pixmap_h.height(),
#            self.mMarkupPathCtrl.getPathSeq())
#        round_h = self.mTopPre.getProject().getRound("lpack")
#        annotation_h = round_h.getAnnotation(
#            self.mImageH.getLongName(), True)
#        pack_info = train_pack.getResult()
#        annotation_h.setData(pack_info)
#        annotation_h.doSave()
#
#        self.mTopPre.getEnv().notifyStatus(
#            msg("train.pack.kept", pack_info["total"]))

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
            assert False
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
                data["status"] = ("ready"
                    if data.get("status") != "ready" else "process")
                self.mImageH.finishAnnotationChange()
                self.mImageH.doSave()
                #if data["status"] == "ready":
                #    self.keepTrainPack()
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
            new_type = self.mComboPathType.getValue()
            if (new_path is not None and new_path.canChangeType(new_type)):
                self.mMarkupPathCtrl.subScenario().changePathType(new_type)
                self.mTopPre.getEnv().needsUpdate()
            else:
                cur_path = self.mMarkupPathCtrl.getCurPath()
                if (cur_path and cur_path.getType() != new_type and
                        cur_path.canChangeType(new_type)):
                    cur_path.changeType(new_type)
                    self.pathChanged(cur_path,
                        self.mMarkupPathCtrl.getCurPathIdx())
            act.done()
            return

        if act.isAction("detect-line"):
            if self.mDetectCtrl is not None:
                self.mDetectCtrl.startDetectLine()
            act.done()
            return
