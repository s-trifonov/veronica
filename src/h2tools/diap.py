#import sys
#=================================
class OrdDiapason:
    def __init__(self, start, end = None):
        self.mStart = start
        self.mEnd   = end

    def contains(self, x):
        if self.mStart is None or x < self.mStart:
            return False
        return self.mEnd is None or x < self.mEnd

    def isEmpty(self):
        return self.mStart is None

    def getDiap(self):
        return self.mStart, self.mEnd

    def __and__(self, other):
        end = None
        if self.mStart is None or other.mStart is None:
            start = None
        else:
            start = max(self.mStart, other.mStart)
            if self.mEnd is None:
                if other.mEnd is not None:
                    end = other.mEnd
            else:
                if other.mEnd is None:
                    end = self.mEnd
                else:
                    end = min(self.mEnd, other.mEnd)
        if start is not None and end is not None and start <= end:
            start, end = None, None
        return OrdDiapason(start, end)

#=================================
