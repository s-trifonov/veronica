import sys, os
from io import StringIO

from lxml import etree

from config.messenger import msg
#===================================================
class _H:
    sXMLParser  = etree.XMLParser(remove_comments = True)
    sHTMLParser = etree.HTMLParser(remove_comments = True)
    sHTMLHeavyParser = etree.HTMLParser(
        recover = False, remove_comments = True)
    sXMLHeavyParser = etree.XMLParser(
        recover = False, remove_comments = True)
    sXMLErrTranslator = None

#====XML===
def simpleLoadXML(fname):
    with open(fname, "rb") as inp:
        return etree.parse(inp, _H.sXMLParser)

def parseXMLFile(fname, with_errors = False):
    if not os.path.exists(fname):
        print("RUNTIME EXC:", str(msg("file.open", fname)), file=sys.stderr)
        raise RuntimeError()

    inp = open(fname, "rb")
    etree.clear_error_log()
    error_log, e_log = None, None
    try:
        doc = etree.parse(inp, _H.sXMLParser)
    except etree.XMLSyntaxError as e:
        doc = None
        e_log = e.error_log.filter_from_level(etree.ErrorLevels.FATAL)

    if e_log is not None:
        print("XML PARSE Errors for", fname, file=sys.stderr)
        if _H.sXMLErrTranslator is not None:
            error_log = _H.sXMLErrTranslator(e_log)
            for err_line in error_log:
                sys.stderr.write(err_line)
            print("===", file=sys.stderr)
        else:
            for err_line in e_log:
                sys.stderr.write(err_line)
            print("===", file=sys.stderr)
    inp.close()
    if not with_errors:
        if doc is None:
            print("RUNTIME EXC:", str(msg("file.xml.parse", fname)),
                file=sys.stderr)
            raise RuntimeError()
        return doc
    return doc, error_log

#====HTML===
def parseHTMLFile(fname):
    if not os.path.exists(fname):
        print("RUNTIME EXC:", str(msg("file.open", fname)), file=sys.stderr)
        raise RuntimeError()
    with open(fname, mode="rb", buffering=0) as inp:
        return etree.parse(inp, _H.sHTMLParser)

def parseHTMLText(text, heavy_mode = False):
    return etree.parse(StringIO(text),
        _H.sHTMLHeavyParser if heavy_mode else _H.sHTMLParser)

def parseXMLText(text):
    return etree.parse(StringIO(text), _H.sXMLHeavyParser)

def parseXMLBytes(text):
    return etree.fromstring(text, _H.sXMLHeavyParser)

def isNode(nd):
    return not(isinstance(nd, etree._Comment)
        or isinstance(nd, etree._ProcessingInstruction)
        or isinstance(nd, etree._Entity))

#==============================
def emptyText(text):
    return not text or text.isspace()

#==============================
def nodeNoAttrs(node):
    for _,  _ in node.attrib.items():
        return False
    return True

def nodeIsPure(node):
    return len(node) == 0 and emptyText(node.text)

def nodeIsJustContainer(node):
    if not (emptyText(node.text) or emptyText(node.tail)):
        return False
    for nd in node.iterchildren():
        if not emptyText(nd.tail):
            return False
    return True

#================================
def getFirstNodeChild(nd0, tag_name):
    lst = nd0.getElementsByTagName(tag_name)
    if lst.length:
        return lst.item(0)
    return None

#================================
def getDocBody(doc):
    html_nd = getFirstNodeChild(doc, "html")
    if html_nd:
        return getFirstNodeChild(html_nd, "body")
    return getFirstNodeChild(doc, "body")

#=========Tools to retrieve info from XML===========
def getElText(prj_tree, path, is_opt = True):
    try:
        seq = prj_tree.xpath(path)
        if is_opt and (not seq or len(seq) == 0 or not seq[0].text):
            return ""
        assert len(seq) == 1 and len(seq[0]) == 0
        return seq[0].text.strip()
    except Exception:
        print("RUNTIME EXC:", str(msg("prj.el-text", path)), file=sys.stderr)
        raise RuntimeError()

def getSingleSubNode(nd, path):
    seq = nd.xpath(path)
    if len(seq) == 1:
        return seq[0]
    #assert False
    return None

#==============================
