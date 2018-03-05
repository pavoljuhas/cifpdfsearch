#!/usr/bin/env python3

"""
This modules provides constants and paths for local installation.

The recommended way to change these constants is to copy
"config/ciflastic.aml.template" to "config/ciflastic.aml"
and edit the site settings as needed.

Attributes
----------
CODDIR : str
    Absolute path to the Crystallography Open Database.
"""


CODDIR = ''


def initialize(cfgfile=None):
    from warnings import warn
    from os.path import isfile, expanduser, abspath
    import archieml
    from ciflastic import cfpath
    if cfgfile is None:
        cfgfile = cfpath('config/ciflastic.aml')
        if not isfile(cfgfile):
            wmsg = "Cannot open default configuration file {}".format(cfgfile)
            warn(wmsg)
            return
    global CODDIR
    with open(cfgfile) as fp:
        cfg = archieml.load(fp)
    CODDIR = abspath(expanduser(cfg['coddir']))
    return


initialize()
