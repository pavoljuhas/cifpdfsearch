#!/usr/bin/env python3

'''Calculate PDFs for the specified CIF files.
'''

import sys
import os.path
import argparse
import numpy

parser = argparse.ArgumentParser(description=__doc__.strip())
parser.add_argument('-c', '--config', metavar='FILE',
                    help="Load the specified configuration file")
parser.add_argument('-f', '--force', action='store_true',
                    help="Overwrite existing result files.")
parser.add_argument('output',
                    help="Output directory for the npy files")
parser.add_argument('cifs', nargs='+',
                    help="CIF files for which to calculate PDFs. "
                         "Replace '-' with files from standard input.")


def calculate(pdfc, ciffile):
    from diffpy.structure import loadStructure
    lo = 0.5
    symeps = 0.001
    haszeropeak = lambda x: any(x[r < lo] > 0.01 * x.max())
    stru = loadStructure(ciffile, fmt='cif', eps=symeps)
    r, g = pdfc(stru)
    if haszeropeak(g):
        raise RuntimeError("contains near-zero peak")
    return r, g


def main(args):
    from ciflastic import config, cifpdf, normcodid
    from numpy.random import randint
    if args.config:
        config.initialize(args.config)
    if not os.path.isdir(args.output):
        emsg = "{} must be a directory".format(args.output)
        raise ValueError(emsg)
    ciflist = args.cifs
    if '-' in ciflist:
        strippedlines = (line.strip() for line in sys.stdin)
        extras = [a for a in strippedlines if a]
        idx = ciflist.index('-')
        ciflist = ciflist[:idx] + extras + ciflist[idx + 1:]
    pdfc = cifpdf.calculator.fromConfig(config.PDFCALCULATOR)
    while ciflist:
        cf = ciflist.pop(randint(len(ciflist)))
        codid = normcodid(cf)
        out = os.path.join(args.output, 'cod{}.npy'.format(codid))
        if not args.force and os.path.isfile(out):
            continue
        # create the file
        open(out, 'w').close()
        try:
            r, g = calculate(pdfc, cf)
        except Exception as e:
            print('{}: {} {}'.format(cf, type(e).__name__, e))
            continue
        numpy.save(out, g.astype(numpy.float32))
    return


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
