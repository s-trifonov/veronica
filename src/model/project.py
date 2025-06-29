import json, os
from .storage import AnnotationStorage
from .dir_h import DirHandler
from .report import htmlFullReport
#=========================================
class Project:
    V_MODE = "Vesiculae.0"

    def __init__(self, project_path, env, adv_mode):
        self.mEnv = env
        self.mProjPath = project_path

        #  TODO: errors & checks, new/update/delete
        with open(project_path, "r", encoding = "utf-8") as input:
            self.mInfo = json.loads(input.read())

        prj_mode = self.mInfo.get("prj-mode", self.V_MODE)
        assert prj_mode == self.V_MODE, (
            f"Mode {prj_mode} not supported, use {self.V_MODE}")

        self.mName = self.mInfo["prj-name"]
        self.mAdvMode = adv_mode
        self.mObjDict = {}
        self.mViewIdCounter = 0
        self.mAnnotations = AnnotationStorage(self)
        self.mTopDirList = [DirHandler(self, dir_name)
            for dir_name in self.mInfo["dir-list"]]

    def getEnv(self):
        return self.mEnv

    def iterTopDirList(self):
        return iter(self.mTopDirList)

    def getName(self):
        return self.mName

    def iterRounds(self):
        return self.mAnnotations.iterRounds()

    def getRound(self, name):
        return self.mAnnotations.getRound(name)

    def getInfo(self, key, default = None):
        return self.mInfo.get(key, default)

    def hasAdvancedMode(self):
        return self.mAdvMode

    def listAnnotationTypes(self):
        return self.mAnnotations.listTypes()

    def listAnnotations(self, type = None):
        return self.mAnnotations.listAnnotations(type)

    def _regObject(self, obj_h):
        view_id = self.mViewIdCounter
        self.mViewIdCounter += 1
        self.mObjDict[view_id] = obj_h
        return view_id

    def findObject(self, view_id):
        return self.mImgDict[view_id]

    def _locateNewFile(self, extension, max_files=200):
        idx = -1
        while idx < max_files:
            idx += 1
            fname = self.mProjPath + f".{idx:03d}.{extension}"
            if not os.path.exists(fname):
                return fname
        self.mEnv.notifyStatus(f"Failed: too many {extension} files")
        return None

    def dumpData(self):
        dump_fname = self._locateNewFile("dump")
        if dump_fname is None:
            return
        with open(dump_fname, "w", encoding="utf-8") as outp:
            print(json.dumps(self.mAnnotations.getAllData(),
                indent=4, sort_keys=True, ensure_ascii=False), file=outp)
        self.mEnv.notifyStatus(f"Dump stored: ...{dump_fname[-45:]} ")

    def collectMetrics(self, max_count=None):
        report = []
        for dir_h in self.iterTopDirList():
            dir_h.collectMetrics(report, max_count)
        return report

    def reportMetricsJson(self, max_count=None):
        rep_fname = self._locateNewFile("report")
        if rep_fname is None:
            return
        all_data = self.collectMetrics(max_count)

        with open(rep_fname, "w", encoding="utf-8") as outp:
            print(json.dumps(all_data,
                indent=4, sort_keys=True, ensure_ascii=False), file=outp)
        self.mEnv.notifyStatus(f"Report stored: ...{rep_fname[-45:]} ")

    def reportMetricsHtml(self, max_count=None):
        rep_fname = self._locateNewFile("html")
        if rep_fname is None:
            return
        all_data = self.collectMetrics(max_count)
        htmlFullReport(all_data, rep_fname )
        self.mEnv.notifyStatus(f"Report stored: ...{rep_fname[-45:]} ")
