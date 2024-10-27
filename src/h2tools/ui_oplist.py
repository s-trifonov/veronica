#=========================================
class UI_OpList:
    def __init__(self, names):
        self.mNames = names

    def relocate(self, cur_name, act, with_names):
        if with_names:
            nm = self.selectName(cur_name, act,
                with_names if with_names is not True else '')
            if nm is not None:
                return nm
        if cur_name in self.mNames:
            idx = self.mNames.index(cur_name)
        else:
            idx = None
        if act.isAction("set"):
            pass
        if act.isAction("check"):
            pass
        elif act.isAction("dec"):
            if idx < 1 or idx is None:
                idx = None
            else:
                idx -= 1
        elif act.isAction("inc"):
            if idx is None or idx + 1 >= len(self.mNames):
                idx = None
            else:
                idx += 1
        elif act.isAction("switch"):
            if len(self.mNames) < 2:
                idx = None
            elif idx is not None:
                idx += 1
                if idx >= len(self.mNames):
                    idx = 0
        elif act.isAction("rswitch"):
            if len(self.mNames) < 2:
                idx = None
            elif idx is not None:
                idx -= 1
                if idx < 0:
                    idx = len(self.mNames) - 1
        else:
            return None
        if idx is None:
            act.failed()
            return None
        act.done()
        return self.mNames[idx]

    def selectName(self, cur_name, act, with_names = ''):
        op_name = with_names + act.getOpName()
        for name in self.mNames:
            if name.endswith(op_name):
                if name != cur_name:
                    act.done()
                    return name
                act.failed()
                return False
        return None

    def sibbling(self, idx, delta):
        if idx is not None:
            if delta > 0:
                idx += 1
            else:
                idx -= 1
            if 0 <= idx < len(self.mNames):
                return self.mNames[idx]
        return None
