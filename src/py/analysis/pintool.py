#-*- coding: utf-8 -*-

from confiture import Confiture, ConfigFileError
import os

from src.py.log import Log, default_log_path
from src.py.pintool import Pintool
from src.py.res import Result


def pintool_analysis(analysis, args):
    # Read configuration file
    tpl = Confiture("config/template.yaml")
    config = tpl.check_and_get("config/config.yaml")
    
    # Check if temporary repo exists
    if not os.path.exists("tmp"):
        os.makedirs("tmp")
    
    # Create Pintool object
    call = Pintool(
                        config["pin"]["path"],
                        config["pin"]["bin"],
                        config["pin"]["compile-flags"],
                        config["analysis"][analysis]["src"],
                        config["analysis"][analysis]["obj"],
                    )
    
    # Log file
    if args.log:
        log = args.log
    else:
        log = default_log_path(args.pgm, analysis) 
    
    # Compile pintool
    Log.stdout("compiling pintool")
    if not call.compile():
        Log.stdout("compilation exited with non-zero status")
        exit()
    # Launch pintool
    Log.stdout("launching analysis on {}".format(args.pgm))
    call.launch(args.pgm, args.args, None, log)
    
    # Get results
    Log.stdout("extracting results")
    res = Result(log, analysis)
    # Print the results
    Log.stdout("results of inference:")
    res.display()

