#!/usr/bin/env python3

"""Internal helper functions.
"""

import sys


def grouper(iterable, n, *fillvalue):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    from itertools import islice
    ii = iter(iterable)
    for x in ii:
        grp = (x,) + tuple(islice(ii, n - 1))
        if fillvalue and len(grp) < n:
            grp += (n - len(grp)) * (fillvalue[0],)
        yield grp
    pass


def tofloat(s):
    """Extract floating point value from a CIF-formatted entry.

    Parameters
    ----------
    s : str
        The value string from a CIF file.  It may contain an
        uncertainty in attached parentheses, which is ignored.

    Returns
    -------
    value : float or None
        The converted floating point value.  Return `NaN` for
        "." and `None` for "?", which stand for inapplicable
        and missing values.
    """
    pidx = s.find('(')
    end = None if pidx < 0 else pidx
    sbare = s[:end].strip()
    if sbare == '.':
        rv = float('NaN')
    elif sbare == '?':
        rv = None
    else:
        rv = float(sbare)
    return rv


def normcodid(codid):
    """Return COD identifier as 7-digit string.

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
    if isinstance(codid, int):
        if not 1000000 <= codid <= 9999999:
            raise ValueError('codid must be a 7-digit integer')
        scid = str(codid)
    elif isinstance(codid, str):
        scid = codid
        if len(codid) != 7 or not codid.isdigit():
            s1 = ''.join(c if c.isdigit() else ' ' for c in codid)
            segs = [w for w in s1.split() if len(w) == 7]
            if not segs:
                emsg = 'Could not find 7-digit segment in {}'.format(codid)
                raise ValueError(emsg)
            scid = segs[-1]
    assert len(scid) == 7
    return scid


def genjson(fp=None, filename=None, bufsize=262144, maxbufsize=None):
    """Generate JSON entries from a file-like object.

    Parameters
    ----------
    fp : file, optional
        A file-like object with a sequence of JSON entries.
    filename : str, optional
        Path to a file with JSON entries.  The `filename` and
        `fp` arguments are mutually exclusive; only one of
        them must be provided.
    bufsize : int, optional
        Size of the buffer to be read from the file for decoding.
        When decoding fails, the buffer is enlarged up to `maxbufsize`
        or until the whole file is consumed.
    maxbufsize : int, optional
        Maximum allowed size of the internal read buffer.  When specified,
        each JSON entry must be shorter than that.

    Returns
    -------
    generator
        The generator of JSON entries.

    Raises
    ------
    JSONDecodeError
        When JSON decoding fails or if some entry exceeds `maxbufsize`.
    """
    from json import JSONDecoder
    if fp is None and filename is None:
        raise TypeError("must have either 'fp' or 'filename' arguments")
    if fp is not None and filename is not None:
        raise TypeError("cannot use both 'fp' and 'filename' arguments")
    if filename is not None:
        kw = {'bufsize' : bufsize, 'maxbufsize' : maxbufsize}
        with open(filename) as fp1:
            for jobj in genjson(fp=fp1, **kw):
                yield jobj
        return
    # here we have file-like object in fp
    maxbuflen = sys.maxsize if maxbufsize is None else maxbufsize
    decoder = JSONDecoder()
    buf = ''
    while True:
        chunk = fp.read(bufsize)
        buf += chunk
        # end of file after processing last entry
        if buf == '':
            break
        try:
            jobj, i = decoder.raw_decode(buf)
        except ValueError:
            if chunk == '':
                raise
            if len(buf) > maxbuflen:
                raise
            continue
        buf = buf[i:].lstrip()
        yield jobj
    return


def safecall(f, default=None):
    """Function wrapper that returns fallback value on exception.
    """
    from functools import wraps
    _last = {}
    @wraps(f)
    def wrapper(*args, **kwds):
        signature = args + tuple(sorted(kwds.items()))
        if _last and _last['signature'] == signature:
            return _last['value']
        rv = default
        try:
            rv = f(*args, **kwds)
            _last.update(signature=signature, value=rv)
        except (ValueError, TypeError):
            pass
        return rv
    return wrapper


def h5writejson(group, cfg):
    """Write json-like object into a given HDF5 group.

    Create an equivalent hierarchy of HDF5 Group objects
    anchored in the `group`.  The types of collection objects
    are saved in the "type" attribute of HDF5 groups.

    Parameters
    ----------
    group : h5py.Group
        The HDF5 group object where to write the json-like object.
    cfg : dict, list, tuple
        The JSON-like hierarchical object to be saved.
    """
    from numpy import string_
    from itertools import accumulate
    from operator import getitem
    def _assign_type(gtop, gpath):
        if 'type' in gtop.attrs:
            return
        owners = list(accumulate((cfg,) + gpath, getitem))
        for owner in reversed(owners):
            gtop.attrs['type'] = string_(type(owner).__name__)
            gtop = gtop.parent
            if 'type' in gtop.attrs:
                break
        return
    for path, value in walkjson(cfg):
        dname = '/'.join(str(p) for p in path)
        group[dname] = value
        _assign_type(group[dname].parent, path[:-1])
    return


def walkjson(obj):
    """Generate index-paths and values from a json-like hierarchy.

    Parameters
    ----------
    obj : dict, list, tuple or other object

    Yields
    ------
    tuple
        A tuple of (indexpath, value), where `indexpath` is a sequence
        of indices which return `value` when applied to the `obj`.
        The `indexpath` is an empty tuple when walking scalar object.
    """
    return _walkjsonpath(obj, path=())


def _walkjsonpath(obj, path):
    "Implementation of walkjson"
    if isinstance(obj, (list, tuple)):
        gen = enumerate(obj)
    elif isinstance(obj, dict):
        gen = obj.items()
    else:
        yield obj, path
        return
    for key, value in gen:
        p1 = path + (key,)
        if isinstance(value, (list, dict, tuple)):
            for x in _walkjsonpath(value, path=p1):
                yield x
        else:
            yield p1, value
    return
