#!/usr/bin/env python3

'''Create single-entry for nickel CIF data.
'''

import glob
from pprint import pprint
from elasticsearch import Elasticsearch, helpers
from ciflastic import jload, cfpath, cifdocument, cifid

INDEX = 'codtest'
es = Elasticsearch()

cifs = glob.glob(cfpath('standards/*.json'))
actions = (dict(_index=INDEX, _id=cifid(jc), _type='cif',
                _source=cifdocument(jc))
           for jc in map(jload, cifs))

print("-- Purging index", repr(INDEX))
res = es.indices.delete(index=INDEX, ignore_unavailable=True)
pprint(res)

print("\n-- Adding {} standard cifs in bulk".format(len(cifs)))
res = helpers.bulk(es, actions)
pprint(res)
es.indices.flush('_all')

print("\n-- Querying all entries ... ", end='')
res = es.search(index=INDEX, body={"query": {"match_all": {}}})
print("got {} hits.\n".format(res['hits']['total']))
pprint(res['hits']['hits'])
