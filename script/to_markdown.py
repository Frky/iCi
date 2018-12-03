#!/usr/bin/env python
#-*- coding: utf-8 -*-

from decimal import Decimal
from statistics import mean, stdev
import sys
import os

ALS = ["jcall", "jmp", "iCi"]
FSCORE = False # True
OVERHEAD = False # True
IGNORE = []
IGNORE = ["SPEC2006", "SPEC2006_save"]
IGNORE = ["fp", "int", "overhead"]
OPTI_LVL = ["O0", "O1", "O2", "O3"]
LATEX = True

if len(sys.argv) < 2:
    print "Specify a res directory"
    exit()

resdir = sys.argv[1]

class Result(object):

    def __init__(self, pgm):
        self.pgm = pgm
        self.res = dict()
        for opti in OPTI_LVL:
            self.res[opti] = dict()
            for an in ["jcall", "jmp", "iCi"]:
                self.res[opti][an] = dict()
                for v in ["miss", "extra", "u_miss", "u_extra", "total"]:
                    self.res[opti][an][v] = 0
                self.res[opti][an]["time"] = list()

    def add(self, res, fname):
        opti = fname.replace(".txt", "").split("_")[-1]
        if opti not in OPTI_LVL:
            return
        for an in ["jcall", "jmp", "iCi"]:
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


class HtmlPrinter(object):

    @classmethod    
    def print_header(cls):
        l = len(ALS)
        print "<table>"
        print " <thead>"
        print "  <tr>"
        print "   <th colspan=2 rowspan=2></th>"
        for o in OPTI_LVL:
            print "   <th colspan={}>{}</th>".format(l, o)
        print "  </tr>"
        print "  <tr>"
        for i in xrange(len(OPTI_LVL)):
            for a in ALS:
                print "   <th>{}</th>".format(a)
        print "  </tr>"
        print " </thead>"
        print " <tbody>"

    @classmethod
    def print_res(cls, RES, overhead=True):
        rowname = False
        print "   <tr>"
        print "    <td rowspan={}>{}</td>".format(2 if overhead else 6, RES.pgm)
        print "    <td>total</td>"
        for opti in OPTI_LVL:
            v = RES.res[opti]["jcall"]["total"]
            if v == 0:
                v = "n.c."
            print "   <td colspan={} style=\"text-align: center;\">{}</td>".format(len(ALS), v)
        print "   </tr>"
        if not overhead:
            print "<tr>" + "<td colspan={}></td>".format(len(OPTI_LVL)*len(ALS) + 1) + "</tr>" 
            for res in ["miss", "extra"]:
                print "   <tr>"
                print "    <td>{}</td>".format(res)
                for opti in OPTI_LVL:
                    v = RES.res[opti]["jcall"]["total"]
                    for an in ALS:
                        if v == 0:
                            print "   <td>n.c.</td>"
                        else:
                            print "   <td>{}</td>".format(RES.res[opti][an][res])
                print "   </tr>"
            print "<tr>" + "<td colspan={}></td>".format(len(OPTI_LVL)*len(ALS) + 1) + "</tr>" 
            # Print FScore
            print "  <tr>"
            print "   <td>fscore</td>"
            for opti in OPTI_LVL:
                for an in ALS:
                    fp = RES.res[opti][an]["extra"]
                    fn = RES.res[opti][an]["miss"]
                    tp = RES.res[opti][an]["total"] - fn
                    try:
                        p = float(tp) / (float(tp) + float(fp))
                        r = float(tp) / (float(tp) + float(fn))
                        f = 2*p*r/(p + r)
                        print "   <td>{:.3f}</td>".format(f)
                    except ZeroDivisionError:
                        print "   <td>n.c.</td>"
            print "  </tr>"
            return
        print "   <tr>"
        print "    <td>overhead</td>"
        for opti in OPTI_LVL:
            if "jcall" in ALS:
                try:
                    print "    <td>{:.3f}</td>".format(sum(RES.res[opti]["jcall"]["time"])/sum(RES.res[opti]["jmp"]["time"]))
                except Exception as e:
                    print "    <td>n.c.</td>"
            if "jmp" in ALS:
               print "    <td>1.00</td>"
            if "iCi" in ALS:
                try:
                    print "    <td>{:.3f}</td>".format(sum(RES.res[opti]["iCi"]["time"])/sum(RES.res[opti]["jmp"]["time"]))
                except Exception:
                    print "    <td>n.c.</td>"
        print "  </tr>"

    @classmethod
    def print_empty_line(cls):
        print "  <tr>"
        print "   <td colspan={}></td>".format(len(OPTI_LVL) * len(ALS) + 2)
        print "  </tr>"

    @classmethod
    def print_footer(cls):
        print "   </tr>"
        print " </tbody>"
        print "</table>"


class LatexPrinter(object):

    h = ""

    @classmethod    
    def print_header(cls, fscore=False, overhead=False):
        l = len(ALS)
        print "\\begin{{tabular}}{{@{{}}l{}@{{}}}}".format(("l" if not fscore and not overhead else "") + 
                                                                "c"*(2+len(OPTI_LVL)*len(ALS) - 2))
        print "\\toprule"
        if fscore or overhead:
            print " ",
        else:
            print "\\multicolumn{2}{c}{} ", 
        for o in OPTI_LVL:
            print "& \\multicolumn{{{}}}{{c}}{{{{\\bf -{}}}}}".format(len(ALS), o),
        print "\\\\" + LatexPrinter.h
        # print "\\cline{{3-{}}}".format(2+len(OPTI_LVL)*len(ALS))
        # print "\\cline{{3-{}}}".format(2+len(OPTI_LVL)*len(ALS))
        if fscore or overhead:
            print " ",
        else:
            print "\\multicolumn{2}{c}{} ", 
        for i in xrange(len(OPTI_LVL)):
            for a in ALS:
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
            for opti in OPTI_LVL:
                v = RES.res[opti]["jcall"]["total"]
                if v == 0:
                    print "& \\multicolumn{{{}}}{{c}}{{n.c.}} ".format(len(ALS))
                else:
                    print "& \\multicolumn{{{}}}{{c}}{{{}}} ".format(len(ALS), v),
            print "\\\\"
        # for i, opti in enumerate(OPTI_LVL):
        #     print "\\cline{{{}-{}}}".format(2 + i * len(ALS), 4 + i*len(ALS))
        if not overhead:
            for res, u_res, resname in [("miss", "u_miss", "FN"), ("extra", "u_extra", "FP")]:
                if fscore: 
                    continue
                print "& {} ".format(resname),
                for opti in OPTI_LVL:
                    v = RES.res[opti]["jcall"]["total"]
                    for an in ALS:
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
            for opti in OPTI_LVL:
                for an in ALS:
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
        for opti in OPTI_LVL:
            if "jcall" in ALS:
                try:
                    print " & {:.3f}".format(sum(RES.res[opti]["jcall"]["time"])/sum(RES.res[opti]["jmp"]["time"])),
                except Exception as e:
                    print " & n.c.",
            if "jmp" in ALS:
               print " & 1.00",
            if "iCi" in ALS:
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

if LATEX:
    PRINTER = LatexPrinter
else:
    PRINTER = HtmlPrinter
first_entry = True
PRINTER.print_header(FSCORE, OVERHEAD)
for files in os.listdir(sys.argv[1]):
    if os.path.isdir(sys.argv[1] + "/" + files):
        if files in IGNORE:
            continue
        r = Result(files)
        r.parse_files(sys.argv[1] + "/" + files)
        if OVERHEAD:
            r.parse_overhead(sys.argv[1] + "/" + files + "/overhead/")

            for opti in OPTI_LVL:
                for an in ["jcall", "jmp", "iCi"]:
                    r.res[opti][an]["time"] = map(lambda a: a[1], sorted(r.res[opti][an]["time"], key=lambda a:a[0]))
        if not first_entry:
            PRINTER.print_empty_line()
        else: 
            first_entry = False
        PRINTER.print_res(r, OVERHEAD, FSCORE)
PRINTER.print_footer()
