import sys
from collections import namedtuple
import numpy as np

#=================================
class Detector16:
    MIN_TOTAL = 100
    MIN_EIG = 1
    MAX_PROP = .33
    MIN_CENTER_QUOTE = .25

    sRoundCornerDistr = [
        [0, 0, 0, 0, 0.19, 0.62,  0.85, 0.98],
        [0, 0, 0.034, 0.61, 0.97],
        [0, 0.034, 0.75],
        [0, 0.61],
        [0.19, 0.97],
        [0.62],
        [0.85],
        [0.98]]

    sRoundDistr = np.ones((16, 16), float)
    for i in range(8):
        for j, pr in enumerate(sRoundCornerDistr[i]):
            sRoundDistr[i, j] = pr
            sRoundDistr[15 - i, j] = pr
            sRoundDistr[i, 15 - j] = pr
            sRoundDistr[15 - i, 15 - j] = pr

    sDistrY = np.zeros((16, 16), float)
    for idx in range(16):
        sDistrY[idx] = idx - 8
    sDistrX = sDistrY.T

    sZeros = np.zeros((16, 16), float)

    @staticmethod
    def roundVal(val):
        return round(float(val), 2)

    @classmethod
    def roundVec(cls, vec):
        return list(map(cls.roundVal, vec))

    @classmethod
    def detect(cls, v16, low_level, debug_mode=False):
        mm = np.maximum( low_level - v16, cls.sZeros)

        mm_r = mm * cls.sRoundDistr
        mm_total = mm_r.sum()
        if debug_mode:
            print("Total:", mm_total, file=sys.stderr)
        if mm_total <= cls.MIN_TOTAL:
            if debug_mode:
                print(f"Rejected by MIN_TOTAL={cls.MIN_TOTAL}", file=sys.stderr)
            return None

        mm_r /= mm_total
        center_quote = mm_r[4:12, 4:12].sum()
        if debug_mode:
            print("Center quote:", center_quote, file=sys.stderr)
        if center_quote <= cls.MIN_CENTER_QUOTE:
            if debug_mode:
                print(f"Rejected by MIN_CENTER_QUOTE={cls.MIN_CENTER_QUOTE}", file=sys.stderr)
            return None

        x0 = (mm_r * cls.sDistrX).sum()
        y0 = (mm_r * cls.sDistrY).sum()

        dd_x = cls.sDistrX - x0
        dd_y = cls.sDistrY - y0
        a11 = np.sum(mm_r * (dd_x * dd_x))
        a12 = np.sum(mm_r * (dd_x * dd_y))
        a22 = np.sum(mm_r * (dd_y * dd_y))
        mm_inert = np.matrix([[a11, -a12], [-a12, a22]])
        mm_eig = np.linalg.eig(mm_inert)
        if debug_mode:
            print("Eigenvalues:", mm_eig.eigenvalues, file=sys.stderr)
        main_idx = 1 if mm_eig.eigenvalues[1] >= mm_eig.eigenvalues[0] else 0

        if mm_eig.eigenvalues[main_idx] <= cls.MIN_EIG:
            if debug_mode:
                print(f"Rejected by MIN_EIG={cls.MIN_EIG}", file=sys.stderr)
            return None

        prop_eig = (mm_eig.eigenvalues[1 - main_idx] /
            mm_eig.eigenvalues[main_idx])
        if  prop_eig >= cls.MAX_PROP:
            if debug_mode:
                print(f"Rejected by max_prop={cls.MAX_PROP} < {prop_eig}",
                    file=sys.stderr)
            return None

        dir_vec = np.array(mm_eig.eigenvectors[main_idx]).flatten()
        if dir_vec[1] < 0:
            dir_vec *= -1
        if debug_mode:
            print ("got prop_eig", prop_eig)
        return (cls.roundVec(dir_vec), [cls.roundVal(x0), cls.roundVal(y0)],
            cls.roundVal(mm_total), cls.roundVal(center_quote),
            cls.roundVal(prop_eig))

    StrokeDetectionPoint = namedtuple("StrokeDetection",
        ["yshift", "xdiap", "width", "ix", "pp", "direct", "prop_eig", "total_w", "center_q"])

    @classmethod
    def detectStrokeImage(cls, ximg, yshift):
        assert ximg.shape[0] == 32
        ximg = ximg[yshift:yshift + 16]
        seq = []
        for ix in range(8, ximg.shape[1] - 8):
            vv = ximg[:, ix-8:ix+8]
            det = cls.detect(vv, vv.mean() - 10, False)
            if det is not None:
                seq.append((ix, det))
        res = []
        j = -1
        while j + 1 < len(seq):
            j += 1
            start_ix, best_det = seq[j]
            best_ix = start_ix
            ix = start_ix
            while j + 1 < len(seq) and seq[j + 1][0] <= ix + 2:
                j += 1
                ix, det = seq[j]
                if det[-1] < best_det[-1]:
                    best_ix = ix
                    best_det = det
            direct, shift, total_w, center_q, prop_eig = best_det
            width = ix - start_ix + 1
            if width < 5 or total_w < 2000:
                continue
            res.append(cls.StrokeDetectionPoint(
                yshift = yshift,
                xdiap = [start_ix, ix],
                width = width,
                ix = best_ix,
                direct = direct,
                pp = [best_ix + shift[0], shift[1] + 8 + yshift],
                prop_eig = prop_eig,
                total_w = total_w,
                center_q = center_q))
        return res
