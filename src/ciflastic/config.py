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

__all__ = ["CODDIR", "PDFSTORAGE", "PDFCALCULATOR", "loadConfig"]


from warnings import warn
from os.path import expanduser, abspath, join as pathjoin
from xdg.BaseDirectory import load_first_config, xdg_config_dirs
import yaml
import ciflastic

# Configuration constants ----------------------------------------------------

CODDIR = ''
PDFSTORAGE = ''
PDFCALCULATOR = {}


def loadConfig(cfgfile):
    """
    Load dictionary of ciflastic configuration values.

    Arguments
    ---------
    cfgfile : str
        Path to configuration file in YAML format.

    Returns
    -------
    cfg : dict
        Dictionary of configuration values.
    """
    with open(cfgfile) as fp:
        cfg = yaml.load(fp)
    return cfg


def initialize(cfgfile=None):
    cfname = 'ciflastic/ciflastic.yml'
    if cfgfile is None:
        cfgfile = load_first_config(cfname)
        if cfgfile is None:
            cf = pathjoin(xdg_config_dirs[0], cfname)
            tf = ciflastic.datapath('config/ciflastic.yml.template')
            wmsg = ("Cannot find configuration file {}.\n"
                    "Falling back to {}.").format(cf, tf)
            warn(wmsg)
            return
    cfg = loadConfig(cfgfile)
    global CODDIR
    global PDFSTORAGE
    CODDIR = abspath(expanduser(cfg['coddir']))
    PDFSTORAGE = abspath(expanduser(cfg.get('pdfstorage', '')))
    PDFCALCULATOR.clear()
    PDFCALCULATOR.update(cfg.get('pdfcalculator', {}))
    return


initialize()
