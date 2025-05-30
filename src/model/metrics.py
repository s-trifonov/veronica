from io import StringIO
from collections import Counter
from tools import geom
from .markup_path import MarkupPathCtrl

#=================================
def evalMetrics(seq_info, report_mode=False):
    if report_mode:
        rep = StringIO()
    else:
        rep_descr = dict()

    v_path_seq = []
    vf_path_seq = []
    for type, points in seq_info:
        if type == "vesicula":
            v_path_seq.append(
                MarkupPathCtrl(type, points).drawPoly())
            if v_path_seq[-1][0] != v_path_seq[-1][-1]:
                v_path_seq[-1].append(v_path_seq[-1][0])
        elif type == "v-seg":
            vf_path_seq.append(
                MarkupPathCtrl(type, points).drawPoly())

    if report_mode:
        print("Counts:", len(v_path_seq), len(vf_path_seq), file=rep)
    else:
        rep_descr["count-v"] = len(v_path_seq)
        rep_descr["count-frag"] = len(vf_path_seq)

    diameters = [int(geom.polyDiameter(points))
        for points in v_path_seq]
    centers = [geom.polyCenter(points)
        for points in v_path_seq]

    diameters.sort()
    if report_mode:
        print("Diameters:", diameters, file=rep)
    else:
        rep_descr["diameters"] = diameters

    hier = []
    for idx0 in range(len(v_path_seq)):
        for idx1 in range(idx0 + 1, len(v_path_seq)):
            q_h = _curveHier(centers[idx0], v_path_seq[idx0],
                centers[idx1], v_path_seq[idx1])
            if q_h == 1:
                hier.append([idx0, idx1])
            elif q_h == -1:
                hier.append([idx1, idx0])

    print("Hier=", hier)
    nodes_len = []
    total_br = 0
    int_idxs = set(range(len(v_path_seq)))
    while len(hier) > 0:
        node_br, node_idxs = _selectNode(hier)
        int_idxs -= node_idxs
        if report_mode:
            print("Node:", len(node_idxs), node_br, sorted(node_idxs), file=rep)
        nodes_len.append(len(node_idxs))
        total_br += node_br
    for sep_idx in sorted(int_idxs):
        nodes_len.append(1)
        if report_mode:
            print("Single:", sep_idx, file=rep)
    nodes_len.sort()
    if report_mode:
        print("Nodes count:", len(nodes_len), nodes_len, file=rep)
        print("Nodes branching:", total_br, file=rep)
    else:
        rep_descr["nodes"] = nodes_len
        rep_descr["total-br"] = total_br

    if report_mode:
        return rep.getvalue()
    return rep_descr

#=================================
def _curveHier(cc0, points0, cc1, points1):
    diap0 = _crossPoly(points0, cc0, cc1)
    diap1 = _crossPoly(points1, cc0, cc1)
    if not diap0 or not diap1:
        return None
    diap0.sort()
    diap1.sort()
    if max(diap0[0], diap1[0]) < min(diap0[1], diap1[1]):
        if diap0[0] <= diap1[0]:
            return 1 if diap1[1] <= diap0[1] else 0
        else:
            return -1 if diap0[1] <= diap1[1] else 0
    return 0

#=================================
def _crossPoly(points, c0, c1):
    dir_along = geom.delta(c0, c1)
    dl = geom.length(*dir_along)
    if dl < 2:
        dir_along = [1, 0]
    else:
        dir_along = [zz/dl for zz in dir_along]
    dir = [dir_along[1], -dir_along[0]]
    cr_base = geom.smult(c0, dir)
    res = []
    cr0 = geom.smult(points[0], dir) - cr_base
    if abs(cr0) < 1:
        cr_base -= 2
        cr0 -= 2

    for idx in range(1, len(points)):
        cr = geom.smult(points[idx], dir) - cr_base
        if (cr > 0 and cr0 < 0) or (cr < 0 and cr0 > 0):
            dcr = cr - cr0
            if abs(dcr) < 1:
                res.append(geom.smult(points[idx], dir_along))
            else:
                zz0 = geom.smult(points[idx-1], dir_along)
                zz1 = geom.smult(points[idx], dir_along)
                coeff = abs(cr0 / dcr)
                res.append( coeff * zz0 + (1 - coeff) * zz1)
        cr0 = cr
    if len(res) > 2 and abs(res[0] - res[-1]) < 1:
        del res[-1]
    if len(res) == 2:
        return res
    return None

#=================================
def _selectNode(hier):
    if len(hier) == 0:
        return None
    counter = Counter()
    for idx_out, idx_in in hier:
        counter[idx_out] += 1
    _, idx_node = max((cnt, idx) for idx, cnt in counter.items())
    node_idxs = {idx_node}
    node_int_idxs = set()
    cnt0 = 0
    while len(node_idxs) != cnt0:
        cnt0 = len(node_idxs)
        for idx_out, idx_in in hier:
            if idx_out in node_idxs:
                node_idxs.add(idx_in)
                node_int_idxs.add(idx_in)
    node_hier = []
    for idx in range(len(hier) - 1, -1, -1):
        idx_out, idx_in = hier[idx]
        if idx_out not in node_idxs:
            continue
        if idx_out != idx_node:
            node_hier.append(hier[idx])
        del hier[idx]

    cnt, br_sum = 0, 0
    while len(node_hier) > 0:
        sub_hier_br, sub_hier_set = _selectNode(node_hier)
        cnt += 1
        br_sum += sub_hier_br
        node_int_idxs -= sub_hier_set
    cnt += len(node_int_idxs)
    node_branching = max(0, cnt - 1) + br_sum
    return node_branching, node_idxs
