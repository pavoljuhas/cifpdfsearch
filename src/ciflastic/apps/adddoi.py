#!/usr/bin/env python3

'''Add DOI values from the specified CIF files to the ES index.
'''

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
    from ciflastic._utils import getargswithstdin
    from elasticsearch import Elasticsearch
    from elasticsearch import helpers as eshelpers
    ciflist = getargswithstdin(args.cifs)
    es = Elasticsearch()
    gscan = eshelpers.scan(es, query={'query' : {'match_all' : {}}},
                           index=args.index, doc_type='cif', _source=False)
    docids = set(e['_id'] for e in gscan)
    actions = (doiaction(f, args.index) for f in ciflist)
    actions = filter(lambda a : a and a['_id'] in docids, actions)
    res = eshelpers.bulk(es, actions)
    pprint(res)
    return


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
