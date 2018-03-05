#!/usr/bin/env python3

'''Create single-entry for nickel CIF data.
'''

from pprint import pprint
from elasticsearch import Elasticsearch
from ciflastic import jload, cfpath, cifdocument, cifid

INDEX = 'codtest'
es = Elasticsearch()

cif = cfpath('standards/Ni-9008476.json')
jcif = jload(cif)
cdoc = cifdocument(jcif)
cid = cifid(jcif)

print("-- Purging index", repr(INDEX))
res = es.indices.delete(index=INDEX, ignore_unavailable=True)
pprint(res)

print("\n-- Adding nickel document to", repr(INDEX))
res = es.index(index=INDEX, doc_type='cif', id=cid, body=cdoc)
pprint(res)
es.indices.flush('_all')

print("\n-- Querying all entries ... ", end='')
res = es.search(index=INDEX, body={"query": {"match_all": {}}})
print("got {} hits.\n".format(res['hits']['total']))
pprint(res['hits']['hits'])
