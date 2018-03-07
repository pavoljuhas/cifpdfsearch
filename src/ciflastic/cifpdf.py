#!/usr/bin/env python3

'''
Tools for bulk calculation of pair distribution functions from COD entries.
'''


import logging
import numbers


class Calculator:

    @staticmethod
    def fromConfig(cfg):
        '''Create PDF calculator object from configuration dictionary.
        '''
        from diffpy.srreal import pdfcalculator
        mycfg = cfg.copy()
        calculatorclass = mycfg.pop('calculatorclass')
        klass = getattr(pdfcalculator, calculatorclass)
        calc = klass()
        # version
        calculatorversion = mycfg.pop('calculatorversion', {})
        # configure contained objects
        subobjs = [(n, v) for n, v in mycfg.items()
                   if n == 'envelopes' or isinstance(v, str)]
        dbattrs = [(n, v) for n, v in mycfg.items()
                   if isinstance(v, numbers.Number)]
        for n, v in subobjs + dbattrs:
            setattr(calc, n, v)
            mycfg.pop(n)
        if mycfg:
            unused = ', '.join(mycfg)
            logging.debug('unused configuration items %s', unused)
        return calc

# end of class Calculator
