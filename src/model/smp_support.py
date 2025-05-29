from hashlib import md5
from config.ver_cfg import Config

#=========================================
class SampleListingSupport:
    def __init__(self, dir_h, smp_round_h):
        self.mDirH = dir_h
        self.mSmpRoundH = smp_round_h
        self.mImageNoDict = None
        self.mImageNoList = None
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

        self.mImageNoList = []
        for image_h in self.mDirH.getImages():
            if self.getImageStatus(image_h) is not None:
                self.mImageNoList.append(self.mImageNoDict[image_h.getName()])
        self.mImageNoList.sort()

        unready_count = sum(q_ready is False
            for q_ready in self.mImageNoDict.values())
        while (len(self.mImageNoList) < len(self.mImageNoDict) and
                unready_count < Config.SMP_UNREADY_FREE_COUNT):
            q_done = False
            for idx, no in enumerate(self.mImageNoList):
                if idx + 1 != no:
                    self.mImageNoList.insert(idx, idx+1)
                    q_done = True
                    break
            if not q_done:
                self.mImageNoList.append(len(self.mImageNoList) + 1)
            unready_count += 1

    def getImageNo(self, image_h):
        return self.mImageNoDict.get(image_h.getName(), -1)

    def getImageStatus(self, image_h):
        learn_data = image_h.getAnnotationData(self.mSmpRoundH)
        if learn_data is None:
            return None
        if learn_data.get("status") == "ready":
            return True
        if not learn_data.get("seq"):
            return None
        return False

    def canAddToLearn(self, image_h):
        no = self.getImageNo(image_h)
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
