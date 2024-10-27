import json
from .storage import AnnotationStorage
from .dir_h import DirHandler
#=========================================
class Project:
    def __init__(self, project_path, env, adv_mode):
        self.mEnv = env
        self.mProjPath = project_path

        #  TODO: errors & checks, new/update/delete
        with open(project_path, "r", encoding = "utf-8") as input:
            self.mInfo = json.loads(input.read())

        self.mName = self.mInfo["prj-name"]
        self.mAdvMode = adv_mode
        self.mObjDict = {}
        self.mViewIdCounter = 0
        self.mAnnotations = AnnotationStorage(self)
        self.mTopDir = DirHandler(self, self.mInfo["dir"])

    def getEnv(self):
        return self.mEnv

    def getTopDir(self):
        return self.mTopDir

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
