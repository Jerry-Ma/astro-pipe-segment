astro-pipe-segment
==================

A set of convenient scripts that work as helpers (or, pipe segments)
in dealing with astronomical data (and reduction pipelines)

## gen_ds9reg.py

convert various ascii file (include sextractor-like ascii output)
to ds9 region file.

see more: `gen_ds9reg.py -h`

## imsel.sh

the script will take a coordinate list file, investigate a given
set of fits images,
return fits file name if the coordinate is covered. Cutouts can
be made on the fly if size is
specified, as well as a conditionally support for associated catalogue
`grep`.

see more: `imsel.sh -h`

## sexconv.py

convert sextractor-like ascii file to plain one. This is useful when
working with some black-boxed tool which requires a somehow more standard
tsv format.

## querysdss.py

A command-line interface to the SDSS SAS web portal.
It takes a varieties of forms (and any possible combination) of
coordinates, then,

* performs coverage check, and print output as designated format
* with download directory given (use -d), corresponding fits
  image will be downloaded.

Required package is missing:

* requests
* bs4

Solution (need to install pip first):

* pip install requests
* pip install beautifulsoup4

