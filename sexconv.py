#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Create Date    :  2013-12-01 19:45
# Python Version :  2.7.3
# Git Repo       :  https://github.com/Jerry-Ma
# Email Address  :  jerry.ma.nk@gmail.com
"""
sexconv.py
"""

import numpy as np
import os
import sys
import glob

tables = []
if len(sys.argv) > 1:
    for argv in sys.argv[1:]:
        tables += map(os.path.abspath, glob.glob(argv))
else:
    if sys.stdin.isatty():
        for ln in sys.stdin:
            tables.append(os.path.abspath(ln))
    else:
        print "Usage: python {0} <sexy catalog files>".format(os.path.basename(sys.argv[0]))
        sys.exit(1)

print "+-- convert sexy ascii to plain one"
error = []
for table in tables:
    try:
        tbl = np.loadtxt(table, ndmin=2, dtype=str)
        outname = os.path.join(os.path.dirname(table),
                            "conv_{0:s}".format(os.path.basename(table)))
        with open(table, 'r') as _fo:
            header = []
            while True:
                ln = _fo.next()
                if ln.strip()[0] == '#':
                    header.append(ln.rstrip('\n').lstrip('#').split())
                else:
                    break
            if len(header) == 1:
                raise ValueError("file is already plain")
            else:
                # need to respect the index then the name
                hdr = []
                while len(header) > 0:
                    i, field = header.pop(0)[:2]
                    i = int(i)
                    j = len(hdr)
                    if i > j + 1:  # the previous field is an array
                        arr = map('_'.join, zip([hdr[-1], ] * (i - j), map(str, range(1 , i - j + 1))))
                        hdr = hdr[:-1] + arr
                    hdr.append(field)
                header = hdr
        print "{0:s}".format(outname)
        np.savetxt(outname, tbl, header=" ".join(header), fmt="%s")
    except Exception as e:
        error.append((table, e))

if error:
    print "+-- error encountered for the following catalogs"
    for t, e in error:
        print t
        print "[x] {0}".format(e)

