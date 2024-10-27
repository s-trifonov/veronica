from markup.xmlutils import parseXMLFile

#=========================================
class XmlConfig:
    def __init__(self, filename):
        self.mProperties = dict()
        doc = parseXMLFile(filename)
        for nd in doc.xpath("/h2-pub-config/prop"):
            self.mProperties[nd.get("name")] = nd.text

    def get(self, name, default = None, strip_it = False,
            split_it = False, as_int = False, ext_mode = None):
        ret = None
        if ext_mode is not None:
            ext_name = name + "." + ext_mode
            if ext_name in self.mProperties:
                ret = self.mProperties[ext_name]
        if ret is None:
            ret = self.mProperties.get(name, default)
        if ret and as_int:
            return int(ret.strip())
        if ret and strip_it:
            ret = ret.strip()
        if split_it:
            return ret.split()
        return ret
