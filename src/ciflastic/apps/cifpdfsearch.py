#!/usr/bin/env python3

'''
Calculate correlation coefficients between given PDFs and COD simulations.
'''

import os.path
import argparse
import numpy

from ciflastic.config import PDFSTORAGE
from ciflastic.cifpdf import HDFStorage
from ciflastic.cifpdf import RAWStorage
from ciflastic import normcodid
from diffpy.pdfgetx import loaddata

RAWSTORE = os.path.splitext(PDFSTORAGE)[0] + '-raw.yml'
ELASTICHOST = ['provexray.csi.bnl.gov']

dspdfpath = 'pdfc/cod{:0>7}'


parser = argparse.ArgumentParser(description=__doc__.strip())
parser.add_argument('--store', choices=['raw', 'hdf'], default='hdf',
                    help="storage backend for calculated PDFs")
parser.add_argument('--rmin', type=float,
                    help="lower bound for evaluating correlation coefficient")
parser.add_argument('--rmax', type=float,
                    help="upper bound for evaluating correlation coefficient")
parser.add_argument('--ccmin', type=float, default=-1.0,
                    help="minimum correlation value for a COD match")
parser.add_argument('-t', '--tolerance', type=float, default=0.0,
                    help="tolerance on normalized stoichiometry, e.g., 0.1")
parser.add_argument('-s', '--sort', action='store_true',
                    help="sort the output by correlation coefficient in "
                    "descending order")
parser.add_argument('searchpdf', help="PDF data to be matched with COD PDFs, "
                    'a two-column text file with (r, g) values.  '
                    'When "cod:ID" use PDF simulation for the COD ID entry.')
parser.add_argument('composition', nargs='*', help='limit search to specified '
                    'normalized composition, for example "Na 0.5 Cl 0.5"')

def genidpdf_all_hdf(hfile):
    grp = hfile['pdfc']
    for n, v in grp.items():
        yield normcodid(n), v[()]
    pass


def genidpdf_composition_hdf(hfile, composition, tolerance):
    genids = codsearch_composition(composition, tolerance)
    for codid in genids:
        ds = hfile.get(dspdfpath.format(codid))
        if ds is not None:
            yield codid, ds[()]
    pass


def genidpdf_all_raw(store):
    return store.items()


def genidpdf_composition_raw(store, composition, tolerance):
    genids = codsearch_composition(composition, tolerance)
    for codid in genids:
        try:
            ds = store.readPDF(codid)[1]
            yield codid, ds
        except KeyError:
            pass
    pass


def codsearch_composition(composition, tolerance):
    from diffpy.pdfgetx.functs import composition_analysis
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import scan
    es = Elasticsearch(ELASTICHOST)
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


def correlation(robs, gobs, rcod, gcod, bounds):
    clo = bounds['clo']
    chi = bounds['chi']
    r1 = rcod[clo:chi]
    gcod1 = gcod[clo:chi]
    gobs1 = numpy.interp(r1, robs, gobs)
    rv = numpy.corrcoef(gobs1, gcod1)[0, 1]
    return rv


class FastCorrelation:

    def __init__(self, robs, gobs, rcod, rmin=None, rmax=None):
        eps = 1e-5
        b = calcbounds(robs, rcod, rmin, rmax)
        iobs = numpy.round(robs / 0.01).astype(int)
        icod = numpy.round(rcod / 0.01).astype(int)
        assert numpy.all(numpy.abs(robs - iobs * 0.01) < eps)
        assert numpy.all(numpy.abs(rcod - icod * 0.01) < eps)
        icomm, jj, kk = numpy.intersect1d(
            icod[b['clo']:b['chi']], iobs, return_indices=True)
        self.robs1 = robs[kk]
        self.gobs1 = gobs[kk]
        csel = jj + b['clo']
        if len(csel) == len(rcod):
            csel = slice()
        elif len(set(numpy.diff(csel))) == 1:
            csel = slice(csel[0], csel[-1] + 1, csel[1] - csel[0])
        assert numpy.allclose(rcod[csel], self.robs1)
        self.csel = csel
        dtp = self.gobs1.dtype.type
        self.rn = rn = dtp(1.0 / len(self.gobs1))
        self.s1gobs = self.gobs1.sum()
        self.den_gobs = (self.gobs1.dot(self.gobs1) -
                         rn * self.s1gobs * self.s1gobs)
        return


    def __call__(self, gcod):
        gcod1 = gcod[self.csel]
        s1gcod = gcod1.sum()
        s2gcod = gcod1.dot(gcod1)
        nom = self.gobs1.dot(gcod1) - s1gcod * self.s1gobs * self.rn
        den_gcod = s2gcod - s1gcod * s1gcod * self.rn
        rv = nom / numpy.sqrt(self.den_gobs * den_gcod)
        return rv


def calcbounds(robs, rcod, rmin=None, rmax=None):
    """
    Calculate bounds and overlap indices for given rmin, rmax

    Return
    ------
    dict
    """
    eps = 1e-5
    lb = max(robs[0], rcod[0])
    if rmin is not None:
        lb = max(rmin, lb)
    ub = min(robs[-1], rcod[-1])
    if rmax is not None:
        ub = min(ub, rmax)
    rstep = rcod[1] - rcod[0]
    clo = int((lb + eps) // rstep)
    chi = int(round(ub / rstep))
    rv = dict(clo=clo, chi=chi, rmin=rcod[clo], rmax=rcod[chi])
    return rv


def main():
    from functools import partial
    pargs = parser.parse_args()
    composition = ' '.join(pargs.composition)
    # resolve storage backend
    if pargs.store == 'hdf':
        hdb = HDFStorage(PDFSTORAGE)
        rcod = hdb.rgrid
        readpdf = hdb.readPDF
        hfile = hdb._openhdf('r')
        genidpdf_all = partial(genidpdf_all_hdf, hfile)
        genidpdf_composition = partial(genidpdf_composition_hdf, hfile)
    elif pargs.store == 'raw':
        store = RAWStorage(RAWSTORE)
        rcod = store.rgrid
        readpdf = store.readPDF
        genidpdf_all = partial(genidpdf_all_raw, store)
        genidpdf_composition = partial(genidpdf_composition_raw, store)
    # load observed PDF data to be matched with COD PDFs
    if pargs.searchpdf.startswith('cod:'):
        robs, gobs = readpdf(pargs.searchpdf[4:])
    else:
        robs, gobs = loaddata(pargs.searchpdf, usecols=(0, 1),
                              dtype=rcod.dtype, unpack=True)
    # determine the actual bounds used and the rcod slice
    bounds = calcbounds(robs, rcod, rmin=pargs.rmin, rmax=pargs.rmax)
    fastcorrcoef = FastCorrelation(robs, gobs, rcod,
                                   rmin=pargs.rmin, rmax=pargs.rmax)
    # print out the header
    print("#T ciflastic.apps.cifpdfsearch")
    print("#C searchpdf =", os.path.basename(pargs.searchpdf))
    print("#C composition =", composition or '*')
    print("#C tolerance =", pargs.tolerance)
    print("#C ccmin =", pargs.ccmin)
    print("#C rmin =", bounds['rmin'])
    print("#C rmax =", bounds['rmax'])
    print("#S 1")
    print("#L codid  correlation")
    # generate correlation coefficients
    has_composition = composition and composition != '*'
    gpdfs = (genidpdf_composition(composition, pargs.tolerance)
             if has_composition else genidpdf_all())
    gcorr = ((codid, fastcorrcoef(gcod))
             for codid, gcod in gpdfs if gcod.any())
    gcorr1 = (gcorr if pargs.ccmin <= -1 else
              (xx for xx in gcorr if xx[1] >= pargs.ccmin))
    gout = gcorr1
    if pargs.sort:
        gout = sorted(gout, key=lambda x: x[1], reverse=True)
    fmt = '{:g}'.format
    for codid, cc in gout:
        print(codid, fmt(cc))
    return


if __name__ == '__main__':
    main()
