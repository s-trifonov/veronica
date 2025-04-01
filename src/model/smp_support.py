from hashlib import md5
from config.ver_cfg import Config

#=========================================
class SampleListingSupport:
    def __init__(self, dir_h, smp_round_h):
        self.mDirH = dir_h
        self.mSmpRoundH = smp_round_h
        self.mImageNoDict = None
        self.mImageNoList = None
        self.mImageStatusDict = None
        self.resetState()

    def sameRound(self, round_h):
        return self.mSmpRoundH is round_h

    def resetState(self):
        sheet = [
            (md5((image_h.getName() + Config.SMP_KEY).
                encode("utf-8")).hexdigest(), image_h.getName())
            for image_h in self.mDirH.getImages()]
        sheet.sort()

        self.mImageNoDict = {rec[1] : idx + 1
            for idx, rec in enumerate(sheet)}

        self.mImageStatusDict = {}
        for image_h in self.mDirH.getImages():
            learn_data = image_h.getAnnotationData(self.mSmpRoundH)
            if learn_data is None:
                continue
            q_ready = learn_data.get("status") == "ready"
            self.mImageStatusDict[
                self.mImageNoDict[image_h.getName()]] = q_ready
        self.mImageNoList = list(sorted(self.mImageStatusDict.keys()))

        unready_count = sum(q_ready is False
            for q_ready in self.mImageNoDict.values())
        if (len(self.mImageNoList) < len(self.mImageNoDict) and
                unready_count < Config.SMP_UNREADY_FREE_COUNT):
            for idx, no in enumerate(self.mImageNoList):
                if idx + 1 != no:
                    self.mImageNoList.insert(idx, idx+1)
                    break

    def getImageNo(self, image_h):
        return self.mImageNoDict.get(image_h.getName(), -1)

    def getImageStatus(self, image_h):
        no = self.getImageNo(image_h)
        return self.mImageStatusDict.get(no)

    def canAddToLearn(self, image_h):
        no = self.getImageNo(image_h)
        if no in self.mImageStatusDict:
            return False
        return no in self.mImageNoList

    def getImages(self):
        ret = [None] * len(self.mImageNoList)
        for image_h in self.mDirH.getImages():
            img_no = self.mImageNoDict.get(image_h.getName())
            if img_no in self.mImageNoList:
                ret[self.mImageNoList.index(img_no)] = image_h
        for image_h in ret:
            if image_h is not None:
                yield image_h
