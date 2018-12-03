#!/usr/bin/env python

import yaml
import os
import sys
from subprocess import check_call as call

print "use run_test instead"
exit()
with open(sys.argv[1], "r") as f:
    coreutils = yaml.load(f)

FNULL = open(os.devnull, "w")

ALS = ["oracle", "jcall", "jmp", "iCi"] 

for opti in sys.argv[3:]:
    for c, d in coreutils.items():
        print "{}... ".format(c),
        if "pre" in d.keys():
            call(d["pre"], stdout=FNULL, shell=True)
            print d["pre"]
        cmd = ".venv/iCi/bin/python ./iCi.py launch --analysis {} --ignore-libs --pgm {}".format(
                    " ".join(ALS),
		    d["bin"],
                )
        if d["args"] != "" and d["args"] != " ":
            cmd += " --args \"{}\"".format(
                    d["args"],
                )
        call(cmd, stdout=FNULL, shell=True)
        if "post" in d.keys():
            call(d["post"], stdout=FNULL, shell=True)
        cmd = ".venv/iCi/bin/python ./iCi.py diff --pgm {} --analysis {} --res {}/{}_{}.txt".format(
                    os.path.basename(d["bin"]),
                    " ".join(ALS),
                    sys.argv[2],
                    c, 
                    opti,
                )
        call(cmd, stdout=FNULL, shell=True)
        for an in ALS:
            call("cp log/{}_{}.txt log/{}_{}_{}.txt".format(os.path.basename(d["bin"]), an, c, opti, an), stdout=FNULL, shell=True)
        print "OK"
