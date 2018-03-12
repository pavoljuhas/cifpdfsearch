#!/usr/bin/env python3

'''Create single-entry for nickel CIF data.
'''

import sys
import os.path
import numpy
from ciflastic import config, cifpdf
from pyobjcryst import loadCrystal

pdfc = cifpdf.calculator.fromConfig(config.PDFCALCULATOR)

def main(ciflist):
    with open(ciflist) as fp:
        allcifs = [line.strip() for line in fp]
    rncifs = [allcifs[i] for i in numpy.random.permutation(len(allcifs))]
    for cf in rncifs:
        fb = os.path.basename(cf)
        nm = ''.join(c for c in fb if c.isdigit())
        out = os.path.join(config.PDFSTORAGE, 'cod' + nm + '.npy')
        if os.path.isfile(out):
            continue
        # create the file
        open(out, 'w').close()
        try:
            crst = loadCrystal(cf)
        except:
            continue
        r, g = pdfc(crst)
        numpy.save(out, g.astype(numpy.float32))
    return


if __name__ == '__main__':
    main(sys.argv[1])
