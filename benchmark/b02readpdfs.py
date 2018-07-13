#!/usr/bin/env python

'''
Load all PDFs using h5py visititems method.
'''

import os.path
import time
import argparse

import numpy

from ciflastic.config import PDFSTORAGE
from ciflastic.cifpdf import HDFStorage

parser = argparse.ArgumentParser(usage="%(prog)s [options] [count]")
parser.add_argument('count', type=int, nargs='?')

pargs = parser.parse_args()
hdb = HDFStorage(PDFSTORAGE)

pdfindexfile = os.path.splitext(PDFSTORAGE)[0] + '.idx'
pdfids = numpy.loadtxt(pdfindexfile, dtype=int)

cnt = 0
total = 0

t0 = time.time()
for codid in pdfids[:pargs.count]:
    r, g = hdb.readPDF(codid)
    cnt += 1
    total += g.sum()
t1 = time.time()

print("elapsed time:", t1 - t0, "seconds")
print("PDF count:", cnt)
print("PDF total:", total)
