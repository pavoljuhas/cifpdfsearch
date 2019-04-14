#!/usr/bin/env python3

'''
Tools for bulk calculation of pair distribution functions from COD entries.
'''


import os.path
import logging
import math
import numpy
import yaml

from ciflastic import normcodid

# register SFTXrayNeutral lookup table
import ciflastic.sftxrayneutral
assert ciflastic.sftxrayneutral is not None

# ----------------------------------------------------------------------------

class calculator:

    _exclude = set(('slope',))

    @classmethod
    def fromConfig(cls, cfg):
        '''Create PDF calculator object from configuration dictionary.
        '''
        from diffpy.srreal import pdfcalculator
        from numbers import Number
        mycfg = cfg.copy()
        classname = mycfg.pop('class')
        klass = getattr(pdfcalculator, classname)
        calc = klass()
        # version
        cversion = mycfg.pop('version', {})
        assert cversion is not None
        # translate derived quantities
        if 'uisowidth' in mycfg:
            mycfg['width'] = uisotofwhm(mycfg.pop('uisowidth'))
        # configure contained objects
        subobjs = [(n, v) for n, v in mycfg.items()
                   if n == 'envelopes' or isinstance(v, str)]
        dbattrs = [(n, v) for n, v in mycfg.items()
                   if isinstance(v, Number) and not n in cls._exclude]
        for n, v in subobjs + dbattrs:
            setattr(calc, n, v)
            mycfg.pop(n)
        if mycfg:
            unused = ', '.join(mycfg)
            logging.debug('unused configuration items %s', unused)
        return calc


    @classmethod
    def toConfig(cls, calc):
        '''Return configuration dictionary for PDF calculator object.
        '''
        from diffpy.srreal import version as ver
        typedattrs = ['baseline', 'peakprofile',
                      'peakwidthmodel', 'scatteringfactortable']
        cfg = {}
        classname = type(calc).__name__
        if not classname in ('PDFCalculator', 'DebyePDFCalculator'):
            emsg = "Invalid calculator type {}".format(type(calc))
            raise TypeError(emsg)
        cfg['class'] = classname
        cfg['version'] = dict([
            ('diffpy.srreal', ver.__version__),
            ('libdiffpy', ver.libdiffpy_version_info.version),
        ])
        tpattrs = [n for n in typedattrs if hasattr(calc, n)]
        tptypes = [getattr(calc, n).type() for n in tpattrs]
        cfg.update(zip(tpattrs, tptypes))
        cfg['envelopes'] = list(calc.usedenvelopetypes)
        cfg['evaluatortype'] = calc.evaluatortype
        dbattrs = (n for n in calc._namesOfWritableDoubleAttributes()
                   if not n in cls._exclude)
        for n in dbattrs:
            cfg[n] = getattr(calc, n)
        if cfg['peakwidthmodel'] == 'constant':
            cfg['uisowidth'] = fwhmtouiso(cfg.pop('width'))
        return cfg

# end of class calculator

# ----------------------------------------------------------------------------

class HDFStorage:

    _gconfigcalc = 'config/pdfcalculator'
    _dsrgridpath = 'common/rgrid'
    _dspdfpath = 'pdfc/cod{:0>7}'
    dtype = 'float32'

    def __init__(self, filename):
        self.filename = os.path.abspath(filename)
        self._rgrid = None
        return


    def writeConfig(self, cfg):
        from ciflastic._utils import h5writejson
        calc = calculator.fromConfig(cfg)
        with self._openhdf('a') as hfile:
            hfile.pop(self._gconfigcalc, None)
            group = hfile.create_group(self._gconfigcalc)
            h5writejson(group, cfg)
            r = calc.rgrid
            if not self._dsrgridpath in hfile:
                hfile.create_dataset(self._dsrgridpath, shape=r.shape,
                                     maxshape=(None,), dtype=self.dtype)
            rds = hfile[self._dsrgridpath]
            rds.resize(r.shape)
            rds[()] = r
        self._rgrid = None
        return


    def writePDF(self, codid, r, g):
        from numpy import allclose
        if r.shape != self.rgrid.shape or not allclose(r, self.rgrid):
            emsg = "r must equal the {} dataset".format(self._dsrgridpath)
            raise ValueError(emsg)
        scid = normcodid(codid)
        nm = self._dspdfpath.format(scid)
        with self._openhdf('a') as hfile:
            ds = hfile.require_dataset(nm, shape=g.shape, dtype=self.dtype)
            ds[:] = g
        return


    def readPDF(self, codid):
        scid = normcodid(codid)
        dsname = self._dspdfpath.format(scid)
        with self._openhdf('r') as hfile:
            g = hfile[dsname][()]
        rv = (self.rgrid, g)
        return rv


    @property
    def rgrid(self):
        if self._rgrid is None:
            with self._openhdf('r') as hfile:
                self._rgrid = hfile[self._dsrgridpath][:]
        return self._rgrid


    def _openhdf(self, mode):
        import h5py
        return h5py.File(self.filename, mode)

# end of class HDFStorage

# ----------------------------------------------------------------------------

class RAWStorage:

    def __init__(self, filename):
        b, e = os.path.splitext(filename)
        f = filename
        if e != '.yml':
            f = b + '.yml'
        with open(f) as fp:
            cfg = yaml.safe_load(fp)
        f = os.path.abspath(f)
        b, _ = os.path.splitext(f)
        codids = numpy.fromfile(b + '.idx', dtype='int32')
        index = {c: i for i, c in enumerate(codids)}
        mcfg = cfg['memmap']
        pcfg = cfg['pdfcalculator']
        gdata = numpy.memmap(b + '.bin', mode='r', dtype=mcfg['dtype'])
        gdata = gdata.reshape(mcfg['shape'])
        rgrid = numpy.arange(pcfg['rmin'], pcfg['rmax'], pcfg['rstep'],
                             dtype=mcfg['dtype'])
        assert len(rgrid) == gdata.shape[1]
        # all good here - let us assign all attributes
        self.filename = os.path.abspath(f)
        self.codids = codids
        self.index = index
        self.gdata = gdata
        self.rgrid = rgrid
        self.dtype = rgrid.dtype
        return


    def writeConfig(self, cfg):
        raise NotImplementedError


    def writePDF(self, codid, r, g):
        raise NotImplementedError


    def readPDF(self, codid):
        cid = codid
        if isinstance(cid, str):
            cid = int(normcodid(cid))
        row = self.index[cid]
        g = self.gdata[row]
        rv = (self.rgrid, g)
        return rv


    def items(self):
        rv = zip(self.codids, self.gdata)
        return rv

# end of class RAWStorage

# Helper functions -----------------------------------------------------------

_GAUSS_SIGMA_TO_FWHM = 2 * math.sqrt(2 * math.log(2))

def uisotofwhm(uiso):
    """Return FWHM for a pair of atoms with equal Uiso displacements.

    Full width at half maximum of a Gaussian in radial distribution function.

    Parameters
    ----------
    uiso : float
        The isotropic displacement parameter in A**2 for every atom site.

    Returns
    -------
    fwhm : float
        Full width at half maximum in A.
    """
    fwhm = _GAUSS_SIGMA_TO_FWHM * ((2 * uiso) ** 0.5)
    return fwhm


def fwhmtouiso(fwhm):
    """Return uniform displacement parameter corresponding to FWHM.

    Calculate isotropic displacements that would produce Gaussian peak
    of the specified full width at half maximum.

    Parameters
    ----------
    fwhm : float
        Full width at half maximum of a Gaussian peak in A.


    Returns
    -------
    uiso : float
        The uniform isotropic displacement parameter in A**2.
    """
    rmsd = fwhm / _GAUSS_SIGMA_TO_FWHM
    uiso = 0.5 * rmsd ** 2
    return uiso
