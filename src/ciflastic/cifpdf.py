#!/usr/bin/env python3

'''
Tools for bulk calculation of pair distribution functions from COD entries.
'''


import os.path
import logging
import math

from ciflastic import normcodid

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

    def __init__(self, filename, mode=None):
        from h5py import File
        self.filename = os.path.abspath(filename)
        self.hfile = File(filename, mode=mode)
        self._rgrid = None
        return


    def writeConfig(self, calc):
        from ciflastic._utils import h5writejson
        self.hfile.pop(self._gconfigcalc, None)
        group = self.hfile.create_group(self._gconfigcalc)
        cfg = calculator.toConfig(calc)
        h5writejson(group, cfg)
        r = calc.rgrid
        if not self._dsrgridpath in self.hfile:
            self.hfile.create_dataset(self._dsrgridpath, shape=r.shape,
                                      maxshape=(None,), dtype=self.dtype)
        rds = self.hfile[self._dsrgridpath]
        rds.resize(r.shape)
        rds[()] = r
        return


    def writePDF(self, codid, r, g):
        if not self._dsrgridpath in self.hfile:
            rds = self.hfile.require_dataset(
                self._dsrgridpath, shape=r.shape, dtype=self.dtype)
            rds[:] = r
        scid = normcodid(codid)
        nm = self._dspdfpath.format(scid)
        ds = self.hfile.require_dataset(nm, shape=g.shape, dtype=self.dtype)
        ds[:] = g
        return


    def readPDF(self, codid):
        scid = normcodid(codid)
        dsname = self._dspdfpath.format(scid)
        rv = (self.rgrid, self.hfile[dsname].value)
        return rv


    @property
    def rgrid(self):
        if self._rgrid is None:
            self._rgrid = self.hfile[self._dsrgridpath][:]
        return self._rgrid

# end of class HDFStorage

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
