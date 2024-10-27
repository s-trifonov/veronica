#import sys

class DefaultStyleCfg:
    SPACING             = 2
    TABLE_ROW_HEIGTH    = 20
    LAYOUT_MARGINS      = [2, 1, 2, 1]
    WIDGET_MARGINS      = [0, 0, 0, 0]


COMMON_STYLE_SHEET = '''

*[sclass="bg_white_y"],  *[sclass="bg_white_y"] > *{
    background-color: rgb(255, 255, 240);
    font-size:12px;
}

*[sclass="bg_white_b"],  *[sclass="bg_white_b"] > *{
    background-color: rgb(248, 248, 255);
}

*[sclass="bg_white_g"],  *[sclass="bg_white_g"] > *{
    background-color: rgb(248, 255, 248);
}

*[sclass="report_title"] {
    background-color: rgb(240, 240, 240);
    margin:0; padding:0;border:0;
}

*[sclass="no_margins"] {
    margin:0; padding:0;border-width:0;
}

*[sclass="err_level_0"] {
    background-color: rgb(221, 255, 221);
    margin:0; padding:0;border:0;
}

*[sclass="err_level_10"] {
    background-color: rgb(255, 255, 102);
    margin:0; padding:0;border:0;
}

*[sclass="err_level_50"] {
    background-color: rgb(255, 204, 51);
    margin:0; padding:0;border:0;
}

*[sclass="err_level_500"] {
    background-color: rgb(255, 0, 0);
    margin:0; padding:0;
    margin:0; padding:0;border:0;
}

*[sclass="box"] {
    border-style: solid;
    border-width: 1;
    border-color: grey;
}

*[sclass="active_box"] {
    color: red;
    font-weight: bold;
}

*[sclass="active_hint"] {
    color: red;
    font-style: italic;
}

*[sclass="hint"] {
    color: grey;
    font-style: italic;
}

*[sclass="wrong_value"] {
    background: rgb(255, 230, 230);
    color: red;
}

QTableView {
    background-color:rgb(255, 255, 255);
    alternate-background-color:rgb(248, 248, 248);
}

QMenuBar {
    max-height: 30px;
}

QStatusBar{
    max-height: 30px;
}

QStatusBar[sclass="hint"]{
    background-color:rgb(255, 255, 180);
}

QCheckBox[sclass="modified"] {
    color: red;
}

QCheckBox[sclass="bold"] {
    font-weight: bold;
}

QPushButton[sclass="compact"] {
    padding: 4px;
}

QPushButton:checked {
    color: red;
    font-weight: bold;
    background-color: rgb(248, 248, 230);
}

QToolButton[sclass="btn-repos"]{
    font-family: Times;
    font-weight: bold;
    font-size: 14px;
}

QLineEdit {
    font-family: Arial;
    font-size: 12pt;
    margin:0; padding:0; border-width:0;
}

QLabel[sclass="title"] {
    font-size: 16px;
    font-weight: bold;
    max-height: 20px;
    margin:0; padding:0;border:0;
}

QLabel[sclass="report"] {
    margin-left: 20px;
    font-weight: bold;
    font-size: 16px;
}

QLabel[sclass="rep-err"] {
    color: red;
    margin-left: 20px;
    font-weight: bold;
    font-size: 16px;
}

*[sclass="small-comment"] {
    color: grey;
    font-style: italic;
    font-size: 11px;
}

*[sclass="red"] {
    color: red;
}

*[sclass="orange"] {
    color: orange;
}

*[sclass="active"] {
    color: brown;
}

*[sclass="font14"] {
    font-size: 14px;
}

*[sclass="font16"] {
    font-size: 16px;
}

*[sclass="font25"] {
    font-size: 25px;
}

*[sclass="font21"] {
    font-size: 21px;
}

'''
