#!/usr/bin/env python

import yaml
import os
import sys
from subprocess import check_call as call

with open(sys.argv[1], "r") as f:
    benchmark = yaml.load(f)

if len(sys.argv) < 2:
    print "Usage: {} CONFIG_FILE [RES_DIR] [OPTIMIZATION_LEVELS]".format(sys.argv[0], sys.argv[1])
    exit()

if len(sys.argv) < 3:
    res_dir = "res/"
else:
    res_dir = sys.argv[2]

if len(sys.argv) < 4:
    opti_lvls = ["O0", "O1", "O2", "O3"]
else:
    opti_lvls = sys.argv[3:]

FNULL = open(os.devnull, "w")
ALS = ["oracle", "jcall", "jmp", "iCi"] 

for opti in opti_lvls:
    print "[-{}]".format(opti)
    for c, d in benchmark.items():
        if c == False:
            c = "false"
        elif c == True:
            c = "true"
        print "  {}... ".format(c),
        if "pre" in d.keys():
            call(d["pre"], stdout=FNULL, shell=True)
        cmd = ".venv/iCi/bin/python ./iCi.py launch --analysis {} --ignore-libs --pgm {}".format(
                    " ".join(ALS),
                    d["bin"][opti], 
                )
        if d["args"] != "" and d["args"] != " ":
            cmd += " --args \"{}\"".format(
                    d["args"],
                )
        call(cmd, stdout=FNULL, shell=True)
        if "post" in d.keys():
            call(d["post"], stdout=FNULL, shell=True)
        cmd = ".venv/iCi/bin/python ./iCi.py diff --pgm {} --analysis {} --res {}/{}_{}.txt".format(
                    d["bin"][opti],
                    " ".join(ALS),
                    res_dir, 
                    c, 
                    opti,
                )
        call(cmd, stdout=FNULL, shell=True)
        for an in ALS:
            call("cp log/{}_{}.txt log/{}_{}_{}.txt".format(os.path.basename(d["bin"][opti]), an, c, opti, an), stdout=FNULL, shell=True)
        print "OK"
    print
