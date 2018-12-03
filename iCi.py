#!/usr/bin/env python
#-*- coding: utf-8 -*-

import argparse

from src.py.analysis.diff import diff_analysis
from src.py.analysis.launch import launch_analysis
from src.py.log import Log

# First, define arguments expected from command line
parser = argparse.ArgumentParser(description='iCi -- intuitive Call instrumentation')
# Result file
parser.add_argument('cmd', type=str, metavar="ALS", nargs=1, help="basic command to execute (launch, diff, etc.)")
parser.add_argument('--analysis', type=str, metavar="ALS", nargs='+', help="analysis to launch (e.g. oracle)")
parser.add_argument('--res', type=str, metavar="RES", nargs='?', help="file to log the (plaintext) results of the analysis")
# Log file 
parser.add_argument('--log', type=str, metavar="LOG", nargs='?', help="file to log the (not formatted) results of the analysis")
parser.add_argument('--pgm', type=str, metavar="PGM", nargs='?', help="binary program to be executed")
parser.add_argument('--args', type=str, metavar="ARGS", nargs='?', help="arguments to give to the binary for the execution")
parser.add_argument('--ignore-libs', action="store_const", const=True, help="ignore everything that happens in the libraries during instrumentation")
parser.add_argument('--ignore-ld', action="store_const", const=True, help="ignore every instruction from and to ld in the output")
parser.add_argument('--no-ins', action="store_const", const=True, help="do not compare instruction by instruction (only total number of calls")
parser.add_argument('-v', action="store_const", const=True, help="output detailed results")
parser.add_argument('-q', action="store_const", const=True, help="quiet mode -- only output the minimum result info")
parser.add_argument('--run', action="store_const", const=True, metavar="RUN", help="Re-run instrumentations before diff")
args = parser.parse_args()

if args.v:
    Log.set_verbose(3)
if args.q:
    Log.set_verbose(1)
if args.res:
    Log.set_output(args.res)

if args.cmd[0] == "launch":
    launch_analysis(args)
elif args.cmd[0] == "diff":
    diff_analysis(args)
else:
    Log.stderr("unknown analysis: {}".format(args.analysis[0]))

Log.close()
