#!/usr/bin/env python
#-*- coding: utf-8 -*-

from decimal import Decimal
from statistics import mean, stdev
import sys
import os
import importlib
from confiture import Confiture
import matplotlib.pyplot as plt  
import matplotlib.colors as colors

class Config(object):
    def __init__(self, c):
        self.ALS = [k for k, v in c["analysis"].items() if v]
        self.OPTI_LVL = c["output"]["opti_lvls"]
        self.DATADIR = c["datadir"]
        self.OVERHEAD = c["output"]["overhead"]
        self.FSCORE = c["output"]["fscore"]
        self.IGNORE = c["ignore"]
        if "sorted" in c["output"].keys():
            self.SORTED = c["output"]["sorted"]
        else:
            self.SORTED = False
        if "variance" in c["output"].keys():
            self.VARIANCE = c["output"]["variance"]
        else:
            self.VARIANCE = False

if len(sys.argv) < 2:
    print "Usage: {} CONFIG".format(sys.argv[0])
    exit()

c = Confiture("test/tab/template.yaml").check_and_get(sys.argv[1])

CONFIG = Config(c)

class Result(object):

    def __init__(self, pgm):
        self.pgm = pgm
        self.res = dict()
        for opti in CONFIG.OPTI_LVL:
            self.res[opti] = dict()
            for an in CONFIG.ALS: # ["jcall", "jmp", "iCi"]:
                self.res[opti][an] = dict()
                for v in ["miss", "extra", "u_miss", "u_extra", "total"]:
                    self.res[opti][an][v] = 0
                self.res[opti][an]["time"] = list()

    def add(self, res, fname):
        opti = fname.replace(".txt", "").split("_")[-1]
        if opti not in CONFIG.OPTI_LVL:
            return
        for an in CONFIG.ALS:
            try:
                self.res[opti][an]["miss"] += int(res[an]["misses"])
                self.res[opti][an]["extra"] += int(res[an]["extra"])
                self.res[opti][an]["total"] += int(res[an]["calls"])
                self.res[opti][an]["u_miss"] += int(res[an]["u_misses"])
                self.res[opti][an]["u_extra"] += int(res[an]["u_extra"])
            except Exception:
                pass

    def __parse_file(self, lines):
        res = dict()
        values = None
        for line in lines:
            k, v = line[:-1].split("=")[:2]
            if k == "analysis2":
                if values:
                    res[an] = values
                values = dict()
                an = v
            if values is not None:
               values[k] = v
        res[an] = values
        return res

    def parse_files(self, resdir):
        for fname in os.listdir(resdir):
            if not os.path.isfile(resdir + "/" + fname):
                continue
            with open("{}/{}".format(resdir, fname), "r") as f:
                self.add(self.__parse_file(f.readlines()), fname)

    def add_overhead(self, toe, fname):
        opti, an = fname.replace(".txt", "").split("_")[-2:]
        pgm = fname.replace(".txt", "").split("_")[:-2]
        if opti in self.res.keys():
            if an in self.res[opti].keys():
                self.res[opti][an]["time"].append((pgm, toe))

    def parse_overhead_one(self, lines):
        for line in lines:
            k, v = line[:-1].split("=")
            if k == "time":
                return float(v)

    def parse_overhead(self, overdir):
        for fname in os.listdir(overdir):
            with open("{}/{}".format(overdir, fname), "r") as f:
                toe = self.parse_overhead_one(f.readlines())
                self.add_overhead(toe, fname)


class LatexPrinter(object):

    h = ""

    @classmethod    
    def print_header(cls, fscore=False, overhead=False):
        l = len(CONFIG.ALS)
        print "\\begin{{tabular}}{{@{{}}l{}@{{}}}}".format(("l" if not fscore and not overhead else "") + 
                                                                "c"*(2+len(CONFIG.OPTI_LVL)*len(CONFIG.ALS) - 2))
        print "\\toprule"
        if fscore or overhead:
            print " ",
        else:
            print "\\multicolumn{2}{c}{} ", 
        for o in CONFIG.OPTI_LVL:
            print "& \\multicolumn{{{}}}{{c}}{{{{\\bf -{}}}}}".format(len(CONFIG.ALS), o),
        print "\\\\" + LatexPrinter.h
        # print "\\cline{{3-{}}}".format(2+len(OPTI_LVL)*len(ALS))
        # print "\\cline{{3-{}}}".format(2+len(OPTI_LVL)*len(ALS))
        if fscore or overhead:
            print " ",
        else:
            print "\\multicolumn{2}{c}{} ", 
        for i in xrange(len(CONFIG.OPTI_LVL)):
            for a in CONFIG.ALS:
                print "& {{\\tt {}}}".format(a),
        print "\\\\",
        print "\\toprule"

    @classmethod
    def print_res(cls, RES, overhead=True, fscore=False):
        rowname = False
        if fscore or overhead:
            print "{}".format(RES.pgm)
        else:
            print "\\multirow{{{}}}{{*}}{{{{\\tt {}}}}} ".format(5, RES.pgm)
        if not fscore and not overhead:
            print "& calls ",
            for opti in CONFIG.OPTI_LVL:
                v = RES.res[opti]["jcall"]["total"]
                if v == 0:
                    print "& \\multicolumn{{{}}}{{c}}{{n.c.}} ".format(len(CONFIG.ALS))
                else:
                    print "& \\multicolumn{{{}}}{{c}}{{{}}} ".format(len(CONFIG.ALS), v),
            print "\\\\"
        # for i, opti in enumerate(OPTI_LVL):
        #     print "\\cline{{{}-{}}}".format(2 + i * len(ALS), 4 + i*len(ALS))
        if not overhead:
            for res, u_res, resname in [("miss", "u_miss", "FN"), ("extra", "u_extra", "FP")]:
                if fscore: 
                    continue
                print "& {} ".format(resname),
                for opti in CONFIG.OPTI_LVL:
                    v = RES.res[opti]["jcall"]["total"]
                    for an in CONFIG.ALS:
                        if v == 0:
                            print "& n.c. ",
                        else:
                            if RES.res[opti][an][res] > 100000:
                                print "& {:.2E} ({})".format(Decimal(RES.res[opti][an][res]), RES.res[opti][an][u_res]),
                            else:
                                print "& {} ({})".format(RES.res[opti][an][res], RES.res[opti][an][u_res]),
                print "\\\\"
            # Print FScore
            if not fscore:
                print "& fscore ",
            for opti in CONFIG.OPTI_LVL:
                for an in CONFIG.ALS:
                    fp = RES.res[opti][an]["extra"]
                    fn = RES.res[opti][an]["miss"]
                    tp = RES.res[opti][an]["total"] - fn
                    try:
                        p = float(tp) / (float(tp) + float(fp))
                        r = float(tp) / (float(tp) + float(fn))
                        f = 2*p*r/(p + r)
                        print "& {:.3f} ".format(f),
                    except ZeroDivisionError:
                        print "& n.c.",
            print "\\\\"
            if fscore:
                return
        if not overhead:
            print "& ovhd",
        for opti in CONFIG.OPTI_LVL:
            if "noinst" in CONFIG.ALS:
                try:
                    print " & {:.3f}".format(sum(RES.res[opti]["noinst"]["time"])/sum(RES.res[opti]["jmp"]["time"])),
                except Exception as e:
                    print " & n.c.",
            if "pempty" in CONFIG.ALS:
                try:
                    print " & {:.3f}".format(sum(RES.res[opti]["pempty"]["time"])/sum(RES.res[opti]["jmp"]["time"])),
                except Exception as e:
                    print " & n.c.",
            if "jcall" in CONFIG.ALS:
                try:
                    print " & {:.3f}".format(sum(RES.res[opti]["jcall"]["time"])/sum(RES.res[opti]["jmp"]["time"])),
                except Exception as e:
                    print " & n.c.",
            if "jmp" in CONFIG.ALS:
               print " & 1.00",
            if "iCi" in CONFIG.ALS:
                try:
                    print " & {:.3f}".format(sum(RES.res[opti]["iCi"]["time"])/sum(RES.res[opti]["jmp"]["time"])),
                except Exception:
                    print " & n.c.",
        print " \\\\"


    @classmethod
    def print_empty_line(cls):
        print "\\midrule"
        pass

    @classmethod
    def print_footer(cls):
        print "\\bottomrule"
        print "\\end{tabular}"

def draw_overhead(res):
    plt.figure(figsize=(12, 9)) 
    ax = plt.subplot(111)    
    ax.spines["top"].set_visible(False)    
    ax.spines["bottom"].set_visible(False)
    ax.spines["right"].set_visible(False)    
    ax.spines["left"].set_visible(False)
    ax.get_xaxis().tick_bottom()    
    ax.get_yaxis().tick_left()    
    
    data = list()
    for pgm, r in res.items():
        for o in r.res.keys():
            try:
                data.append(sum(r.res[o]['iCi']['time'])/sum(r.res[o]['jcall']['time']))
            except TypeError:
                data.append(0)
    x_pos = range(1, len(data) + 1)
    ax.bar(x_pos, data, width=0.5, label="iCi")
    # plt.xticks(tick_pos, map(lambda a: a.tot_in + a.tot_out, data), rotation="vertical")
    plt.tick_params(axis="both", which="both", bottom="off", top="off",    
            labelbottom="on", left="off", right="off", labelleft="on") 
    plt.legend(fontsize=12)

    plt.savefig("yo.png", bbox_inches="tight") 
    return
    for opti in CONFIG.OPTI_LVL:
        if "noinst" in CONFIG.ALS:
            try:
                print " & {:.3f}".format(sum(RES.res[opti]["noinst"]["time"])/sum(RES.res[opti]["jmp"]["time"])),
            except Exception as e:
                print " & n.c.",
        if "pempty" in CONFIG.ALS:
            try:
                print " & {:.3f}".format(sum(RES.res[opti]["pempty"]["time"])/sum(RES.res[opti]["jmp"]["time"])),
            except Exception as e:
                print " & n.c.",
        if "jcall" in CONFIG.ALS:
            try:
                print " & {:.3f}".format(sum(RES.res[opti]["jcall"]["time"])/sum(RES.res[opti]["jmp"]["time"])),
            except Exception as e:
                print " & n.c.",
        if "jmp" in CONFIG.ALS:
           print " & 1.00",
        if "iCi" in CONFIG.ALS:
            try:
                print " & {:.3f}".format(sum(RES.res[opti]["iCi"]["time"])/sum(RES.res[opti]["jmp"]["time"])),
            except Exception:
                print " & n.c.",
    

if not CONFIG.FSCORE and not CONFIG.VARIANCE:
    """ 
        Draw chart of overhead

    """
    data = dict()
    for files in os.listdir(CONFIG.DATADIR):
        if os.path.isdir(CONFIG.DATADIR + "/" + files):
            if files in CONFIG.IGNORE:
                continue
            r = Result(files)
            r.parse_files(CONFIG.DATADIR + "/" + files)
            r.parse_overhead(CONFIG.DATADIR + "/" + files + "/overhead/")
            for opti in CONFIG.OPTI_LVL:
                for an in CONFIG.ALS:
                    r.res[opti][an]["time"] = map(lambda a: a[1], sorted(r.res[opti][an]["time"], key=lambda a:a[0]))
            data[files] = r
    draw_overhead(data)
    exit()

PRINTER = LatexPrinter
first_entry = True
PRINTER.print_header(CONFIG.FSCORE, CONFIG.OVERHEAD)

def treat_one(files):
    global first_entry
    r = Result(files)
    r.parse_files(CONFIG.DATADIR + "/" + files)
    if CONFIG.OVERHEAD:
        r.parse_overhead(CONFIG.DATADIR + "/" + files + "/overhead/")

        for opti in CONFIG.OPTI_LVL:
            for an in CONFIG.ALS:
                r.res[opti][an]["time"] = map(lambda a: a[1], sorted(r.res[opti][an]["time"], key=lambda a:a[0]))
    if not first_entry:
        PRINTER.print_empty_line()
    else: 
        first_entry = False
    PRINTER.print_res(r, CONFIG.OVERHEAD, CONFIG.FSCORE)

to_treat = list()
for files in os.listdir(CONFIG.DATADIR):
    if os.path.isdir(CONFIG.DATADIR + "/" + files):
        if files in CONFIG.IGNORE:
            continue
        if CONFIG.SORTED:
            to_treat.append(files)
            continue
        treat_one(files)
if CONFIG.SORTED:
    to_treat = sorted(to_treat)
    for f in to_treat:
        treat_one(f)
PRINTER.print_footer()

