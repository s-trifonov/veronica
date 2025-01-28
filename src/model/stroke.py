import math

from config.ver_cfg import Config
import tools.geom as geom
from .cropper import Cropper
from deep.detect16 import Detector16

#=================================
DSTEP = Config.STROKE_WIDTH // 2
def detectStrokeCrossings(image, pp1, pp2):
    global DSTEP
    if not (
            DSTEP <= pp1[0] < image.width - DSTEP and
            DSTEP <= pp1[1] < image.height - DSTEP and
            DSTEP <= pp2[0] < image.width - DSTEP and
            DSTEP <= pp2[1] < image.height - DSTEP):
        return None
    if pp1[0] > pp2[0] or (pp1[0]==pp2[0] and pp1[1] > pp2[1]):
        pp1, pp2 = pp2, pp1

    dd = geom.delta(pp1, pp2)
    dd_len = geom.length(*geom.delta(pp1, pp2))
    assert dd[0] >= 0

    if dd_len < 2 * Config.STROKE_WIDTH:
        return None
    angle = math.asin(dd[1] / dd_len) * 180 / math.pi
    dd_len = int(dd_len)

    cropper = Cropper(pp1, angle,
        (dd_len, 2 * Config.STROKE_WIDTH), [0, 2 * DSTEP])
    img_array = cropper.makeArray(image)
    res = []
    for attempt in (0, 1):
        detection = Detector16.detectStrokeImage(img_array, 16 * attempt)
        for det_point in detection:
            x_l, y_l = det_point.pp
            dx, dy = (DSTEP * dz for dz in det_point.direct)
            pp = cropper.mapToGlobal((x_l, y_l))
            pp1 = cropper.mapToGlobal((x_l - dx, y_l - dy))
            pp2 = cropper.mapToGlobal((x_l + dx, y_l + dy))
            res.append((pp, pp1, pp2, det_point))
    return res
