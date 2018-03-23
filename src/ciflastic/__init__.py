#!/usr/bin/env python3

__all__ = ['cifid', 'cifdocument', 'genjson', 'walkjson',
           'jload', 'datapath', 'cifpath']

import json
import os.path

from ciflastic.cifdocument import cifid, cifdocument
from ciflastic._utils import genjson, walkjson, normcodid


def jload(filename):
    '''Load JSON document from the specified file.
    '''
    with open(filename) as fp:
        rv = json.load(fp)
    return rv


def datapath(basename):
    """Return absolute path to data files root in ciflastic.
    """
    return os.path.join(_DATADIR, basename)


def cifpath(codid):
    """Absolute path to a CIF file from Crystallography Open Database.

    Parameters
    ----------
    codid : int or str
        COD database code for the CIF file.  When `str` use the
        last sequence of exactly 7 digits.

    Returns
    -------
    str
        Absolute path to the CIF file.

    Raises
    ------
    ValueError
        When codid has invalid range.
    TypeError
        When codid is of unsupported type.
    """
    from ciflastic.config import CODDIR
    scid = normcodid(codid)
    parts = ['cif', scid[0], scid[1:3], scid[3:5], scid + '.cif']
    rv = os.path.join(CODDIR, *parts)
    return rv


_MYDIR = os.path.abspath(__path__[0])
_DATADIR = os.path.normpath(os.path.join(_MYDIR, '../..'))
