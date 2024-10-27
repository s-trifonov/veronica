from .annotation import Annotation
#===============================================
class AnnotationRound:
    def __init__(self, storage, descr = None):
        self.mStorage = storage
        self.mDescrObj = descr
        self.mName = self.mDescrObj["name"]
        self.mType = self.mDescrObj["type"]
        self.mAnnotations = {
            it["file"]: Annotation(self, it["file"], it["data"])
            for it in self.mStorage.getAgent().find(
                {"_tp": "annotation", "round": self.mName})
        }

    def getName(self):
        return self.mName

    def getType(self):
        return self.mType

    def getStorage(self):
        return self.mStorage

    def getAnnotation(self, filename, force_create = False):
        if filename not in self.mAnnotations:
            if force_create:
                self.mAnnotations[filename] = Annotation(self, filename)
            else:
                return None
        return self.mAnnotations[filename]

