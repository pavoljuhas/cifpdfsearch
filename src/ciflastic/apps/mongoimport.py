#!/usr/bin/env python3

'''Import MongoDB databroker entries for ISS or XPD beamlines.
'''

import argparse
from ciflastic._utils import toisoformat


parser = argparse.ArgumentParser(description=__doc__.strip())
parser.add_argument('beamline', choices=['iss', 'xpd'],
                    help="NSLS-II beamline to be imported")
parser.add_argument('--index',
                    help="Elastic Search index to be updated "
                         "[{beamline}.test]")
parser.add_argument('--no-filter', action='store_false', dest='filter',
                    help="Disable filtering to internal experimenters")


noconversion = lambda x: x

def normalize_counts(d):
    if not isinstance(d, dict):
        return None
    totalcount = sum(d.values()) or 1.0
    rv = dict((k, v / totalcount) for k, v in d.items())
    return rv


def listofstrings(v):
    rv = None
    if isinstance(v, list) and all(isinstance(w, str) for w in v):
        rv = v
    return rv

DOCMAP = {}

DOCMAP['iss'] = [
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
    ("uid", "uid", noconversion),
    ("year", "year", int),
    ("time", "date", toisoformat),
]

DOCMAP['xpd'] = [
    # mongoname  esname  converter
    ("_id", "xpdid", str),
    ("bt_experimenters", "experimenters", listofstrings),
    ("bt_piLast", "pi", noconversion),
    ("bt_safN", "saf", str),
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

DOCFILTER = {
    'iss' : {},
    'xpd' : {
        # limit to XPD beamline stuff and Billinge relations
        '$or' : [
            {'bt_piLast' : {'$exists' : False}},
            {'bt_piLast' : {'$in' : (
                '0713_test',
                'Abeykoon',
                'Antonaropoulos',
                'Assefa',
                'Banerjee',
                'Benjiamin',
                'Billinge',
                'Bordet',
                'Bozin',
                'Demo',
                'Dooryhee',
                'Frandsen',
                'Ghose',
                'Hanson',
                'Milinda and Runze',
                'Milinda',
                'Pinero',
                'Robinson',
                'Sanjit',
                'Shi',
                'Test',
                'Yang',
                'billinge',
                'simulation',
                'test',
                'testPI',
                'testPI_2',
                'testTake2',
                'xpdAcq_realase',
            )}}
        ]},
}


def esdocument(docmap, entry):
    rv = {}
    assert '_id' in entry
    for mname, esname, fcnv in docmap:
        if not mname in entry:
            continue
        mvalue = entry[mname]
        evalue = fcnv(mvalue) if mvalue is not None else None
        if evalue is None:
            continue
        rv[esname] = evalue
    return rv


def main(cmdargs=None):
    # for speed sake parse arguments before any imports
    args = parser.parse_args(cmdargs)
    # now proceed with imports
    from ciflastic import config
    from pymongo import MongoClient
    from elasticsearch import Elasticsearch
    from elasticsearch import helpers as eshelpers
    dbname = '{.beamline}-datastore'.format(args)
    esindex = args.index or '{.beamline}test'.format(args)
    client = MongoClient(**config.MONGO)
    db = client[dbname]
    collection = db['run_start']
    bmdocmap = DOCMAP[args.beamline]
    projection = set(x[0] for x in bmdocmap)
    mfilter = DOCFILTER[args.beamline] if args.filter else {}
    cursor = collection.find(mfilter, projection=projection)
    idsdocs = ((str(e['_id']), esdocument(bmdocmap, e)) for e in cursor)
    actions = (dict(_index=esindex, _id=esid, _type=args.beamline, _source=d)
               for esid, d in idsdocs)
    es = Elasticsearch()
    es.indices.delete(index=esindex, ignore_unavailable=True)
    es.indices.create(index=esindex)
    mbody = {"properties" : {
        "time" : {"type" : "date", "format": "epoch_second"},
        "date" : {"type" : "date", "format": "strict_date_optional_time"}
    }}
    es.indices.put_mapping(doc_type=args.beamline, index=esindex, body=mbody)
    eshelpers.bulk(es, actions)
    return


if __name__ == '__main__':
    main()
