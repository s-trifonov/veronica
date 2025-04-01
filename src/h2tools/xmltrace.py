import sys
from .xmlutils import isNode
#===================================
class TracedXMLNode:
    def __init__(self, node, filename = None, parent = None):
        self.tag = node.tag
        self.text = node.text
        self.tail = node.tail
        self.attrib = node.attrib
        self.sourceline = node.sourceline
        self.mParent = parent
        self.mFileName = filename
        self.mNode  = node
        self.mAttrs = {a: v for a, v in node.attrib.items()}
        self.mUnusedAttrs = set(self.mAttrs.keys())
        for a in ():
            if a in self.mUnusedAttrs:
                self.mUnusedAttrs.remove(a)
        self.mChildren = []
        for nd in node.iterchildren():
            if isNode(nd):
                self.mChildren.append(TracedXMLNode(nd, parent=self))
        self.mUntouchChildren = (len(self.mChildren) > 0)

    def __len__(self):
        return len(self.mChildren)

    def get(self, attr, value=None):
        if attr in self.mUnusedAttrs:
            self.mUnusedAttrs.remove(attr)
        return self.mAttrs.get(attr, value)

    def iterchildren(self):
        self.mUntouchChildren = False
        for nd in self.mChildren:
            yield nd

    def _getTagPath(self):
        if self.mParent is not None:
            return self.mParent._getTagPath() + "/" + self.tag
        return self.tag

    def _getFileName(self):
        if self.mParent is not None:
            return self.mParent._getFileName()
        return self.mFileName

    def deactivate(self):
        self.mUnusedAttrs     = set()
        self.mUntouchChildren = False
        self.mChildren        = []

    def reportProblems(self):
        if len(self.mUnusedAttrs) > 0 or self.mUntouchChildren:
            print("Tag %s\t line=%s file=%s" % (self._getTagPath(),
                self.sourceline, self._getFileName()), file = sys.stderr)
            if len(self.mUnusedAttrs) > 0:
                print("\t", "unused attributes:",
                    self.mUnusedAttrs, file = sys.stderr)
            if self.mUntouchChildren:
                print("\t", "lost children!", file = sys.stderr)
        if len(self.mChildren) and not self.mUntouchChildren:
            for ch in self.mChildren:
                ch.reportProblems()
