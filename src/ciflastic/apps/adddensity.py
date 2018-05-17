#!/usr/bin/env python3

'''Add numeric density field for the specified CIF files to the ES index.
'''

import argparse
from pprint import pprint

parser = argparse.ArgumentParser(description=__doc__.strip())
parser.add_argument('--index', default='codall',
                    help="Elastic Search index to be updated")
parser.add_argument('files', nargs='+',
                    help="two column data files with (codid, numdensity)")


def makeaction(index, codid, numdensity):
    action = {
        '_op_type' : 'update',
        '_index' : index,
        '_id' : str(codid),
        '_type' : 'cif',
        'doc' : {'numdensity' : numdensity},
    }
    return action


def main(args):
    from elasticsearch import Elasticsearch
    from elasticsearch import helpers as eshelpers
    es = Elasticsearch()
    gscan = eshelpers.scan(es, query={'query' : {'match_all' : {}}},
                           index=args.index, doc_type='cif', _source=False)
    docids = set(e['_id'] for e in gscan)
    lines = (line for f in args.files for line in open(f))
    pairs = ((w[0], float(w[1])) for w in map(str.split, lines))
    actions = (makeaction(args.index, codid, density)
               for codid, density in pairs)
    actions = filter(lambda a : a and a['_id'] in docids, actions)
    res = eshelpers.bulk(es, actions)
    pprint(res)
    return


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
