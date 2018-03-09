#!/usr/bin/env python3

"""
This modules provides constants and paths for local installation.

The recommended way to change these constants is to copy
"config/ciflastic.yml.template" to "config/ciflastic.aml"
and edit the site settings as needed.

Attributes
----------
CODDIR : str
    Absolute path to the Crystallography Open Database.
"""


CODDIR = ''
PDFSTORAGE = ''
PDFCALCULATOR = {}


def initialize(cfgfile=None):
    from warnings import warn
    from os.path import isfile, expanduser, abspath
    import yaml
    from ciflastic import datapath
    if cfgfile is None:
        cfgfile = datapath('config/ciflastic.yml')
        if not isfile(cfgfile):
            wmsg = "Cannot open default configuration file {}".format(cfgfile)
            warn(wmsg)
            return
    global CODDIR
    global PDFSTORAGE
    with open(cfgfile) as fp:
        cfg = yaml.load(fp)
    CODDIR = abspath(expanduser(cfg['coddir']))
    PDFSTORAGE = abspath(expanduser(cfg.get('pdfstorage', '')))
    PDFCALCULATOR.clear()
    PDFCALCULATOR.update(cfg.get('pdfcalculator', {}))
    return


initialize()
