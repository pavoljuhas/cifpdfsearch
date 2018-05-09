#!/usr/bin/env python3

'''Import MongoDB databroker entries for ISS or XPD beamlines.
'''

import argparse
from ciflastic._utils import toisoformat


parser = argparse.ArgumentParser(description=__doc__.strip())
parser.add_argument('--index', default='isstest',
                    help="Elastic Search index to be updated")


noconversion = lambda x: x

def normalize_counts(d):
    totalcount = sum(d.values()) or 1.0
    rv = dict((k, v / totalcount) for k, v in d.items())
    return rv


ISSDOCMAP = [
    # mongoname  esname  converter
    ("_id", "issid", str),
    ("comment", "comment", noconversion),
    ("cycle", "cycle", int),
    ("detectors", "detectors", noconversion),
    ("e0", "e0", noconversion),
    ("edge", "edge", noconversion),
    ("element", "element", noconversion),
    ("experiment", "experiment", noconversion),
    ("group", "group", noconversion),
    ("name", "name", noconversion),
    ("num_points", "num_points", noconversion),
    ("plan_name", "plan_name", noconversion),
    ("PI", "pi", noconversion),
    ("PROPOSAL", "proposal", noconversion),
    ("SAF", "saf", noconversion),
    ("scan_id", "scan_id", noconversion),
    ("time", "time", noconversion),
    ("trajectory_name", "trajectory_name", noconversion),
    ("year", "year", int),
    ("time", "date", toisoformat),
]


XPDDOCMAP = [
    # mongoname  esname  converter
    ("_id", "xpdid", str),
    ("bt_experimenters", "experimenters", noconversion),
    ("bt_piLast", "pi", noconversion),
    ("bt_safN", "saf", noconversion),
    ("bt_wavelength", "wavelength", float),
    ("composition_string", "formula", noconversion),
    ("dark_frame", "dark_frame", bool),
    ("group", "group", noconversion),
    ("lead_experimenter", "pi", noconversion),
    ("notes", "comment", noconversion),
    ("num_points", "num_points", noconversion),
    ("plan_name", "plan_name", noconversion),
    ("sample_composition", "composition", normalize_counts),
    ("scan_id", "scan_id", noconversion),
    ("sp_computed_exposure", "sp_computed_exposure", float),
    ("sp_num_frames", "sp_num_frames", int),
    ("sp_plan_name", "sp_plan_name", noconversion),
    ("sp_time_per_frame", "sp_time_per_frame", float),
    ("sp_type", "sp_type", noconversion),
    ("time", "time", noconversion),
    ("time", "date", toisoformat),
    ("uid", "uid", noconversion),
    ("time", "year", lambda t : int(toisoformat(t)[:4])),
]


def esdocument(docmap, entry):
    rv = {}
    assert '_id' in entry
    for mname, esname, fcnv in docmap:
        if not mname in entry:
            continue
        mvalue = entry[mname]
        evalue = fcnv(mvalue)
        if evalue is None:
            continue
        rv[esname] = evalue
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
    documents = (esdocument(ISSDOCMAP, e) for e in cursor)
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
