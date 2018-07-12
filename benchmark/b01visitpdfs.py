#!/usr/bin/env python

'''
Load all PDFs using h5py visititems method.
'''

import time
from ciflastic.config import PDFSTORAGE
from h5py import File

class VCounter:
    cnt = 0
    total = 0
    def __call__(self, name, dataset):
        self.cnt += 1
        self.total += dataset.value.sum()
        return

v = VCounter()

t0 = time.time()
hfp = File(PDFSTORAGE, 'r')
hfp['pdfc'].visititems(v)
t1 = time.time()

print("elapsed time:", t1 - t0, "seconds")
print("PDF count:", v.cnt)
print("PDF total:", v.total)
