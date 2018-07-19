#!/usr/bin/env python3

'''
Calculate correlation coefficients between given PDFs and COD simulations.
'''

import os.path
import argparse
import numpy
import h5py

from ciflastic.config import PDFSTORAGE
from ciflastic.cifpdf import HDFStorage
from ciflastic import normcodid
from diffpy.pdfgetx import loaddata

dspdfpath = 'pdfc/cod{:0>7}'


parser = argparse.ArgumentParser(description=__doc__.strip())
parser.add_argument('-c', '--composition',
                    help='normalized chemical composition to limit checked '
                    'PDFs, for example "Na0.5"')
parser.add_argument('-t', '--tolerance', type=float, default=0.0,
                    help="tolerance on normalized stoichiometry, e.g., 0.1")
parser.add_argument('-s', '--sort', action='store_true',
                    help="sort the output by correlation coefficient in "
                         "descending order")
parser.add_argument('searchpdf', help="PDF data to be matched with COD PDFs, "
                    'a two-column text file with (r, g) values.  '
                    'When "cod:ID" use PDF simulation for the COD ID entry.')


def genidpdf_all(hfile):
    grp = hfile['pdfc']
    for n, v in grp.items():
        yield normcodid(n), v.value
    pass


def codsearch_composition(composition, tolerance):
    from diffpy.pdfgetx.functs import composition_analysis
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import scan
    es = Elasticsearch(['provexray.csi.bnl.gov'])
    smbls, counts = composition_analysis(composition)
    if tolerance == 0:
        mustterms = [{'term': {("composition." + s): c}}
                     for s, c in zip(smbls, counts)]
        q = {"bool": {"must": mustterms}}
    else:
        rangeterms = [
            {
                'range': {
                    ("composition." + s): {
                        "gte": c - tolerance,
                        "lte": c + tolerance,
                    }
                }
            } for s, c in zip(smbls, counts)]
        q = {"bool": {"must": rangeterms}}
    gscan = scan(es, query={'query': q},
                 index='cod', doc_type='cif', _source=False)
    for e in gscan:
        codid = normcodid(e['_id'])
        yield codid
    pass


def genidpdf_composition(hfile, composition, tolerance):
    genids = codsearch_composition(composition, tolerance)
    for codid in genids:
        ds = hfile.get(dspdfpath.format(codid))
        if ds is not None:
            yield codid, ds.value
    pass


def correlation(robs, gobs, rcod, gcod):
    eps = 1e-7
    ub = max(robs[0], rcod[0])
    lb = min(robs[-1], rcod[-1])
    rstep = rcod[1] - rcod[0]
    clo = int(round(ub / rstep))
    chi = int((lb + eps) // rstep)
    r1 = rcod[clo:chi]
    gcod1 = gcod[clo:chi]
    gobs1 = numpy.interp(r1, robs, gobs)
    rv = numpy.corrcoef(gobs1, gcod1)[0, 1]
    return rv


def main():
    pargs = parser.parse_args()
    print("# ciflastic.apps.corrcodpdfs")
    print("# searchpdf =", os.path.basename(pargs.searchpdf))
    print("# composition =", pargs.composition or 'any')
    print("# tolerance =", pargs.tolerance)
    print("#S 1")
    print("#L codid  correlation")
    # load searchpdf
    hdb = HDFStorage(PDFSTORAGE)
    if pargs.searchpdf.startswith('cod:'):
        robs, gobs = hdb.readPDF(pargs.searchpdf[4:])
    else:
        robs, gobs = loaddata(pargs.searchpdf, usecols=(0, 1),
                              dtype=hdb.dtype, unpack=True)
    # create generator of COD IDs and PDF curves
    rcod = hdb.rgrid
    getall = (pargs.composition is None or pargs.composition.lower() == 'any')
    hfile = h5py.File(PDFSTORAGE, mode='r')
    gpdfs = (genidpdf_all(hfile) if getall
             else genidpdf_composition(hfile, pargs.composition,
                                       pargs.tolerance))
    gcorr = ((codid, correlation(robs, gobs, rcod, gcod))
             for codid, gcod in gpdfs if gcod.any())
    gout = sorted(gcorr, key=lambda x: -x[1]) if pargs.sort else gcorr
    for codid, cc in gout:
        print(codid, cc)
    return


if __name__ == '__main__':
    main()
