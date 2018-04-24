#!/usr/bin/env python3

'''Add DOI values from the specified CIF files to the ES index.
'''

import sys
import os.path
import argparse
from pprint import pprint

parser = argparse.ArgumentParser(description=__doc__.strip())
parser.add_argument('--index', default='codtest',
                    help="Elastic Search index to be updated")
parser.add_argument('cifs', nargs='+',
                    help="CIF files for which to calculate PDFs. "
                         "Replace '-' with files from standard input.")


def doiaction(filename, index):
    import gemmi.cif
    doc = gemmi.cif.read(filename)
    block = doc.sole_block()
    doi = block.find_value('_journal_paper_doi')
    codid = block.find_value('_cod_database_code')
    if not doi:
        return {}
    action = {
        '_op_type' : 'update',
        '_index' : index,
        '_id' : codid,
        '_type' : 'cif',
        'doc' : {'doi' : doi},
    }
    return action


def main(args):
    from elasticsearch import Elasticsearch
    from elasticsearch import helpers as eshelpers
    ciflist = args.cifs
    if '-' in ciflist:
        strippedlines = (line.strip() for line in sys.stdin)
        extras = [a for a in strippedlines if a]
        idx = ciflist.index('-')
        ciflist = ciflist[:idx] + extras + ciflist[idx + 1:]
    actions = (doiaction(f, args.index) for f in ciflist)
    actions = filter(None, actions)
    es = Elasticsearch()
    res = eshelpers.bulk(es, actions)
    pprint(res)
    return


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
