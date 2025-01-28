from random import Random
from config.ver_cfg import Config
from .patch_cropper import PatchCropper
from .patch import PatchHandler

#=================================
class _PatchPool:
    def __init__(self, r_h):
        self.mRH = r_h
        self.mVariants = []
        self.mCount = 0

    def getCount(self):
        return self.mCount

    def addOne(self, patch_h):
        if self.mCount < Config.TRAIN_PACK_SIZE:
            self.mVariants.append(patch_h)
        else:
            idx = self.mRH.randint(0, self.mCount)
            if idx < Config.TRAIN_PACK_SIZE:
                self.mVariants[idx] = patch_h
        self.mCount += 1

    def getResult(self, size):
        assert size <= Config.TRAIN_PACK_SIZE
        self.mRH.shuffle(self.mVariants)
        return self.mVariants[:size]

#=================================
class TrainPatchPack:
    def __init__(self, env, img_h, width, height, markup_seq, seed = 179):
        self.mImgH = img_h
        self.mMarkupSeq = markup_seq
        self.mRH = Random(seed)
        self.mPools = [_PatchPool(self.mRH)]
        self.mCorrectRegion = PatchCropper.fullCorrectRegion(width, height)
        env.startProgress(Config.TRAIN_PACK_MAX_ITERATIONS)
        for _ in range(Config.TRAIN_PACK_MAX_ITERATIONS):
            self._makeOne()
            env.stepProgress()

        patches = []
        rest = Config.TRAIN_PACK_SIZE
        for idx in range(len(self.mPools) - 1, -1, -1):
            size = min(rest // (idx + 1), self.mPools[idx].getCount())
            patches += [p_h.getDescr().toJSon()
                for p_h in self.mPools[idx].getResult(size)]
            rest -= size
        env.endProgress()

        self.mResult = {
            "seed": seed,
            "total": len(patches),
            "complex_counts": [p_p.getCount() for p_p in self.mPools],
            "patches": patches
        }
        print("Pack:", self.mResult["total"], self.mResult["complex_counts"])

    def getResult(self):
        return self.mResult

    def _makeOne(self):
        x1, y1, x2, y2 = self.mCorrectRegion
        center = [
            self.mRH.randint(int(x1), int(x2)),
            self.mRH.randint(int(y1), int(y2))]
        angle = self.mRH.randint(0, 365)
        patch_h = PatchHandler(self.mImgH, center, angle)
        patch_h.setupMarkup(self.mMarkupSeq)
        repeat_count = int(
            patch_h.getComplexity() * Config.TRAIN_PACK_COMPLEX_MD)
        self._regOne(patch_h)
        angles = {angle}
        for _ in range(1, repeat_count):
            angle = self.mRH.randint(0, 365)
            if angle in angles:
                continue
            angles.add(angle)
            patch_h = PatchHandler(self.mImgH, center, angle)
            patch_h.setupMarkup(self.mMarkupSeq)
            repeat_count = int(
                patch_h.getComplexity() * Config.TRAIN_PACK_COMPLEX_MD)
            self._regOne(patch_h)

    def _regOne(self, patch_h):
        if patch_h.hasError():
            print("Error")
            return
        compl = patch_h.getComplexity()
        while len(self.mPools) < compl + 1:
            self.mPools.append(_PatchPool(self.mRH))
        self.mPools[compl].addOne(patch_h)
