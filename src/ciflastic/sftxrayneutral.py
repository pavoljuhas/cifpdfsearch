#!/usr/bin/env python3

"""
Define class SFTXrayNeutral which ignores ionic charge in atom types.

The class always returns scattering factors for non-ionized elements.
"""

import copy

from diffpy.srreal.scatteringfactortable import ScatteringFactorTable
from diffpy.srreal.scatteringfactortable import SFTXray


class SFTXrayNeutral(ScatteringFactorTable):
    """
    Lookup x-ray scattering factors of bare elements.
    """

    __sftxray = SFTXray()

    def create(self):
        return SFTXrayNeutral()

    def clone(self):
        return copy.copy(self)

    def type(self):
        return "xrayneutral"

    def radiationType(self):
        return "XNEUTRAL"

    def _sfwater(self, q):
        fh = self.__sftxray._standardLookup("H", q)
        fo = self.__sftxray._standardLookup("O", q)
        return 2 * fh + fo

    def _standardLookup(self, smbl, q):
        smblbare = smbl.rstrip('+-012345678')
        if smblbare == 'D':
            rv = self._standardLookup('H', q)
        elif smblbare == 'Wa':
            rv = self._sfwater(q)
        else:
            rv = self.__sftxray._standardLookup(smblbare, q)
        return rv

# end of class SFTXrayNeutral


_sftb = SFTXrayNeutral()
ScatteringFactorTable._deregisterType(_sftb.type())
_sftb._registerThisType()
del _sftb
