#!/usr/bin/env python3

'''Import MongoDB databroker entries for ISS or XPD beamlines.
'''

import sys
import os.path
import argparse
from pprint import pprint
from ciflastic._utils import tofloat, grouper, safecall
import datetime


parser = argparse.ArgumentParser(description=__doc__.strip())
parser.add_argument('--index', default='isstest',
                    help="Elastic Search index to be updated")

_MONGO_HOST = {'port' : 9876}

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


def toisoformat(epoch):
    epochms = round(epoch, 3)
    dt = datetime.datetime.fromtimestamp(epochms)
    tiso = dt.isoformat()
    rv = tiso[:-3] if dt.microsecond else tiso
    assert len(rv) in (19, 23)
    return rv


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
    from pymongo import MongoClient, DESCENDING
    from elasticsearch import Elasticsearch
    from elasticsearch import helpers as eshelpers
    client = MongoClient(**_MONGO_HOST)
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
