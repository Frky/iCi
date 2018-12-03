#!/usr/bin/env python
#-*- coding: utf-8 -*-

from subprocess import call
import os
import sys

for f in os.listdir("log/"):
    nucleus = list()
    ici = list()

    if "O2" in f and "iCi" in f:
        pgm = f.split("_")[0]
        opti = f.split("_")[1]
        outfile = "log/{}_{}_nucleus.txt".format(pgm, opti)
        if not os.path.exists(outfile):
            # Launch nucleaus and log result 
            cmd = "./ressources/nucleus -e ./bin/{}/{} -d linear | grep \"function\" | cut -d \" \" -f 3 | sed -e 's/entry@0x0000000000//g'  > {}".format(opti, pgm, outfile)
            call(cmd, shell=True)

        # Read nucleus results
        with open(outfile, 'r') as f:
            nucleus = map(lambda a: int(a[:-1], 16), f.readlines())
        
        # Read iCi log file 
        with open("log/{}_{}_iCi.txt".format(pgm, opti), 'r') as f:
            for l in f.readlines():
                ll = l.split(":")
                if ll[0] == 'F':
                    iCi.append((int(ll[-3]), ll[1]))
        
        names = dict()
        
        # Try to read the oracle to get symbols
        if os.path.exists(outfile.replace("nucleus", "oracle")):
            with open(outfile.replace("nucleus", "oracle"), 'r') as f:
                for l in f.readlines():
                    ll = l.split(":")
                    if ll[0] == 'F':
                        addr = int(ll[-3])
                        name = ll[-2]
                        names[addr] = name
        
        name_printed = False
        for f, path in iCi:
            if f not in nucleus:
                name = names[f] if f in names.keys() else ""
                if "plt" not in name and name != "":
                    if not name_printed:
                        print "# {}".format(pgm.upper())
                        name_printed = True
                    print "[{}] {}".format(hex(f), name)
        if name_printed:
            print
        
