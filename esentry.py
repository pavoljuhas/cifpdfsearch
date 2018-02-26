#!/usr/bin/env python3

from sys import exit
import json
import pprint
from diffpy.pdfgetx.functs import composition_analysis
from elasticsearch import Elasticsearch


CIFDOCMAP = '''
_cell_length_a a
_cell_length_b b
_cell_length_c c
_cell_angle_alpha alpha
_cell_angle_beta beta
_cell_angle_gamma gamma
_cell_volume volume
_chemical_formula_sum formula
_symmetry_space_group_name_H-M spacegroup
_symmetry_space_group_name_Hall spacegrouphall
_cod_database_code codid
'''.split()

CIFDOCMAP = dict(zip(CIFDOCMAP[0::2], CIFDOCMAP[1::2]))

CIFCONVERTERS = {
    "INT" : int,
    "FLOAT" : float,
    "" : lambda x: x,
}


def getconverter(codtype):
    f = CIFCONVERTERS.get(codtype, CIFCONVERTERS[''])
    return f


def cifid(codjson):
    rv = int(codjson['data']['values']['_cod_database_code'][0])
    return rv


def cifscalar(cifname):
    return True


def normalized_formula(formula):
    smbls, counts = composition_analysis(formula)
    totalcount = sum(counts)
    rv = dict.fromkeys(smbls, 0.0)
    for s, c in zip(smbls, counts):
        rv[s] += c
    for s in rv:
        rv[s] /= totalcount
    return rv


def cifdocument(codjson):
    """
    Create document from JSON record from cif2json utility.
    """
    codvalues = codjson['data']['values']
    codtypes = codjson['data']['types']
    rv = {}
    for cn, en in CIFDOCMAP.items():
        tps = codtypes[cn]
        vals = codvalues[cn]
        gen = (getconverter(tp)(x) for tp, x in zip(tps, vals))
        evalue = next(gen) if cifscalar(cn) else list(gen)
        rv[en] = evalue
    # derived quantities
    rv['nformula'] = normalized_formula(rv['formula'])
    return rv


jcif = json.load(open('standards/Ni-9008476.json'))
doc = cifdocument(jcif)
cid = cifid(jcif)

es = Elasticsearch()
es.index(index='cod', doc_type='cif', id=cid, body=doc)
res = es.search(index="cod", body={"query": {"match_all": {}}})
print("Got %d Hits:" % res['hits']['total'])
pprint.pprint(res['hits'])
