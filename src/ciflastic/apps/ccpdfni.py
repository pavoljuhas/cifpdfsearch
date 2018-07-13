#!/usr/bin/env python3

'''Evaluate correlation coefficient of Ni-9008476.cif PDF with all others.
'''

import numpy
import h5py

from ciflastic.config import PDFSTORAGE
from ciflastic import normcodid

dspdfpath = 'pdfc/cod{:0>7}'
codnickel = 9008476
with h5py.File(PDFSTORAGE, 'r') as hfile:
    gni = hfile[dspdfpath.format(codnickel)].value


def ccvisit(name, ds):
    cid = normcodid(name)
    ds = ds.value
    if not ds.any():
        return
    ccni = numpy.corrcoef(gni, ds)[0, 1]
    print(cid, ccni)
    return


def main():
    global hfile
    print("#C PDF correlation to Ni-{}".format(codnickel))
    print("# codid  corr".format(codnickel))
    hfile = h5py.File(PDFSTORAGE, 'r')
    hfile['pdfc'].visititems(ccvisit)
    hfile.close()
    return


if __name__ == '__main__':
    main()
