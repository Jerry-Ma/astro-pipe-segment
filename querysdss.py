#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Create Date    :  2014-01-28 13:20
# Python Version :  2.7.5
# Git Repo       :  https://github.com/Jerry-Ma
# Email Address  :  jerry.ma.nk@gmail.com
"""
querysdss.py
"""


import os
import sys
import re
import time
import multiprocessing
from collections import OrderedDict
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print '''
+- script for retrieving SDSS fits file by query of coverage check service
[x] required package is missing:
     requests
     bs4
    solution (need to install pip first):
     pip install requests
     pip install beautifulsoup4
    '''
    sys.exit(1)


SDSS_DR = 10
if SDSS_DR == 10:
    TABLE_CLASS = 'table table-border'
    RERUN = 301


def pprint(coverage):
    head, body = coverage
    s = []
    s.append('+- SDSS coverage by RA and Dec [DR{0:d}]'.format(SDSS_DR))
    s.append(' {0:^14s}{1:^14s}|{2:^8s}{3:^8s}{4:^7s}'
             '|{5:^6s}{6:^6s}{7:^7s}'.format(head[0], head[1],
                                             *head[2] + head[3]))

    def trunc(n):
        if len(n) > 14:
            return '{0:14.10f}'.format(float(n))
        else:
            return n

    for i in body:
        s.append(' ' + '-' * 72)
        nentry = max(map(len, i[2:4]))
        if nentry:
            for j in range(0, nentry):
                if j > 0:
                    radec = ['', ] * 2
                else:
                    radec = map(trunc, i[0:2])
                try:
                    m = i[2][j]
                except IndexError:
                    m = ['', ] * 3
                try:
                    n = i[3][j]
                except IndexError:
                    n = ['', ] * 3
                k = radec + m + n
                s.append(' {0:^14s}{1:^14s}|{2:^8s}{3:^8s}{4:^7s}'
                         '|{5:^6s}{6:^6s}{7:^7s}'.format(*k))
        else:
            k = i[0:2] + ['', ] * 6
            s.append(' {0:^14s}{1:^14s}|{2:^8s}{3:^8s}{4:^7s}'
                     '|{5:^6s}{6:^6s}{7:^7s}'.format(*k))
    s.append('+' + '-' * 72)
    return '\n'.join(s)


def tprint(coverage, info='image'):
    head, body = coverage
    info = info.lower()
    if info == 'image':
        index = 3
    elif info == 'spectrum':
        index = 2
    else:
        return None
    s = []
    s.append('+- SDSS ({0:s}) coverage by RA and Dec [DR{1:d}]'
             .format(info, SDSS_DR))
    s.append('# {0:15s}{1:15s}{2:7s}{3:7s}{4:8s}'
             .format(head[0], head[1], *head[index]))
    for i in body:
        nentry = len(i[index])
        if nentry:
            for j in range(0, nentry):
                k = i[0:2] + i[index][j]
                s.append('  {0:15s}{1:15s}{2:7s}{3:7s}{4:8s}'.format(*k))
        else:
            k = i[0:2] + ['n/a', ] * 3
            s.append('  {0:15s}{1:15s}{2:7s}{3:7s}{4:8s}'.format(*k))
    return '\n'.join(s)


def parse_table(html):
    head = []
    body = []
    parsed = BeautifulSoup(html)
    table = parsed.find('table', class_=TABLE_CLASS)
    thead = table.thead.find('tr').find_all('th')
    tbody = table.tbody.find_all('tr')
    for i, j in enumerate(thead):
        if j.string is None:
            # handle span
            _string = list(j.stripped_strings)[1]
            head.append([s.strip().replace(' ', '_')
                         for s in _string.replace(':', '/').split('/')])
        else:
            head.append(j.string.strip())
    for k in tbody:
        body.append([])
        for i, j in enumerate(k.find_all('td')):
            if j.string is None:
                cell = []
                _span = j.find_all('span')
                if _span:
                    for m, n in enumerate(j.find_all('a')):
                        _string = _span[m].string + n.string
                        cell.append([s.strip() for s
                                     in _string.replace(':', '/').split('/')])
                else:
                    for n in j.find_all('a'):
                        _string = n.string
                        cell.append([s.strip() for s
                                     in _string.replace(':', '/').split('/')])
                body[-1].append(cell)
            else:
                body[-1].append(j.string.strip())
    return head, body


def check_coverage(radecs):
    coords = '\n'.join(['  '.join(map(str, i)) for i in radecs])
    url = 'http://dr{0:d}.sdss3.org/coverageCheck/search'.format(SDSS_DR)
    response = requests.post(url=url, data={'radecs': coords})
    if response.status_code == requests.codes.ok:
        head, body = parse_table(response.text)
        return head, body
    else:
        raise IOError('unexpected response from server')


def human_readable_size(number_bytes):
    for x in ['b', 'k', 'm']:
        if number_bytes < 1024.0:
            return "%.1f%s" % (number_bytes, x)
        number_bytes /= 1024.0


def machine_readable_size(string):
    number, unit = re.match('(\d+\.?\d*)(\w*)', string).groups()
    conv = {'k': 1024, 'm': 1024 * 1024}
    if number:
        if unit:
            return float(number) * conv.get(unit.lower(), 0)
        else:
            return float(number)
    return 0


def download_sdss_fits_image(run, camcol, field, filter_, dir_, queue):
    url = ('http://data.sdss3.org/sas/dr10/boss/photoObj/'
           'frames/{rerun:d}/{run:d}/{camcol:d}/'
           'frame-{filter_:s}-{run:06d}-{camcol:d}-{field:04d}.fits.bz2'
           .format(rerun=RERUN, run=run, camcol=camcol, field=field,
                   filter_=filter_))
    local_fn = os.path.join(dir_, url.split('/')[-1])
    if not os.path.isdir(dir_):
        os.makedirs(dir_)
    response = requests.get(url, stream=True)
    tl = human_readable_size(int(response.headers.get('content-length')))
    with open(local_fn, 'wb') as fo:
        dl = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:  # filter out keep-alive new chunks
                dl += len(chunk)
                fo.write(chunk)
                fo.flush()
                _dl = human_readable_size(dl)
                queue.put([filter_, _dl, tl])
    return local_fn


def deg2SDSSname(ra, dec):
    if ra < 0:
        ra = 360. - ra
    hh = int(ra / 15.)
    mm = int((ra - hh * 15) * 4)
    ss = (ra - hh * 15 - mm / 4.) * 240
    hra = '{0:2d}{1:2d}{2:5s}'.format(hh, mm, str(ss))
    if dec < 0:
        sign = '-'
    else:
        sign = '+'
    dd = int(dec)
    dm = int((dec - dd) * 60)
    ds = (dec - dd - dm / 60.) * 3600
    hdec = '{0:s}{1:2d}{2:2d}{3:4s}'.format(sign, dd, dm, str(ds))
    return 'J{0:s}{1:s}'.format(hra, hdec)


def human_readable_time(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60.
    return "{}:{:>02}:{:>05.2f}".format(h, m, s)


def map_download(args):
    return download_sdss_fits_image(*args)


def bulk_download_fits_images(coverage, filters=['u', 'g', 'r', 'i', 'z'],
                              save_strategy='default',
                              dir_=os.getcwd()):
    print '+- retrieve fits file from SDSS SAS server portal'
    print ' retrieving for filters: {0:s}'.format(' '.join(filters))
    print ' save strategy: {0:s}'.format(save_strategy)
    print ' target directory: {0:s}'.format(dir_)
    dl_args = []
    for current_job, i in enumerate(coverage[1]):
        for j in i[3]:
            try:
                run, camcol, field = map(int, j)
                if save_strategy == 'mosaic':
                    sdss_name = deg2SDSSname(*map(float, i[0:2]))
                    dl_dir = os.path.join(dir_, sdss_name)
                else:
                    dl_dir = dir_
                dl_args.append([run, camcol, field, dl_dir])
                if save_strategy == 'demo':
                    break
            except ValueError:
                pass

    _args = list(OrderedDict.fromkeys(tuple(x) for x in dl_args))
    total_job = len(_args)
    total_job_width = len(str(total_job))
    total_job_tmp = '[{{0:>{0:d}d}}/{{1:>{0:d}d}}]'.format(total_job_width)
    manager = multiprocessing.Manager()
    queue = manager.Queue()
    pool = multiprocessing.Pool(processes=len(filters))
    for i, j in enumerate(_args):
        starttime = time.time()
        dl_status = dict.fromkeys(filters, '--/--')

        dl_status['job_id'] = total_job_tmp.format(i + 1, total_job)
        res = pool.map_async(map_download, [(j[0], j[1], j[2], f, j[3],
                                             queue) for f in filters])
        while True:
            try:
                res.get(0.5)
                break
            except multiprocessing.TimeoutError:
                while not queue.empty():
                    f, dl, tl = queue.get()
                    dl_status[f] = '{0:s}/{1:s}'.format(dl, tl)
                pbfmt = '{job_id:s} ' + ' '.join(
                    ['{{{0:s}:12s}}'.format(i) for i in filters])
                sys.stdout.write('\r{0:79s}'.format(pbfmt.format(**dl_status)))
                sys.stdout.flush()
        tot_time = time.time() - starttime
        tot_size = sum([machine_readable_size(dl_status[i].split('/')[-1])
                        for i in filters])
        summary = ('{0:s} time elapsed: {1:11s} total size: {2:8s}'
                   ' speed: {3:>8s}/s'
                   .format(dl_status['job_id'],
                           human_readable_time(tot_time),
                           human_readable_size(tot_size),
                           human_readable_size(tot_size / tot_time)))
        print '\r{0:79s}'.format(summary)
    pool.close()
    pool.join()
    print '\r{0:79s}'.format('+- done!')


if __name__ == '__main__':

    import argparse

    re_radec = re.compile(r'(\d\d):(\d\d):(\d\d\.?\d*)[;, ]+'
                          '([+-]?)(\d\d):(\d\d):(\d\d\.?\d*)')

    def string2deg(string):
        if ':' in string:
            hh, mm, ss, sign, dd, dm, ds = re_radec.match(string).groups('+')
            ra = float(hh) * 15 + float(mm) / 4. + float(ss) / 240.
            dec = float(dd) + float(dm) / 60. + float(ds) / 3600.
            if sign == '-':
                dec = -dec
            return [ra, dec]
        else:
            return map(float, string.split(','))

    def select_radec_col(source, head, prior=None,):
        _head = [h.lower() for h in head]
        coord_str = [('ra', 'dec'), ('alpha', 'delta')]
        ixy = []
        for strx, stry in coord_str:
            ix = [i for i, h in enumerate(_head) if strx in h]
            ixy.extend([(i, _head.index(_head[i].replace(strx, stry)))
                        for i in ix
                        if _head[i].replace(strx, stry) in _head])
        nxy = len(ixy)
        if nxy < 1:
            selected_ixy = None
        else:
            if nxy > 1:
                if prior is None:
                    print '+- ambiguous on parsing: {0:s}'.format(source)
                    print ' detected {0:s}/{1:s}'.format('ra', 'dec')
                    for i, (ix, iy) in enumerate(ixy):
                        print ' [{0:d}] {1:3d}: {2:10s} | {3:3d}: {4:10s}'\
                            .format(i + 1, ix, head[ix], iy, head[iy])
                    if source != '-':
                        sel = raw_input(
                            'choose the pair of coords [{:d}-{:d}]? '.format(
                                1, nxy))
                    else:
                        parser.error('ra, dec columns have to'
                                     ' be set (use -p) in prior '
                                     'when reading through a pipe')
                    if sel in map(str, range(1, nxy + 1)):
                        selected_ixy = ixy[int(sel) - 1]
                else:
                    try:
                        selected_ixy = ixy[prior - 1]
                    except IndexError:
                        parser.error('illegal column '
                                     'selection prior')
            else:
                selected_ixy = ixy[0]
        return selected_ixy

    def file2deg(fname, col_prior=None):
        '''parser to:
                ignore blank lines
                treat first block of # commented line(s) as head
                use head to determine column number of ra,dec
                (compatible with ascii file by sextractor)
                if no head found, check first 3 lines in data block,
                to deal with case of a csv header (with possible unit).
                return converted ra,dec pair based on col_prior:
                    None: let user to choose
                    int: choose the indicated pair
                    tuple: choose the indicated indice
        '''
        coords = []
        fo = argparse.FileType('r')(fname)
        head_need_parsed = True
        head = []
        body = []
        for ln in fo:
            if ln.startswith('#'):
                if head_need_parsed:
                    head.append(re.split('[;, ]+',
                                ln.lstrip('#').rstrip('\n').strip()))
            else:
                if ln.strip():
                    head_need_parsed = False
                    body.append(re.split('[;, ]+', ln.rstrip('\n').strip()))
        fo.close()
        if not head:  # get possible csv head
            def isstr(s):
                try:
                    float(s)
                    return False
                except ValueError:
                    return True
            if len(body) > 1:
                for i in range(1, min(3, len(body))):
                    if map(isstr, body[i]) != map(isstr, body[i - 1]):
                        head = body[0]
                        body = body[i:]
                        break
        elif len(head) == 1:  # ascii table with normal head
            head = head[0]
        else:
            head = [i[1] for i in head]
        # disqualify only non-head comments
        if head and len(head) != len(body[0]):
            head = []
        if isinstance(col_prior, (tuple, list)):
            ij = col_prior
        else:
            if head:
                ij = select_radec_col(fname, head, prior=col_prior)
            else:
                ij = (0, 1)
        # when no ra,dec found in head
        if ij is None and head:
            parser.error('failed parsing column numbers of '
                         'ra,dec from header line(s), '
                         'use -p to specify.')
        for j in body:
            coords.append(string2deg(','.join([j[k] for k in ij])))
        return coords

    def parse_col_prior(arg):
        if len(arg.split(',')) == 2:
            return map(int, arg.split(','))
        else:
            if arg == '-':
                return None
            else:
                return int(arg)

    parser = argparse.ArgumentParser(formatter_class=
                                     argparse.RawTextHelpFormatter,
                                     description='''
+- A command-line interface to the SDSS SAS web portal
 It takes a varieties of forms (and any possible combination) of
 coordinates, then,
     * performs coverage check, and print output as designated format
     * with download directory given (use -d), corresponding fits
       image will be downloaded.
+- script by Jerry Ma
''')
    parser.add_argument('coordinates', nargs='+',
                        help='''feed input coordinates by a series
(or a combination) of ra,dec pairs or ascii files
that contain the coordinates, eg.:
[prog] 111.1,-22.2 11:11:11,+22:22:22 file ...

the columns where RA and Dec are presented in csv
or ascii table with appropriate header (include
sextractor-like header format) can be recognized;
in case of pure data, the first 2 columns are taken
as coordinate. file example:
# ra dec
  141.23   14.4
  12:23:34 -13:23:23

'-' should be present in order to receive input
from a pipe, eg.:
cat file1 | [prog] -''')
    parser.add_argument('-b', '--download-bands', nargs='+',
                        choices=['u', 'g', 'r', 'i', 'z'],
                        help='''select SDSS bands to download, eg.
[prog] -b u g r i z''',
                        default=['u', 'g', 'r', 'i', 'z'],)
    parser.add_argument('-d', '--download-dir', nargs='?',
                        const=os.getcwd(),
                        help='''enable to retrieve fits image to
designated directory. default is the current directory''')
    parser.add_argument('-p', '--column-select-prior', nargs='+',
                        type=parse_col_prior,
                        help='''provide to help file parser determine
which columns to use as ra and dec

m,n to specified directly the indice
    of columns (start from 0)
p   to notify the parser choose the
    p-th detected pair (start from 1)
-   a position holder that does nothing

multiple values are needed if multiple
input files are to be parsed, eg.
[prog] file1 file2 file3 -p 0,1 - 1
will instruct the parser to take
column 0,1 of file1 and the 1st
detected pair of columns of file2''')
    parser.add_argument('-t', '--table-output', action='store_true',
                        help='''format output of coverage check
to regular ascii table''')

    parser.add_argument('-s', '--save-strategy', nargs='?',
                        default='default',
                        choices=['default', 'demo', 'mosaic'],
                        help='''save strategy to use, can be
default  save all referred fits images
         to folder specified by -d
demo     only save one image for each
         ra,dec pair
mosaic   save fits images to individual
         sub-folders name by SDSS naming
         convention, JHHMMSS.ss+DDMMSS.s
use 'default' when option not present''')
    run_arg = parser.parse_args()
    # disable pipe when no - is present
    if not '-' in run_arg.coordinates and not sys.stdin.isatty():
        parser.error('pipe detected while no "-" found in arguments')
    radecs = []
    i_prior = 0
    for i, arg in enumerate(run_arg.coordinates):
        try:
            if ',' in arg:
                radecs.append(string2deg(arg))
            else:
                try:
                    col_prior = run_arg.column_select_prior[i_prior]
                except TypeError:
                    col_prior = None
                radecs.extend(file2deg(arg, col_prior))
                i_prior += 1
        except argparse.ArgumentTypeError:
            parser.error('argument coordinates: problem occurs when parsing '
                         '{0:s}'.format(arg))
    coverage = check_coverage(radecs)
    if run_arg.table_output:
        print tprint(coverage)
    else:
        print pprint(coverage)
    print run_arg.download_dir
    if run_arg.download_dir:
        bulk_download_fits_images(coverage, dir_=run_arg.download_dir,
                                  filters=run_arg.download_bands,
                                  save_strategy=run_arg.save_strategy)
