#!/usr/bin/env python3


from cifpdfsearch._utils import tofloat, grouper, safecall


CIFDOCMAP = '''
_cell_length_a a
_cell_length_b b
_cell_length_c c
_cell_angle_alpha alpha
_cell_angle_beta beta
_cell_angle_gamma gamma
_cell_volume volume
_chemical_formula_sum formula
_chemical_name_mineral mineralname
_symmetry_space_group_name_H-M spacegroup
_symmetry_space_group_name_Hall spacegrouphall
_cod_database_code codid
'''.split()

CIFDOCMAP = dict(grouper(CIFDOCMAP, 2))

CIFCONVERTERS = {
    "_cell_angle_alpha" : tofloat,
    "_cell_angle_beta" : tofloat,
    "_cell_angle_gamma" : tofloat,
    "_cell_volume" : tofloat,
    "INT" : tofloat,
    "FLOAT" : tofloat,
    "" : lambda x: x,
}


def getconverter(codjson, cifname):
    def _candidates():
        yield CIFCONVERTERS.get(cifname)
        codtypes = codjson['data']['types']
        tp = codtypes.get(cifname, ("",))[0]
        yield CIFCONVERTERS.get(tp)
        yield CIFCONVERTERS[""]
    fcnv = next(f for f in _candidates() if f is not None)
    return fcnv


def cifid(codjson):
    rv = int(codjson['data']['values']['_cod_database_code'][0])
    return rv


def cifscalar(cifname):
    return True


def normalized_formula(formula):
    from diffpy.pdfgetx.functs import composition_analysis
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
    cifnames = set(CIFDOCMAP).intersection(codvalues)
    getcomposition = safecall(normalized_formula)
    rv = {}
    for cn in cifnames:
        fcnv = getconverter(codjson, cn)
        genval = (fcnv(x) for x in codvalues[cn])
        evalue = next(genval) if cifscalar(cn) else list(genval)
        en = CIFDOCMAP[cn]
        rv[en] = evalue
    # derived quantities
    formula = rv.get('formula', 'xxx-fail-xxx')
    if getcomposition(formula):
        rv['composition'] = getcomposition(formula)
        rv['nel'] = len(rv['composition'])
    return rv
