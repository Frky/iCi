#-*- coding: utf-8 -*-

from src.py.log import Log

class Function(object):
    def __init__(self, iname, offset, name, calls):
        self.__iname = iname
        self.__offset = int(offset)
        self.__name = name
        self.__calls = int(calls)
        self.__ins = list()

    def add_ins(self, ins):
        self.__ins.append(ins)

    def print_ins(self, ref, prefix="", ignore_ld=False):
        uniq = 0
        for ins in self.__ins:
            if "ld-linux" in ins.img and ignore_ld:
                continue
            # Look for the reference instruction (if exists)
            refi = None
            if ref:
                for r in ref:
                    if r.addr == ins.addr:
                        refi = r
                        break
            if refi: 
                nb_catch = refi.nb_hit
            else:
                nb_catch = 0
            if nb_catch != ins.nb_hit:
                Log.stdout("{}{} [seen {}]".format(prefix, ins, nb_catch), prefix="", lvl=3)
                uniq += 1
        return uniq

    @property
    def name(self):
        return self.__name
    @property
    def offset(self):
        return self.__offset
    @property
    def iname(self):
        return self.__iname
    @property
    def ins(self):
        return self.__ins
    @property
    def calls(self):
        return self.__calls

    def __str__(self):
        return "(@0x{:012x}) {} - called {} time{}".format(
                    self.offset,
                    self.name,
                    self.calls,
                    "s" if self.calls > 1 else "",
                )

class Instruction(object):
    def __init__(self, args):
        self.__img = args[0]
        self.__addr = int(args[1])
        self.__str = "".join(args[2:-1])
        self.__nb_hit = int(args[-1])

    @property
    def img(self):
        return self.__img
    @property
    def addr(self):
        return self.__addr
    @property
    def nb_hit(self):
        return self.__nb_hit
    def __str__(self):
        return "({}@0x{:08x}) {} -- {} time{}".format(
                        self.__img, 
                        self.__addr, 
                        self.__str, 
                        self.__nb_hit,
                        "s" if self.__nb_hit > 1 else "",
                    )

class Result(object):

    def __init__(self, path, name=""):
        self.__fn = dict()
        self.__name = name
        last_fn = None
        with open(path, "r") as f:
            # First line is elapsed time
            self.__time = f.readline()[:-1]
            for line in f.readlines():
                typ = line.split(":")[0]
                if typ == 'F':
                    fn = Function(*line[:-1].split(":")[1:])
                    self.__fn.setdefault(fn.iname, list())
                    self.__fn[fn.iname].append(fn)
                    last_fn = fn
                elif typ == 'I':
                    ins = Instruction(line[:-1].split(":")[1:])
                    if last_fn is not None:
                        last_fn.add_ins(ins)
                else:
                    Log.stderr("unrecognized format: {}".format(line))

    @property
    def fn(self):
        return self.__fn

    @property 
    def name(self):
        return self.__name

    @property 
    def time(self):
        return self.__time

    def display(self):
        tot_calls = 0
        for img, fn in self.__fn.items():
            Log.stdout(" | # {}".format(img), lvl=3, prefix="")
            for f in sorted(fn, key=lambda a: -a.calls):
                if f.calls == 0:
                    break
                Log.stdout(" | \t{}".format(f), lvl=3, prefix="")
                tot_calls += f.calls
        Log.stdout(" | ", prefix="", lvl=3)
        Log.stdout(" | TOTAL: {} calls".format(tot_calls), lvl=3, prefix="")
        # If verbose was lower than the lvl of previous messages
        if Log.get_verbose() < 3:
            # Log time
            Log.stdout("time={}".format(self.__time), lvl=1, prefix="")
            # Log summary
            Log.stdout("calls={}".format(tot_calls), lvl=1, prefix="")

    def diff(self, oracle, ignore_ld=False, no_ins=False):
        # Total number of errors
        misses = 0
        extra = 0
        # number of unique instructions causing errors
        u_misses, u_extra = 0, 0
        tot = 0
        for img, fn in oracle.fn.items():
            if "ld-linux" in img and ignore_ld:
                continue
            self.__fn.setdefault(img, list())
            Log.stdout(" | {}".format(img), prefix="", lvl=3)
            Log.stdout(" |", prefix="", lvl=3)
            for f in fn:
                g = None
                for gg in self.__fn[img]:
                    if gg.offset == f.offset:
                        g = gg
                        break
                if g is None:
                    ncalls = 0
                else:
                    ncalls = g.calls
                if ncalls < f.calls:
                    misses += (f.calls - ncalls)
                    Log.stdout(" |   (@{:012x}) {} - {} calls missed".format(f.offset, f.name, f.calls - ncalls), prefix="", lvl=3)
                    u_misses += f.print_ins(g.ins if g else None, " |      ", ignore_ld)
                elif f.calls < ncalls:
                    extra += (ncalls - f.calls)
                    Log.stdout(" |   (@{:012x}) {} - {} extra calls".format(f.offset, f.name, - f.calls + ncalls), prefix="", lvl=3)
                    u_extra += f.print_ins(g.ins if g else None, " |      ", ignore_ld)
                tot += f.calls
            for g in self.__fn[img]:
                f = None
                for ff in fn:
                    if ff.offset == g.offset:
                        f = ff
                        break
                if f is None:
                    extra += g.calls
                    Log.stdout(" |   (@{:012x}) {} - {} extra calls".format(g.offset, g.name, g.calls), prefix="", lvl=3)
                    u_extra += g.print_ins(None, " |      ", ignore_ld)
            Log.stdout(" |", prefix="", lvl=3)
        Log.stdout(" | TOTAL CALLS (ORACLE): {}".format(tot), prefix="", lvl=3)
        Log.stdout(" | TOTAL MISSES: {} ({} unique instructions)".format(misses, u_misses), prefix="", lvl=3)
        Log.stdout(" | TOTAL EXTRA: {} ({} unique instructions)".format(extra, u_extra), prefix="", lvl=3)
        if Log.get_verbose() < 3:
            Log.stdout("calls={}".format(tot), prefix="", lvl=1)
            Log.stdout("misses={}".format(misses), prefix="", lvl=1)
            Log.stdout("u_misses={}".format(u_misses), prefix="", lvl=1)
            Log.stdout("extra={}".format(extra), prefix="", lvl=1)
            Log.stdout("u_extra={}".format(u_extra), prefix="", lvl=1)

