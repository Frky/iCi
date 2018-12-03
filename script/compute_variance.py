#!/usr/bin/env python
#-*- coding: utf-8 -*-

from statistics import stdev, variance, mean
import os
import sys

if len(sys.argv) < 2:
    print "Usage: {} DATA_DIR".format(sys.argv[0])
    exit()

data_dir = sys.argv[1]

data = dict()

def treat_file(fdir, fname):
    global data
    fpath = data_dir + "/" + files
    pgm, opti, i = fname.replace(".txt", "").split('_')
    data.setdefault(pgm, dict())
    data[pgm].setdefault(opti, list())
    with open(fpath) as f:
        for line in f.readlines():
            key, val = line[:-1].split('=')
            if key == "time":
                data[pgm][opti].append(float(val))
    
for files in os.listdir(data_dir):
    treat_file(data_dir, files)

OPTI = ["O0", "O1", "O2", "O3"]

tab = dict()
tab["min"] = list()
tab["max"] = list()
tab["average"] = list()

for opti in OPTI:
    vals = list()
    for p, o in data.items():
        if opti in o.keys():
            assert len(o[opti]) == 10
            d = o[opti]
            vals.append(stdev(d))
    vals.remove(max(vals))
    vals.remove(min(vals))
    tab["min"].append(min(vals))
    tab["max"].append(max(vals))
    tab["average"].append(mean(vals))

print "\\begin{tabular}{lcccc}"
print "    \\toprule"
print "     & %s\\\\" % " & ".join(map(lambda a: "{{\\bf -%s }}" % a, OPTI))
print "    \\toprule"
for k in sorted(tab.keys())[::-1]:
    v = tab[k]
    print "    %s & %s \\\\" % (k, " & ".join(map(lambda a: "{:.3f}".format(a), v)))
print "    \\bottomrule"
print "\\end{tabular}"
