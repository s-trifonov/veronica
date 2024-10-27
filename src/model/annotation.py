from datetime import datetime

#===============================================
class Annotation:
    def __init__(self, round, filename, data = None):
        self.mRound = round
        self.mFileName = filename
        self.mData = data
        self.mStoredData = data
        self.mStateCouter = 0

    def getRound(self):
        return self.mRound

    def getFileName(self):
        return self.mFileName

    def getData(self):
        return self.mData

    def getStateCounter(self):
        return self.mStateCouter

    def setData(self, data):
        self.mData = data
        self.mStateCouter += 1

    def needsSave(self):
        return self.mData is not self.mStoredData

    def reload(self):
        self.mData = self.mStoredData
        self.mStateCouter += 1

    def doSave(self):
        assert self.needsSave()
        query = {
            "_tp": "annotation",
            "round": self.mRound.getName(),
            "file": self.mFileName}

        if self.mData is None:
            self.mRound.getStorage().getAgent().delete_one(query)
        else:
            descr = {
                **query,
                "data": self.mData,
                "upd-time": datetime.now().isoformat()}
            self.mRound.getStorage().getAgent().update_one(
                query, {"$set": descr}, upsert = True)
        self.mStoredData = self.mData
