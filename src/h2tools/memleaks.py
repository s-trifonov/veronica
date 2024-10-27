import sys, gc, psutil, tracemalloc

#===========================
def reportMemoryState(title, outp = sys.stderr):
    gc.collect()
    if outp is None:
        return
    cnt, int_total = 0, 0
    for obj in gc.get_objects():
        cnt += 1
        int_total += sys.getsizeof(obj)
    ps_total = psutil.Process().memory_info().rss
    frag = 1. - (int_total/(ps_total + 1.))

    print(title, "mem state:", gc.get_count(), "/", cnt, "\n",
        "ps_total:", ps_total, "obj_total:", int_total,
        "garbage:", len(gc.garbage),
        "fragmentation = %0.1f%s" % (100 * frag, '%'),
        file = outp)
    MyTraces.step(outp)

#===========================
#import memory_profiler as mp
#def repMemory(title):
#    gc.collect
#    print("Mem usage:", title, mp.memory_usage(max_usage=True),
#        file = sys.stderr)

#===========================
class MyTraces:
    sPrevIdSet = None

    @classmethod
    def step(cls, outp = None):
        if cls.sPrevIdSet is None:
            cls.start()
        else:
            cls.next(outp)

    @classmethod
    def stop(cls):
        if cls.sPrevIdSet:
            del cls.sPrevIdSet
            cls.sPrevIdSet = None
            tracemalloc.stop()

    @classmethod
    def start(cls, id_set = None):
        if cls.sPrevIdSet is not None:
            return
        gc.collect()
        if id_set is None:
            id_set = set()
            for obj in gc.get_objects():
                id_set.add(id(obj))
        cls.sPrevIdSet = id_set
        tracemalloc.start()

    @classmethod
    def next(cls, outp = sys.stderr):
        assert cls.sPrevIdSet is not None
        gc.collect()
        counts = [0, 0, 0]
        sizes = [0, 0, 0]
        curIdSet = set()
        rest_stat = dict()
        if outp is not None:
            print("Id set:", len(cls.sPrevIdSet))
        for obj in gc.get_objects():
            curIdSet.add(id(obj))
            obj_size = sys.getsizeof(obj)
            counts[0] += 1
            sizes[0] += obj_size
            if id(obj) in cls.sPrevIdSet:
                continue
            counts[1] += 1
            sizes[1] += obj_size
            obj_tb = tracemalloc.get_object_traceback(obj)
            if obj_tb is None:
                continue
            counts[2] += 1
            sizes[2] += obj_size
            obj_frame = obj_tb[0].filename + ":" + str(obj_tb[0].lineno)
            frame_stat = rest_stat.get(obj_frame)
            if frame_stat is None:
                frame_stat = [0, 0]
                rest_stat[obj_frame] = frame_stat
            frame_stat[0] += 1
            frame_stat[1] += obj_size
        cls.stop()
        cls.start(curIdSet)

        if (outp is not None):
            print("==Rest stat===(%d cnt=%s sz=%s)" %
                (len(rest_stat), str(counts), str(sizes)), file = outp)
            for obj_frame in sorted(rest_stat.keys()):
                cnt, sz = rest_stat[obj_frame]
                print(f"{obj_frame}\t{cnt}\t{sz}", file = outp)
            print("===", file = outp)

