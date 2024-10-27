from pymongo import MongoClient

from .round import AnnotationRound
#===============================================
class AnnotationStorage:
    def __init__(self, project):
        self.mProject = project

        host = self.mProject.getInfo("mongo-host", "localhost")
        port = self.mProject.getInfo("mongo-port", 27017)
        top_path = self.mProject.getInfo("mongo-top", "Veronica")

        self.mAgent = MongoClient(host, port)[top_path][
            self.mProject.getName()]

        #  TODO: errors & checks, new/update/delete
        self.mRounds = {it["name"]: AnnotationRound(self, it)
            for it in self.mAgent.find({"_tp": "round"})
        }

        for tp, name in (("info", "info"), ("learn", "learn")):
            if name not in self.mRounds:
                self.createRound(name, tp)

    def getAgent(self):
        return self.mAgent

    def iterRounds(self):
        return self.mRounds.values()

    def getRound(self, name):
        return self.mRounds.get(name)

    def createRound(self, name, tp):
        assert name not in self.mRounds
        descr = {"_tp": "round", "name": name, "type": tp}
        self.mAgent.update_one(descr, {"$set": descr}, upsert = True)
        self.mRounds[name] = AnnotationRound(self, descr)
