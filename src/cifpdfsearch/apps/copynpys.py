#!/usr/bin/env python3

'''Merge PDF results from individual .npy files into one h5 file.
'''

from __future__ import print_function

import os.path
import argparse
import numpy


parser = argparse.ArgumentParser(description=__doc__.strip())
parser.add_argument('-c', '--config', metavar='FILE',
                    help="Load the specified configuration file")
parser.add_argument('-o', '--output',
                    help="Output path to use instead of configuration value")
parser.add_argument('args', nargs='+', metavar='file',
                    help="npy files to be copied to the HDF 5 output.  "
                         "Replace '-' with files from standard input.")


def main(args):
    from cifpdfsearch.cifpdf import HDFStorage
    from cifpdfsearch import config, normcodid
    from cifpdfsearch._utils import getargswithstdin
    if args.config:
        config.initialize(args.config)
    npyfiles = list(getargswithstdin(args.args))
    filename = args.output if args.output is not None else config.PDFSTORAGE
    hdb = HDFStorage(filename)
    # TODO - add check for existing config in HDFStorage
    hdb.writeConfig(config.PDFCALCULATOR)
    r = hdb.rgrid
    progress_step = len(npyfiles) / (80.0 + 1)
    progress_next = 0
    for i, f in enumerate(npyfiles):
        if os.path.getsize(f) == 0:
            continue
        g = numpy.load(f)
        codid = normcodid(os.path.basename(f))
        hdb.writePDF(codid,r, g)
        if i >= progress_next:
            print('.', end='', flush=True)
            progress_next += progress_step
    print()
    return


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
