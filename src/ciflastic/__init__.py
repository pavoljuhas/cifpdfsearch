#!/usr/bin/env python3

__all__ = ['cifid', 'cifdocument', 'genjson', 'walkjson',
           'jload', 'datapath', 'cifpath', 'APPDATADIR']

import json
import os.path
from pkg_resources import Requirement, resource_filename

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
    return os.path.join(APPDATADIR, basename)


def cifpath(codid):
    """Absolute path to a CIF file from Crystallography Open Database.

    Parameters
    ----------
    codid : int or str
        COD database code for the CIF file or CIF basename.  When CIF
        basename use the last sequence of exactly 7 digits.

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
    # handle non-id strings as CIF filenames
    if isinstance(codid, str):
        bn = os.path.basename(codid)
        scid = normcodid(bn)
    else:
        scid = normcodid(codid)
    parts = ['cif', scid[0], scid[1:3], scid[3:5], scid + '.cif']
    rv = os.path.join(CODDIR, *parts)
    return rv


def gencifpaths():
    """Generate absolute paths to CIFs from Crystallography Open Database.

    Yields
    ------
    str
        Absolute paths to CIF files in the local COD database.
    """
    from ciflastic.config import CODDIR
    top = os.path.join(CODDIR, 'cif')
    for root, dirnames, filenames in os.walk(top):
        if root == top:
            dirnames[:] = [d for d in dirnames if len(d) == 1 and d.isdigit()]
            dirnames.sort()
            continue
        dirnames.sort()
        filenames.sort()
        for f in filenames:
            if f.endswith('.cif'):
                yield os.path.join(root, f)
    pass

# ----------------------------------------------------------------------------

# Resolve APPDATADIR base path to the application data files.
_upbasedir = os.path.normpath(resource_filename(__name__, '..'))
_development_mode = (
    os.path.basename(_upbasedir) == "src" and
    os.path.isfile(os.path.join(_upbasedir, "../setup.py"))
)

# Requirement must have egg-info.  Do not use in _development_mode.
_req = Requirement.parse("ciflastic")
APPDATADIR = (os.path.dirname(_upbasedir) if _development_mode
              else resource_filename(_req, ""))
APPDATADIR = os.path.abspath(APPDATADIR)

del _upbasedir
del _development_mode
del _req
