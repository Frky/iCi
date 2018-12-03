
import sys
import os

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
print r.res
draw_overhead(r)

