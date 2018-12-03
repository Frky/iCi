#-*- coding: utf-8 -*-

from confiture import Confiture, ConfigFileError
import os

from src.py.sym import SymExtractor
from src.py.log import Log, default_log_path, default_log_dir
from src.py.pintool import Pintool
from src.py.res import Result


def launch_analysis(args, analysis=None):
    if analysis is None:
        analysis = args.analysis

    # Read configuration file
    tpl = Confiture("config/template.yaml")
    config = tpl.check_and_get("config/config.yaml")
    
    # Check if temporary repo exists
    if not os.path.exists("tmp"):
        os.makedirs("tmp")
    
    # Extract dwarf info
    SymExtractor().extract(args.pgm, "tmp/dwarf.txt")
    
    # Create Pintool object
    pintool = Pintool(
                        config["pin"]["path"],
                        config["pin"]["bin"],
                        config["pin"]["compile-flags"],
                        config["pintool"]["src"],
                        config["pintool"]["obj"],
                    )
    
    # Log file
    if args.log:
        logidir = args.log
    else:
        logdir = default_log_dir(args.pgm)
    
    # Compile pintool
    Log.stdout("compiling pintool")
    if not pintool.compile(analysis if analysis else args.analysis):
        Log.stdout("compilation exited with non-zero status")
        exit()
    if "oracle" in analysis:
        infile = "tmp/dwarf.txt"
    else:
        infile = None
    # Launch pintool
    Log.stdout("launching analysis on {}".format(args.pgm))
    pintool.launch(args.pgm, args.args, infile, logdir, "-l true" if not args.ignore_libs else None)
    
    # Get results
    for an in analysis:
        Log.stdout("extracting results")
        res = Result(default_log_path(logdir, args.pgm, an))
        # Print the results
        Log.stdout("results of inference:")
        res.display()

