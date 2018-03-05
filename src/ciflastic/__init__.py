#!/usr/bin/env python3

__all__ = ['cifid', 'cifdocument', 'genjson', 'jload', 'cfpath']

import json
import os.path

from ciflastic.cifdocument import cifid, cifdocument
from ciflastic._utils import genjson


def jload(filename):
    '''Load JSON document from the specified file.
    '''
    with open(filename) as fp:
        rv = json.load(fp)
    return rv


def cfpath(basename):
    """Return absolute path to data files root in ciflastic.
    """
    return os.path.join(_DATADIR, basename)


_MYDIR = os.path.abspath(__path__[0])
_DATADIR = os.path.normpath(os.path.join(_MYDIR, '../..'))
