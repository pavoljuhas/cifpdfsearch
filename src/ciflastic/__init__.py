#!/usr/bin/env python3

__all__ = ['cifid', 'cifdocument', 'jload', 'cfpath']

import json
import os.path

from ciflastic.cifdocument import cifid, cifdocument


def jload(filename):
    '''Load JSON document from the specified file.
    '''
    with open(filename) as fp:
        rv = json.load(fp)
    return rv


def cfpath(basename):
    """Return absolute path to standard files included in ciflastic.
    """
    return os.path.join(_DATADIR, basename)


_MYDIR = os.path.abspath(os.path.dirname(__file__))
_DATADIR = os.path.normpath(os.path.join(_MYDIR, '../../standards'))
