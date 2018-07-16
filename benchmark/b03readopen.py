#!/usr/bin/env python

'''
Load all PDFs using getitem on an open h5py File.
'''

import os.path
import time
import argparse

import numpy
import h5py

from ciflastic.config import PDFSTORAGE


parser = argparse.ArgumentParser(usage="%(prog)s [options] [count]")
parser.add_argument('count', type=int, nargs='?')

pargs = parser.parse_args()

pdfindexfile = os.path.splitext(PDFSTORAGE)[0] + '.idx'
pdfids = numpy.loadtxt(pdfindexfile, dtype=int)
dspdfpath = 'pdfc/cod{:0>7}'
hfile = h5py.File(PDFSTORAGE, mode='r')

cnt = 0
total = 0

t0 = time.time()
for codid in pdfids[:pargs.count]:
    g = hfile[dspdfpath.format(codid)].value
    cnt += 1
    total += g.sum()
t1 = time.time()

print("elapsed time:", t1 - t0, "seconds")
print("PDF count:", cnt)
print("PDF total:", total)
