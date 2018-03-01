#!/usr/bin/env python3

"""Internal helper functions.
"""

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    from itertools import zip_longest
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


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
