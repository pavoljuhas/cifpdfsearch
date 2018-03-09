#!/usr/bin/env python3

__all__ = ['cifid', 'cifdocument', 'genjson', 'walkjson',
           'jload', 'datapath', 'cifpath']

import json
import os.path

from ciflastic.cifdocument import cifid, cifdocument
from ciflastic._utils import genjson, walkjson


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
    """
    from ciflastic.config import CODDIR
    if isinstance(codid, int):
        if not 1000000 <= codid <= 9999999:
            raise ValueError('codid must be a 7-digit integer')
        scid = str(codid)
    elif len(codid) == 7 and codid.isdigit():
        scid = codid
    else:
        s1 = ''.join(c if c.isdigit() else ' ' for c in codid)
        segs = [w for w in s1.split() if len(w) == 7]
        if not segs:
            emsg = 'Could not find 7-digit segment in {}'.format(codid)
            raise ValueError(emsg)
        scid = segs[-1]
    assert len(scid) == 7
    parts = ['cif', scid[0], scid[1:3], scid[3:5], scid + '.cif']
    rv = os.path.join(CODDIR, *parts)
    return rv


_MYDIR = os.path.abspath(__path__[0])
_DATADIR = os.path.normpath(os.path.join(_MYDIR, '../..'))
