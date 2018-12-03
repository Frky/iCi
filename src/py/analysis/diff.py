#-*- coding: utf-8 -*-

import os 

from src.py.analysis.launch import launch_analysis
from src.py.log import Log, default_log_path, default_log_dir
from src.py.res import Result

def diff_analysis(args):
    #     if args.file1:
    #         if not args.file2:
    #             Log.stderr("you must specify two files")
    #             exit()
    #         oracle = Result(args.file1)
    #         other = Result(args.file2)
    if not args.analysis or len(args.analysis) < 2:
        Log.stderr("you must specify at least two analysis")
        exit()
    if not args.pgm:
        Log.stderr("you must specify a program to analyze")
        exit()
    if args.run:
        lvl = Log.get_verbose()
        Log.set_verbose(0)
        launch_analysis(args)
        Log.set_verbose(lvl)
    logdir = default_log_dir(args.pgm)
    path = default_log_path(logdir, args.pgm, args.analysis[0])
    oracle = Result(path, args.analysis[0])
    for an in args.analysis[1:]:
        path = default_log_path(logdir, args.pgm, an)
        other = Result(path, an)
        if Log.get_verbose() < 3:
            Log.stdout("pgm={}".format(os.path.basename(args.pgm)), lvl=1, prefix="")
            Log.stdout("args={}".format(args.args), lvl=1, prefix="")
            Log.stdout("analysis1={}".format(oracle.name), lvl=1, prefix="")
            Log.stdout("time1={}".format(oracle.time), lvl=1, prefix="")
            Log.stdout("analysis2={}".format(other.name), lvl=1, prefix="")
            Log.stdout("time2={}".format(other.time), lvl=1, prefix="")
        other.diff(oracle, ignore_ld=args.ignore_ld)
