#import sys
from bisect import bisect_left
from .utils import raiseRuntimeError
from .diap import OrdDiapason
#====================================
class SortedArray:
    def __init__(self, idx_func, objects = None):
        self.mOrdF = idx_func
        if objects is not None:
            self.mObjects = sorted(objects, key = self.mOrdF)
            self.mOrder = [self.mOrdF(obj) for obj in self.mObjects]
        else:
            self.mObjects = []
            self.mOrder   = []

    def __len__(self):
        return len(self.mObjects)

    def __getitem__(self, idx):
        return self.mObjects[idx]

    def __iter__(self):
        return iter(self.mObjects)

    def isEmpty(self):
        return len(self.mObjects) == 0

    def append(self, obj):
        ord_no = self.mOrdF(obj)
        if len(self.mObjects) > 0 and ord_no <= self.mOrder[-1]:
            raiseRuntimeError("Bad sort order in bisect")
        self.mObjects.append(obj)
        self.mOrder.append(ord_no)

    def insert(self, obj):
        ord_no = self.mOrdF(obj)
        if len(self.mObjects) > 0 and ord_no > self.mOrder[0]:
            raiseRuntimeError("Bad sort order in bisect")
        self.mObjects.insert(0, obj)
        self.mOrder.insert(0, ord_no)

    def leftFind(self, obj):
        return self.leftFindByKey(self.mOrdF(obj))

    def leftFindByKey(self, key):
        idx = self.idxByKey(key)
        if idx < 0:
            return None
        return self.mObjects[idx]

    def idxByKey(self, key):
        if len(self.mObjects) == 0:
            return -1
        idx = bisect_left(self.mOrder, key)
        if idx >= len(self.mObjects):
            idx = len(self.mObjects) - 1
        elif self.mOrder[idx] > key:
            idx -= 1
        return idx

    def diapByIdx(self, idx, norm_it = True):
        if idx + 1 < len(self.mOrder):
            start, end = self.mOrder[idx], self.mOrder[idx + 1]
            if norm_it:
                start, end = start[0], end[0]
            return OrdDiapason(start, end)
        if 0 <= idx < len(self.mOrder):
            start = self.mOrder[idx]
            if norm_it:
                start = start[0]
            return OrdDiapason(start)
        return None

    def getNavigation(self, obj):
        ret = [None] * 4
        ord_no = self.mOrdF(obj)
        idx = bisect_left(self.mOrder, ord_no)
        if ord_no > self.mOrder[0]:
            ret[0] = self.mObjects[0]
        if ord_no < self.mOrder[-1]:
            ret[3] = self.mObjects[-1]
        if idx > 1:
            ret[1] = self.mObjects[idx - 1]
        counts = [idx, 0, len(self.mObjects) - idx]
        if counts[2] > 0 and self.mObjects[idx] is obj:
            counts[1] = 1
            counts[2] -= 1
            if idx + 2 < len(self.mObjects):
                ret[2] = self.mObjects[idx + 1]
        elif idx + 1 < len(self.mObjects):
            ret[2] = self.mObjects[idx]
        ret.append(counts)
        return ret

    def filterObjects(self, test_f):
        return filter(test_f, self.mObjects)

    def find(self, find_key):
        idx = self.idxByKey(find_key)
        if idx < 0:
            return None
        return self.mObjects[idx], idx, self.diapByIdx(idx, True)
