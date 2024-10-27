from copy import deepcopy
import json

#=========================================
class AnnotationChangeCommand:
    def __init__(self, image_h, round_h,
            new_data = False, cur_loc = None):
        self.mImageH = image_h
        self.mRoundH = round_h
        self.mDataPrev = self.mImageH.getAnnotationData(self.mRoundH)
        if new_data is False:
            self.mDataForw = (deepcopy(self.mDataPrev)
                if self.mDataPrev is not None else {})
        else:
            self.mDataForw = new_data
            self.hasChanges(True)
        self.mLocPrev = cur_loc
        self.mLocForw = cur_loc

    def dataToUpdate(self):
        return self.mDataForw

    def getRoundH(self):
        return self.mRoundH

    def hasChanges(self, assert_it = False):
        dump1, dump2 = (json.dumps(data, sort_keys=True)
            for data in (self.mDataPrev, self.mDataForw))
        assert not assert_it or dump1 != dump2, (
            "No changes in command: " + dump1)
        return dump1 != dump2

    def doIt(self):
        annotation_h = self.mRoundH.getAnnotation(
            self.mImageH.getLongName(), True)
        annotation_h.setData(self.mDataForw)

    def postLoc(self, loc):
        self.mLocForw = loc

    def undoIt(self):
        annotation_h = self.mRoundH.getAnnotation(
            self.mImageH.getLongName(), True)
        annotation_h.setData(self.mDataPrev)
        return self.mLocPrev

    def redoIt(self):
        annotation_h = self.mRoundH.getAnnotation(
            self.mImageH.getLongName(), True)
        annotation_h.setData(self.mDataForw)
        return self.mLocForw
