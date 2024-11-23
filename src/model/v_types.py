from config.messenger import msg
#=================================
class VTypeInfo:
    def __init__(self, type, geom_type,
            dim_kind = "curve", closed = False):
        self.mType = type
        self.mName = msg("markup.path.type." + self.mType)
        assert geom_type in ("spline", "line", "poly")
        assert dim_kind in ("curve", "area")
        self.mGeomType = geom_type
        self.mDimKind = dim_kind
        self.mClosed = closed or self.mDimKind == "area"

    def getType(self):
        return self.mType

    def getName(self):
        return self.mName

    def getGeomType(self):
        return self.mGeomType

    def isAreaType(self):
        return self.mDimKind == "area"

    def isClosed(self):
        return self.mClosed

#=================================
class VType:
    sDescriptors = [
        VTypeInfo("vesicula", "spline", closed = True),
        VTypeInfo("v-seg", "spline"),
        VTypeInfo("barrier", "spline"),
        VTypeInfo("blot", "spline", "area"),
        VTypeInfo("dirt", "poly", "area")]

    sTypeList = [tp.getType() for tp in sDescriptors]

    sTypeMap = {tp.getType(): tp for tp in sDescriptors}

    @classmethod
    def getList(cls):
        return iter(cls.sTypeList)

    @classmethod
    def getTypeDescr(cls, vtype):
        return cls.sTypeMap[vtype]

    @classmethod
    def iterTypes(cls):
        return [cls.sTypeMap[tp] for tp in cls.sTypeList]
