#!/usr/bin/env python3

'''
Tools for bulk calculation of pair distribution functions from COD entries.
'''


import logging
import numbers
import numpy

# ----------------------------------------------------------------------------

class Calculator:

    @staticmethod
    def fromConfig(cfg):
        '''Create PDF calculator object from configuration dictionary.
        '''
        from diffpy.srreal import pdfcalculator
        mycfg = cfg.copy()
        calculatorclass = mycfg.pop('calculatorclass')
        klass = getattr(pdfcalculator, calculatorclass)
        calc = klass()
        # version
        calculatorversion = mycfg.pop('calculatorversion', {})
        # configure contained objects
        subobjs = [(n, v) for n, v in mycfg.items()
                   if n == 'envelopes' or isinstance(v, str)]
        dbattrs = [(n, v) for n, v in mycfg.items()
                   if isinstance(v, numbers.Number)]
        for n, v in subobjs + dbattrs:
            setattr(calc, n, v)
            mycfg.pop(n)
        if mycfg:
            unused = ', '.join(mycfg)
            logging.debug('unused configuration items %s', unused)
        return calc

# end of class Calculator

# Helper functions -----------------------------------------------------------

_GAUSS_SIGMA_TO_FWHM = 2 * numpy.sqrt(2 * numpy.log(2))

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
