#!/usr/bin/env python

"""
cifpdfsearch - elastic search tools for CIF structures and NSLS2 data

Packages:   cifpdfsearch
"""

import os
import re
import sys
import glob
from setuptools import setup, find_packages

# Use this version when git data are not available, like in git zip archive.
# Update when tagging a new release.
FALLBACK_VERSION = '0.0.1'

MYNAME = 'cifpdfsearch'

# determine if we run with Python 3.
PY3 = (sys.version_info[0] == 3)

# versioncfgfile holds version data for git commit hash and date.
# It must reside in the same directory as version.py.
MYDIR = os.path.dirname(os.path.abspath(__file__))
versioncfgfile = os.path.join(MYDIR, 'src', MYNAME, 'version.cfg')
gitarchivecfgfile = os.path.join(MYDIR, '.gitarchive.cfg')

def gitinfo():
    from subprocess import Popen, PIPE
    kw = dict(stdout=PIPE, cwd=MYDIR, universal_newlines=True)
    proc = Popen(['git', 'describe', '--match=v[[:digit:]]*'], **kw)
    desc = proc.stdout.read()
    proc = Popen(['git', 'log', '-1', '--format=%H %ct %ci'], **kw)
    glog = proc.stdout.read()
    rv = {}
    version = '.post'.join(desc.strip().split('-')[:2]).lstrip('v')
    rv['version'] = version or FALLBACK_VERSION
    rv['commit'], rv['timestamp'], rv['date'] = glog.strip().split(None, 2)
    return rv


def getversioncfg():
    if PY3:
        from configparser import RawConfigParser
    else:
        from ConfigParser import RawConfigParser
    vd0 = dict(version=FALLBACK_VERSION, commit='', date='', timestamp=0)
    # first fetch data from gitarchivecfgfile, ignore if it is unexpanded
    g = vd0.copy()
    cp0 = RawConfigParser(vd0)
    cp0.read(gitarchivecfgfile)
    if len(cp0.get('DEFAULT', 'commit')) > 20:
        g = cp0.defaults()
        mx = re.search(r'\btag: v(\d[^,]*)', g.pop('refnames'))
        if mx:
            g['version'] = mx.group(1)
    # then try to obtain version data from git.
    gitdir = os.path.join(MYDIR, '.git')
    if os.path.exists(gitdir) or 'GIT_DIR' in os.environ:
        try:
            g = gitinfo()
        except OSError:
            pass
    # finally, check and update the active version file
    cp = RawConfigParser()
    cp.read(versioncfgfile)
    d = cp.defaults()
    rewrite = not d or (g['commit'] and (
        g['version'] != d.get('version') or g['commit'] != d.get('commit')))
    if rewrite:
        cp.set('DEFAULT', 'version', g['version'])
        cp.set('DEFAULT', 'commit', g['commit'])
        cp.set('DEFAULT', 'date', g['date'])
        cp.set('DEFAULT', 'timestamp', g['timestamp'])
        with open(versioncfgfile, 'w') as fp:
            cp.write(fp)
    return cp

versiondata = getversioncfg()

with open(os.path.join(MYDIR, 'README.md')) as fp:
    long_description = fp.read()

# define distribution
setup_args = dict(
    name = MYNAME,
    version = versiondata.get('DEFAULT', 'version'),
    packages = find_packages('src'),
    package_dir = {'' : 'src'},
    # test_suite = 'cifpdfsearch.tests',
    include_package_data = True,
    install_requires = [],
    zip_safe = False,
    data_files = [
        ('', ['README.md']),
        ('config', ['config/cifpdfsearch.yml.template']),
        ('standards', (glob.glob('standards/*.json') +
                       glob.glob('standards/*.cif'))),
    ],
    author = "Pavol Juhas",
    author_email = "pavol.juhas@gmail.com",
    description = "elastic search tools for CIF structures and NSLS2 data",
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    license = 'BSD-style license',
    url = "https://github.com/pavoljuhas/cifpdfsearch",
    keywords = "elastic search CIF structures PDF NSLS2 x-ray",
    classifiers = [
        # List of possible values at
        # https://pypi.python.org/pypi?:action=list_classifiers
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
        'Topic :: Scientific/Engineering :: Physics',
    ],
)

if __name__ == '__main__':
    setup(**setup_args)
