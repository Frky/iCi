#-*- coding: utf-8 -*-

import os
import sys

class Log(object):
    
    VERBOSE = 2
    OUT = sys.stdout

    @classmethod
    def get_verbose(cls):
        return Log.VERBOSE

    @classmethod
    def set_verbose(cls, value):
        Log.VERBOSE = value

    @classmethod
    def set_output(cls, out):
        if out != sys.stdout:
            Log.OUT = open(out, "w")
        else:
            Log.OUT = out
            
    @classmethod 
    def close(cls):
        if Log.OUT != sys.stdout:
            Log.OUT.close()
            Log.OUT = sys.stdout

    @classmethod
    def stdout(cls, msg, lvl=2, prefix="[*] "):
        if lvl > Log.VERBOSE:
            return
        Log.OUT.write("{}{}\n".format(prefix, msg))

    @classmethod
    def stderr(cls, msg):
        print("*** {}".format(msg))

def default_log_dir(pgm):
    # Check if default log repo exists
    if not os.path.exists("log"):
        os.makedirs("log")
    return "log/"

def default_log_path(logdir, pgm, analysis):
    return "{}/{}_{}.txt".format(logdir, os.path.basename(pgm), analysis)

