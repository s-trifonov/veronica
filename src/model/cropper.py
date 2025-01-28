import math
from PIL import Image
import numpy as np

import tools.geom as geom
#=================================
class Cropper:
    def __init__(self, p_glob, angle, bounds, p_loc=None):
        self.mAngle = angle
        self.mBounds = bounds

        if self.mAngle == 0:
            cc, ss = 1, 0
        else:
            aa = angle * math.pi / 180
            cc, ss = math.cos(aa), math.sin(aa)

        self.mToLocal = [[cc, ss, 0], [-ss, cc, 0]]
        self.mToGlobal = [[cc, -ss, 0], [ss, cc, 0]]
        if p_loc is None:
            p_loc = [0, 0]
        self.__adjustTransform(p_loc, p_glob, self.mToGlobal)
        self.__adjustTransform(p_glob, p_loc, self.mToLocal)

    @classmethod
    def __adjustTransform(cls, p_from, p_to, mm):
        pp = geom.mapPoint(mm, p_from)
        mm[0][2] += p_to[0] - pp[0]
        mm[1][2] += p_to[1] - pp[1]

    def getAngle(self):
        return self.mAngle

    def getBounds(self):
        return self.mBounds

    def getPoly(self, closed=True):
        width, height = self.mBounds
        points = self.mapPointsToGlobal([
            [0, 0], [width, 0], [width, height], [0, height]])
        if closed:
            points.append(points[0])
        return points

    def mapToLocal(self, pp):
        return geom.mapPoint(self.mToLocal, pp)

    def mapPointsToLocal(self, points):
        return [geom.mapPoint(self.mToLocal, pp)
            for pp in points]

    def mapToGlobal(self, pp):
        return geom.mapPoint(self.mToGlobal, pp)

    def mapPointsToGlobal(self, points):
        return [geom.mapPoint(self.mToGlobal, pp)
            for pp in points]

    def doCrop(self, fullImage):
        p_poly = self.getPoly(False)
        x1 = min(pp[0] for pp in p_poly)
        x2 = max(pp[0] for pp in p_poly)
        y1 = min(pp[1] for pp in p_poly)
        y2 = max(pp[1] for pp in p_poly)
        if self.mAngle == 0:
            return fullImage.crop([x1, y1, x2, y2])
        local_image = fullImage.crop([
            x1 - 1, y1 - 1, x2 + 1 , y2 + 1])
        width, height = self.getBounds()
        rotated_image = local_image.rotate(self.mAngle,
            resample=Image.Resampling.BILINEAR, expand=True)
        rx = round((rotated_image.width - width)/2)
        ry = round((rotated_image.height - height)/2)
        return rotated_image.crop([rx, ry, rx + width, ry + height])

    def makeArray(self, fullImage):
        image = self.doCrop(fullImage)
        img_array = np.asarray(image, float)
        h, w = self.getBounds()
        cropped_shape = (w, h)
        if len(img_array.shape) != 2:
            assert len(img_array.shape) == 3
            img_array = np.average(img_array, 2)
        assert img_array.shape == cropped_shape
        return img_array
