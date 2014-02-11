astro-pipe-segment
==================

To down load the scripts, go to

Github page: [https://github.com/Jerry-Ma/astro-pipe-segment]()

A set of convenient scripts that work as helpers (or, pipe segments)
in dealing with astronomical data (and reduction pipelines)

##### Table of Contents

[gen_ds9reg.py](#gen_ds9reg.py)

[imsel.sh](#imsel.sh)

[querysdss.py](#querysdss.py)

[sexconv.py](#sexconv.py)

-------------------
## gen_ds9reg.py
link: [https://github.com/Jerry-Ma/astro-pipe-segment/blob/master/gen_ds9reg.py]()

It can convert various ascii file (include sextractor-like ascii output)
to ds9 region file.

see more: `gen_ds9reg.py -h`

## imsel.sh
link: [https://github.com/Jerry-Ma/astro-pipe-segment/blob/master/imsel.sh]()

The script will take a coordinate list file, investigate a given
set of fits images,
return fits file name if the coordinate is covered. Cutouts can
be made on the fly if size is
specified, as well as a conditionally support for associated catalogue
grep.

see more: `imsel.sh -h`

## querysdss.py
link: [https://github.com/Jerry-Ma/astro-pipe-segment/blob/master/querysdss.py]()

This is a command-line interface to the SDSS SAS web portal.
It takes a varieties of forms (and any possible combination) of
coordinates, then,

* performs coverage check, and print output as designated format
* with download directory given (use -d), corresponding fits
  image will be downloaded.

Required package is missing:

* requests
* bs4

Solution (need to install `python-pip` first):

* `pip install requests`
* `pip install beautifulsoup4`

## sexconv.py
link: [https://github.com/Jerry-Ma/astro-pipe-segment/blob/master/sexconv.py]()

It will convert sextractor-like ascii file to plain one. This is useful when
working with some black-boxed tool which requires a somehow more standard
tsv format.
