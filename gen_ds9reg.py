#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Create Date    :  2013-08-29 15:42
# Python Version :  2.7.3
# Git Repo       :  https://github.com/Jerry-Ma
# Email Address  :  jerry.ma.nk@gmail.com
"""
gen_ds9reg.py
"""


import argparse
import readline
import numpy as np


def def_raw_input(prompt, default=''):
    readline.set_startup_hook(lambda: readline.insert_text(default))
    try:
        return raw_input(prompt)
    finally:
        readline.set_startup_hook()


def guess_xy(header, strx, stry, use_all=False, col=None):

    if not col is None:
        return [col,], ("cx", "cy")
    try:
        strx, restx = strx.split('|', 1)
        stry, resty = stry.split('|', 1)
    except ValueError:
        restx = resty = ''
    _header = [_h.lower() for _h in header]
    _ix = [_i for _i, _h in enumerate(_header) if strx in _h]
    ixy = [(_i, _header.index(_header[_i].replace(strx, stry))) for _i in _ix
            if _header[_i].replace(strx, stry) in _header]
    nxy = len(ixy)

    if nxy == 0:
        print '!------------',
        print ' no {:s}/{:s} detected'.format(strx, stry),
        print '------------!'
        if restx and resty:
            return guess_xy(header, restx, resty, use_all=useall)
        else:
            _sel =  def_raw_input('specify the coords system[x,y|ra,dec]? ', 'x,y').split(',')
            str_xy = (_sel[0], _sel[1])
            _sel =  def_raw_input('specify the column number? ', '1,2').split(',')
            sel_ixy = [(int(_sel[0]), int(_sel[1]))]
            return sel_ixy, str_xy
    else:
        print '+------------',
        print ' detected {:s}/{:s} cols'.format(strx, stry),
        print '-------------+'
        for _i, (_ix, _iy) in enumerate(ixy):
            print ' PAIR [{:d}]   {:3d}: {:10s}  |  {:3d}: {:10s}'.format(
                                                        _i + 1,
                                                        _ix, header[_ix],
                                                        _iy, header[_iy])
    sel_ixy = ixy
    if nxy > 1:
        while not use_all:
            _sel = def_raw_input(
                'choose the pair of coords [{:d}-{:d}]? '.format(1, nxy), '1')
            if _sel in [str(_i) for _i in range(1, nxy + 1)]:
                sel_ixy = [ixy[int(_sel) - 1]]
                break
    return sel_ixy, (strx, stry)


parser = argparse.ArgumentParser()
parser.add_argument('input', nargs='?')
parser.add_argument('-c', '--global-color', nargs='?',
                    default='green',
                    choices=['white',
                             'black',
                             'red',
                             'green',
                             'blue',
                             'cyan',
                             'magenta',
                             'yellow'])
parser.add_argument('-d', '--global-coordinate', nargs='?',
                    default='fk5',
                    choices=['physical',  # pixel coords of original file
                             'image',     # pixel coords of current file
                             'fk4',       # sky coordinate systems
                             'fk5',       # sky coordinate systems
                             'galactic',  # sky coordinate systems
                             'ecliptic',  # sky coordinate systems
                             ])
parser.add_argument('-r', '--circle-radius', nargs='?', default='1\'')
parser.add_argument('-s', '--specify-column', nargs='?')
parser.add_argument('-x', '--index-on', action='store_true')
parser.add_argument('-u', '--use-all-xy', action='store_true')
parser.add_argument('-t', '--extra-text', nargs='?')
parser.add_argument('-l', '--legend-text', nargs='?')
parser.add_argument('-p', '--legend-position', nargs='?')
run_arg = parser.parse_args()

color = run_arg.global_color
coord = run_arg.global_coordinate
radius = run_arg.circle_radius
column = run_arg.specify_column
useall = run_arg.use_all_xy
index = run_arg.index_on
extext = run_arg.extra_text
ltext = run_arg.legend_text
lpos = run_arg.legend_position
if ltext:
    ltext = ltext.split(',')
    if not lpos:
        lpos = (-5, -5)
    else:
        lpos = lpos.split(',')
    offunit = radius[-1]
    offnum = float(radius[0:-1])
    deg_conv = {'d': 1, '\'': 60, '\"': 3600}
if not column is None:
    column = map(int, column.split(','))
    print " use coordinate system {0:s}".format(coord)

strxy = {
         'physical': ('x', 'y'),
         'image': ('x', 'y'),
         'fk4': ('ra|alpha', 'dec|delta'),
         'fk5': ('ra|alpha', 'dec|delta'),
         'galactic': ('l', 'b'),
         'ecliptic': ('l', 'b'),
         }

table = np.loadtxt(run_arg.input, ndmin=2, dtype=str)

with open(run_arg.input, 'r') as _fo:
    header = []
    while True:
        _ln = _fo.next()
        if _ln.strip()[0] == '#':
            header.append(_ln.rstrip('\n').lstrip('#').split())
        else:
            break
    if len(header) == 1:
        header = header[0]
    else:
        header = [_h[1] for _h in header]

xycol, strxy = guess_xy(header, *strxy[coord], use_all=useall, col=column)

for _i, (_ix, _iy) in enumerate(xycol):

    regfile = run_arg.input + '_' +\
                ''.join(strxy) + str(_ix) + str(_iy) + '.reg'
    print '+------------'
    print ' write to region file:'
    print '     {:s}'.format(regfile)
    with open(regfile, 'w') as _fo:
        _fo.write('global color={:s}\n'.format(color))
        for _ind, _cont in enumerate(table):
            if index:
                _index = 'No.{:d}'.format(_ind+1)
            else:
                _index = ''
            try:
                #_extext = ', {:s}={:s}'.format(extext,
                                             #_cont[header.index(extext)])
                if index:
                    _extext = ', {:s}'.format(
                        _cont[header.index(extext)])
                else:
                    _extext = '{:s}'.format(_cont[header.index(extext)])
            except ValueError:
                if extext:
                    print ' invalid extra text'
                _extext = ''
            _fo.write('{:s}; circle({:s} {:s} {:s}) # text={{{:s}{:s}}}\n'
                .format(coord, _cont[_ix], _cont[_iy], radius,
                        _index, _extext))
            if ltext:
                lposx = float(_cont[_ix]
                              ) + offnum / deg_conv[offunit] * float(lpos[0])
                lposy = float(_cont[_iy]
                              ) + offnum / deg_conv[offunit] * float(lpos[1])
                legend = []
                for l in ltext:
                    #legend.append('{0:s}: {1:s}'.format(
                    legend.append('{1:s}'.format(
                        l, _cont[header.index(l)]))
                _fo.write('{:s}; text({!s} {!s}) # text={{{:s}}}\n'
                    .format(coord, lposx, lposy,
                        ' '.join(legend)))


