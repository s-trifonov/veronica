import cProfile, pstats
from io import StringIO

class MyProfiler:
    sProfile = None
    sNote = None

    @classmethod
    def start(cls, note = ""):
        if cls.sProfile is None:
            cls.sProfile = cProfile.Profile()
            cls.sNote = note if note else ""
            cls.sProfile.enable()

    @classmethod
    def end(cls, no_repeate = True):
        if not cls.sProfile:
            return
        cls.sProfile.disable()
        s = StringIO()
        ps = pstats.Stats(cls.sProfile, stream = s)
        ps.sort_stats("cumulative").print_stats()
        print("Profile dump: %s" % cls.sNote)
        print(s.getvalue())
        cls.sProfile = False if no_repeate else None
        cls.sNote = None
