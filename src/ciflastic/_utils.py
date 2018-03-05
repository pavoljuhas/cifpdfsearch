#!/usr/bin/env python3

"""Internal helper functions.
"""

import sys


def grouper(iterable, n, *fillvalue):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    from itertools import islice, cycle
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
            print('foo')
            return _last['value']
        rv = default
        try:
            rv = f(*args, **kwds)
            _last.update(signature=signature, value=rv)
        except (ValueError, TypeError):
            pass
        return rv
    return wrapper
