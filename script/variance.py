#!/usr/bin/env python

import yaml
import os
import sys
from subprocess import check_call as call
import time


if len(sys.argv) < 2:
    print "Usage: {} CONFIG_FILE [RES_DIR] [OPTIMIZATION_LEVELS]".format(sys.argv[0])
    exit()

with open(sys.argv[1], "r") as f:
    benchmark = yaml.load(f)

if len(sys.argv) < 3:
    res_dir = "res/"
else:
    res_dir = sys.argv[2]

if len(sys.argv) < 4:
    opti_lvls = ["O0", "O1", "O2", "O3"]
else:
    opti_lvls = sys.argv[3:]

FNULL = open(os.devnull, "w")
ALS = ["iCi"] 

for opti in opti_lvls:
    print "[-{}]".format(opti)
    for c, d in benchmark.items():
        if c == False:
            c = "false"
        elif c == True:
            c = "true"
        print "  {}... ".format(c),

        for i in xrange(10):
            if "pre" in d.keys():
                call(d["pre"], stdout=FNULL, shell=True)
            cmd = ".venv/iCi/bin/python ./iCi.py launch --analysis {} --ignore-libs --pgm {} --res {}/variance/{}_{}_{}.txt -q".format(
                        " ".join(ALS),
                        d["bin"][opti],
                        res_dir,
                        c, 
                        opti,
                        i,
                    )
            if d["args"] != "" and d["args"] != " ":
                cmd += " --args \"{}\"".format(
                        d["args"],
                    )
            call(cmd, stdout=FNULL, shell=True)
            if "post" in d.keys():
                call(d["post"], stdout=FNULL, shell=True)
        print "OK"
