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
import argparse
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument('input', nargs='?')
run_arg = parser.parse_args()
table = np.loadtxt(run_arg.input, ndmin=2, dtype=str)
outname = os.path.join(os.path.dirname(run_arg.input),
                       "conv_{0:s}".format(os.path.basename(run_arg.input)))
print "+-- convert sexy ascii to plain one"
with open(run_arg.input, 'r') as _fo:
    header = []
    while True:
        ln = _fo.next()
        if ln.strip()[0] == '#':
            header.append(ln.rstrip('\n').lstrip('#').split())
        else:
            break
    if len(header) == 1:
        sys.exit(" file is already plain")
    else:
        header = [h[1] for h in header]
print " write to {0:s}".format(outname)
np.savetxt(outname, table, header=" ".join(header), fmt="%s")
