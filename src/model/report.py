import sys
import numpy as np
from io import StringIO

#=================================
PIXEL_SIZE = .231862

#=================================
def _strFloat(val, qual=1):
    return str(round(val, qual))

def _strPerc(val, total):
    vv = 100 * val / (total + .001)
    return _strFloat(vv)

#=================================
def _histo(seq, bounds):
    ret = []
    for idx in range(len(bounds) + 1):
        if idx == 0:
            crit = lambda val: val < bounds[0]
        elif idx == len(bounds):
            crit = lambda val: val >= bounds[-1]
        else:
            crit = lambda val: val >= bounds[idx-1] and val < bounds[idx]
        ret.append(sum(int(crit(val)) for val in seq))
    return ret

#=================================
class CaseReport:
    def __init__(self, case_data):
        self.mData = case_data
        self.mCommonMetrics = []
        self.mTables = []
        self.mTitle = self._formTitle()
        self.evalDiameters()
        self.evalBranchness()

    def get(self, key, default = None):
        return self.mData.get(key, default)

    def getTitle(self):
        return self.mTitle

    def getMetrics(self):
        return self.mCommonMetrics

    def getTables(self):
        return self.mTables

    def getName(self):
        return self.get('dir')

    def getVCount(self):
        return sum(len(rep["diameters"])
            for rep in self.get('rep'))

    def getImgCount(self):
        return len(self.get('rep'))

    def _formTitle(self):
        name = self.getName()
        cnt_img = self.getImgCount()
        return f"Для {name}:\t {cnt_img} изображений"

    def _regCommonMetric(self, title, value):
        self.mCommonMetrics.append([title, value])

    def _regTable(self, title, rows):
        self.mTables.append([title, rows] )

    #=================================
    def evalDiameters(self):
        global PIXEL_SIZE
        diameters = []
        for rep in self.get('rep'):
            diameters += rep["diameters"]
        diameters = np.array(diameters) * PIXEL_SIZE
        d_histo = _histo(diameters, [20, 40, 60, 80])
        self._regCommonMetric("Общее число везикул", str(len(diameters)))
        self._regCommonMetric("Доля малых везикул (до 40 nm, в %)",
            _strPerc(d_histo[0] + d_histo[1], sum(d_histo)) )
        self._regCommonMetric("Усреднённый диаметр(в nm)",
            _strFloat(diameters.mean(), 1))
        self._regTable("Диаметр везикул", [
            ["", "до 20 nm", "от 20 до 40",
                "от 40 до 59", "от 60 до 79", "от 80 nm"],
            ["Число"] + [str(val) for val in d_histo],
            ["Квоты (в %)"] + [_strPerc(val, sum(d_histo)) for val in d_histo]])

    #=================================
    def evalBranchness(self):
        nodes = []
        t_br = 0
        for rep in self.get("rep"):
            nodes += rep["nodes"]
            t_br += rep["total-br"]
        n_real_nodes = sum(int(val > 1) for val in nodes)
        nodes = np.array(nodes)
        d_histo = _histo(nodes, [2, 3, 4, 6])
        self._regCommonMetric("Среднее число везикул в гнезде", _strFloat(nodes.mean()))
        self._regCommonMetric("Доля одиночных гнёзд(в %)",
            _strPerc(len(nodes) - n_real_nodes, len(nodes)))
        self._regCommonMetric("Ветвистость", _strPerc(t_br, n_real_nodes))
        self._regTable("Вложенность везикул",  [
            ["", "1", "2", "3", "4 и 5", "от 6 и выше"],
            ["Число"] + [str(val) for val in d_histo],
            ["Квоты (в %)"] + [_strPerc(val, sum(d_histo)) for val in d_histo]])


    #=================================
    def reportDetailed(self, detailed_outp):
        print("<hr/>", file=detailed_outp)
        print(f"<h2>Детализация по образцу {self.getName()}</h2>",
            file=detailed_outp)
        for idx, rep in enumerate(self.get('rep')):
            self._reportOneDetailed(idx+1, rep, detailed_outp)

    #=================================
    def _reportOneDetailed(self, no, rep, detailed_outp):
        img_name = rep["img"]
        print(f"<h3>По изображению no={no}: {img_name}</h3>",
            file=detailed_outp)
        diameters = rep["diameters"]
        print(f"<p>Диаметры [{len(diameters)}]:</p>", file=detailed_outp)
        print("<table><tr><td>",
            "</td><td>".join(str(val) for val in diameters),
            "</td></tr></table>",
            file=detailed_outp)
        n_singles = rep["singles"]
        print(f"<p>Одиночные везикулы:\t{n_singles}</p>",
            file=detailed_outp)
        sacs = rep["sacs"]
        if len(sacs) > 0:
            print(f"<p>Везикулы с вложениями [{len(sacs)}]:</p>",
                file=detailed_outp)
            print("<table>", file=detailed_outp)
            print("<tr><td>число</td><td>ветвистость</td>",
                "<td>Структура</td></tr>", file=detailed_outp)
            for node_count, node_br, node_struct in sacs:
                print(f"<tr><td>{node_count}</td><td>{node_br}</td>" +
                    f"<td>{node_struct}</td></tr>",
                    file=detailed_outp)
            print("</table>", file=detailed_outp)
        print(file=detailed_outp)

#=================================
def plainStatReport(stat_rep, outp=None):
    if outp is None:
        outp = sys.stdout
    print(stat_rep.getTitle(),  file=outp)
    for nm,  val in stat_rep.getMetrics():
        print("\t" + nm + ":", "\t" + val,  file=outp)
    print(file=outp)

    for table_info in stat_rep.getTables():
        title, rows = table_info
        n_col = None
        print("\t", title,  file=outp)
        for line_cells in rows:
            if n_col is None:
                n_col = len(line_cells)
            else:
                assert len(line_cells) == n_col
            print("\t" + "\t".join(line_cells),  file=outp)
        print(file=outp)

#=================================
def htmlStatReport(stat_rep, outp):
    print("<hr/>", file= outp)
    print("<h2>", stat_rep.getTitle(), "</h2>", file=outp)
    print("<table border='1'>", file=outp)
    for nm, val in stat_rep.getMetrics():
        print("<tr><td>", nm, "</td><td>", val, "</td></tr>", file=outp)
    print("</table>\n", file=outp)

    print("<table><tr>", file=outp)
    for table_info in stat_rep.getTables():
        title, rows = table_info
        print('<td><h3>', title, '</h3>', file=outp)
        print('<table border="1">', file=outp)
        n_col = None
        for line_cells in rows:
            if n_col is None:
                n_col = len(line_cells)
            else:
                assert len(line_cells) == n_col,  f"{len(line_cells)}, {n_col}"
            print("<tr><td>" + "</td><td>".join(line_cells) + "</td></tr>", file=outp)
        print('</table></td><td width="20px"></td>\n', file=outp)
    print("</tr></table>", file=outp)

#=================================
def plainFullReport(all_data, outp=None):
    if outp is None:
        outp = sys.stdout
    for case_data in all_data:
        stat_rep = CaseReport(case_data)
        plainStatReport(stat_rep, outp)

#=================================
def htmlFullReport(all_data,  fname, detailed=False):
    detailed_outp = StringIO() if detailed else None
    with open(fname, "w", encoding="utf-8") as outp:
        print('''
<!DOCTYPE html>
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <title>Отчёт по измерению везикул</title>
  </head>
  <body>''', file=outp)
        total_metrics = None
        all_names = []
        for case_data in all_data:
            stat_rep = CaseReport(case_data)
            htmlStatReport(stat_rep, outp)
            if detailed_outp is not None:
                stat_rep.reportDetailed(detailed_outp)
            all_names.append(stat_rep.getName())
            if total_metrics is None:
                total_metrics = [[key, [val]]
                    for key,  val in stat_rep.getMetrics()]
            else:
                for idx, m_info in enumerate(stat_rep.getMetrics()):
                    key,  val = m_info
                    assert key == total_metrics[idx][0]
                    total_metrics[idx][1].append(val)

        print("<hr/>", file= outp)
        print('<h2>', "Сводная таблица", '</h2>', file=outp)
        print('<table border="1">', file=outp)
        print('<tr><td></td><td>', '</td><td>'.join(all_names),
            '</td></tr>', file=outp)
        for m_title,  values in total_metrics:
            print('<tr><td>', m_title, '</td><td>',
                '</td><td>'.join(values), '</td></tr>', file=outp)
        print('</table>', file=outp)
        if detailed_outp is not None:
            outp.write(detailed_outp.getvalue())
        print('''
    </body>
</html>''', file=outp)
#=================================
