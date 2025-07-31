import os
from glob import glob
from config.ver_cfg import Config
from .img_h import ImageHandler
from .smp_support import SampleListingSupport
from .metrics import evalMetrics

#=========================================
class DirHandler:
    def __init__(self, project,
            dir_path = None, parent = None, dir_name = None):
        self.mProject = project
        self.mParent = parent
        self.mDirName = dir_name
        self.mStatusMsg = ""
        self.mViewId = self.mProject._regObject(self)
        if self.mParent is None:
            self.mViewPath = "/"
            self.mDirPath = dir_path
        else:
            self.mViewPath = self.mParent.getViewPath() + dir_name + "/"
            self.mDirPath = self.mParent.getDirPath() + dir_name + "/"
        self.mImages = [ImageHandler(self, fname)
            for fname in glob(self.mDirPath + "/*.tif")]
        self.mImages.sort(key=lambda img: img.getName())
        self.mSmpSupport = SampleListingSupport(self,
            self.mProject.getRound(Config.SMP_ROUND))

        self.mDirectories = []
        for fname in os.listdir(self.mDirPath):
            if os.path.isdir(self.mDirPath + "/" + fname):
                self.mDirectories.append(DirHandler(self.mProject,
                    parent = self, dir_name = fname))
        self.mDirectories.sort(key=lambda dir: dir.getViewPath())

    def getProject(self):
        return self.mProject

    def getViewId(self):
        return self.mViewId

    def getDirName(self):
        return self.mDirName

    def getDirPath(self):
        return self.mDirPath

    def getViewPath(self):
        return self.mViewPath

    def getParent(self):
        return self.mParent

    def isEmpty(self, round = None):
        for image_h in self.mImages:
            if image_h.hasAnnotation(round):
                return False
        for dir_h in self.mDirectories:
            if not dir_h.isEmpty(round):
                return False
        return True

    def getSmpSupport(self):
        return self.mSmpSupport

    def getImages(self):
        return self.mImages

    def getDirectories(self):
        return self.mDirectories

    def getCurImageH(self):
        if (0 <= self.mCurIdx < len(self.mImages)):
            return self.mImages[self.mCurIdx]
        return None

    def getCurIdx(self):
        if (0 <= self.mCurIdx < len(self.mImages)):
            return self.mCurIdx
        return None

    def setCur(self, idx):
        self.mCurIdx = idx

    def getStatusMsg(self):
        return self.mStatusMsg

    def collectMetrics(self, report, max_count=None):
        for dir_h in self.getDirectories():
            dir_h.collectMetrics(report, max_count )
        rep = []
        for image_h in self.mSmpSupport.getImages():
            if self.mSmpSupport.getImageStatus(image_h) is not True:
                continue
            ldata = image_h.getAnnotationData(self.mProject.getRound("learn"))
            if "seq" in ldata:
                rep.append(evalMetrics(image_h.getName(), ldata["seq"]))
                if max_count is not None and len(rep) == max_count:
                    break
        if len(rep) > 0:
            report.append({
                "dir": self.getDirName(),
                "rep":rep})
        return len(rep) > 0
