#!/usr/bin/env python3

'''Import MongoDB databroker entries for ISS or XPD beamlines.
'''

import argparse
from ciflastic._utils import grouper, toisoformat


parser = argparse.ArgumentParser(description=__doc__.strip())
parser.add_argument('--index', default='isstest',
                    help="Elastic Search index to be updated")


ISSDOCMAP = '''
_id issid
comment comment
cycle cycle
detectors detectors
e0 e0
edge edge
element element
experiment experiment
group group
name name
num_points num_points
plan_name plan_name
PI pi
PROPOSAL proposal
SAF saf
scan_id scan_id
time time
trajectory_name trajectory_name
year year
time date
'''.split()
ISSDOCMAP = [tuple(x) for x in grouper(ISSDOCMAP, 2)]


ISSCONVERTERS = {
    'issid' : str,
    'cycle' : int,
    'year' : int,
    'date' : toisoformat,
    '' : lambda x: x,
}


def getconverter(eskey):
    fcnv = ISSCONVERTERS.get(eskey, ISSCONVERTERS[''])
    return fcnv


def issdocument(rsentry):
    rv = {}
    assert '_id' in rsentry
    for mname, esname in ISSDOCMAP:
        if not mname in rsentry:
            continue
        mvalue = rsentry[mname]
        if mvalue == '':
            continue
        fcnv = getconverter(esname)
        rv[esname] = fcnv(mvalue)
    return rv


def main(args):
    from ciflastic import config
    from pymongo import MongoClient, DESCENDING
    from elasticsearch import Elasticsearch
    from elasticsearch import helpers as eshelpers
    client = MongoClient(**config.MONGO)
    db = client['iss-datastore']
    collection = db['run_start']
    projection = set(x[0] for x in ISSDOCMAP)
    cursor = collection.find(projection=projection,
                             sort=[('time', DESCENDING)])
    documents = (issdocument(e) for e in cursor)
    actions = (dict(_index=args.index, _id=d['issid'], _type='iss', _source=d)
               for d in documents)
    es = Elasticsearch()
    es.indices.delete(index=args.index, ignore_unavailable=True)
    es.indices.create(index=args.index)
    mbody = {"properties" : {
        "time" : {"type" : "date", "format": "epoch_second"},
        "date" : {"type" : "date", "format": "strict_date_optional_time"}
    }}
    es.indices.put_mapping(doc_type='iss', index=args.index, body=mbody)
    eshelpers.bulk(es, actions)
    return


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
