"""
"""

from __future__ import division
from collections import OrderedDict as OD 
import re

import numpy as np
import SloppyCell.ReactionNetworks as scrn 

from rxnnet.util import Series
from rxnnet import structure, dynamics, steadystate
reload(structure)
reload(dynamics)


class Network(object, scrn.Network):  # scrn.Network is an old-style class
    """
    """

    """
    __slots__ = ('add_species', 'add_reaction', 
                 'xdim', 'pdim', 'vdim',
                 'pids', #'p', 'p0', 
                 'xids', 'x', 'x0',
                 'c', 'constants', 
                 'rxnids', 'rxns', 'ratelaws',
                 'get_stoich_mat', 'N', 
                 'integrate', 'get_traj',
                 'get_s', 

                 't',

                 'set_var_vals',

        ) 
    """  


    def __init__(self, *args, **kwargs):
        scrn.Network.__init__(self, *args, **kwargs)
        """
        Thoughts on self.t:
            Can easily introduce bugs, whenver the vector field is changed
            but self.t and self.x0 are not reset
        """
        self.t = 0


    def add_species(self, id, compartment, initial_value=0, *args, **kwargs):
        """A wrapper of SloppyCell.ReactionNetworks.Network.add_species.
        """
        scrn.Network.add_species(self, id, compartment, initial_value, 
                                 *args, **kwargs)
    
    
    def add_reaction(self, id, stoich=None, eqn=None, ratelaw=None, p=None, 
                     **kwargs):
        """A wrapper of SloppyCell.ReactionNetworks.Network.add_reaction. 
        
        :param id: id of the reaction
        :type id: str
        :param stoich: a mapping (stoich, eg, {'S':-1, 'P':1}) or 
                a str (eqn, eg, 'S<->P'); if an eqn is provided, 
                bidirectional arrow ('<->') denotes reversible reaction and 
                unidirectional arrow ('->') denotes irreversible reaction
        :param eqn: 
        :type eqn: str
        :param ratelaw:
        :type ratelaw:
        :param p: map from pid to pinfo, where pinfo can be 
                a float (pval) or a tuple (pval, is_optimizable); 
                eg, p={'V_R1':1, 'KM_S':2, 'KE_R1':(1, False)}
        :type p:
        """
        rxnid = id
        
        # get stoich
        assert not (stoich is None and eqn is None)
        if eqn:
            stoich = _eqn2stoich(eqn)
            
        # add parameters
        if p is not None:
            for pid, pinfo in p.items():
                if isinstance(pinfo, tuple):
                    pval, is_optimizable = pinfo
                else:
                    pval, is_optimizable = pinfo, True
                self.add_parameter(pid, pval, is_optimizable=is_optimizable)
        
        if ratelaw is None:
            ratelaw = '0' 
        
        # add reaction
        scrn.Network.addReaction(self, id=rxnid, stoichiometry=stoich, 
                                 kineticLaw=ratelaw, **kwargs)


    @property
    def xdim(self):
        return len(self.dynamicVars)


    @property
    def pdim(self):
        return len(self.optimizableVars)


    @property
    def vdim(self):
        return len(self.reactions)

    
    @property
    def pids(self):
        return self.optimizableVars.keys()


    @property
    def p(self):
        return Series([var.value for var in self.optimizableVars], 
                           self.pids, dtype=np.float)

        
    @p.setter
    def p(self, p_new):
        try:
            self.set_var_vals(p_new.to_dict())
        except AttributeError:
            self.set_var_vals(dict(zip(self.pids, p_new)))


    @property
    def p0(self):
        return Series([var.initialValue for var in self.optimizableVars], 
                      self.pids, dtype=np.float)    


    @property
    def xids(self):
        return self.dynamicVars.keys()


    @property
    def x0(self):
        return Series([var.initialValue for var in self.dynamicVars], 
                      self.xids, dtype=np.float)


    @property
    def x(self):
        return Series([var.value for var in self.dynamicVars], 
                      self.xids, dtype=np.float)


    @x.setter
    def x(self, x_new):
        try:
            self.set_var_vals(x_new.to_dict())
        except AttributeError:
            self.set_var_vals(dict(zip(self.xids, x_new)))


    @property
    def c(self):
        return Series(OD([(sp.id, sp.value) for sp in self.species 
                          if sp.is_constant]), 
                      dtype=np.float)


    @property
    def constants(self):
        """Replacing the constantVarValues attribute of scrn.Network instances,
        as it is buggy and does not update upon changing p in certain ways.
        """
        return Series([var.value for var in self.constantVars], 
                      self.constantVars.keys(), dtype=np.float)


    @property
    def vars(self):
        return Series(OD(self.variables.items()), dtype=object)
    

    @property
    def varvals(self):
        return Series(OD([(var.id, var.value) for var in self.variables]), 
                      dtype=np.float)

    
    @property
    def varids(self):
        return self.variables.keys()


    @property
    def rxnids(self):
        return self.reactions.keys()


    @property
    def rxns(self):
        return Series(OD([(rxn.id, rxn) for rxn in self.reactions]), 
                      dtype=object)


    @property
    def ratelaws(self):
        return Series(OD([(rxn.id, rxn.kineticLaw) for rxn in self.reactions]),
                      dtype=object)


    @property
    def asgrules(self):
        return Series(OD(self.assignmentRules.items()), dtype=object)


    def get_stoich_mat(self, *args, **kwargs):
        return structure.get_stoich_mat(net=self, *args, **kwargs)
    get_stoich_mat.__doc__ = structure.get_stoich_mat.__doc__


    @property
    def N(self):
        return self.get_stoich_mat(only_dynvar=True, integerize=False)


    @property
    def Nr(self):
        pass


    @property
    def L(self):
        pass


    @property
    def K(self):
        pass


    @property
    def P(self):
        pass


    def integrate(self, *args, **kwargs):
        return dynamics.integrate(self, *args, **kwargs)
    integrate.__doc__ = dynamics.integrate.__doc__
    get_traj = integrate


    def get_s(self, *args, **kwargs):
        return steadystate.get_s(self, *args, **kwargs)
    get_s.__doc__ = steadystate.get_s.__doc__


    def set_ss(self):
        pass


    @property
    def s(self):
        self.set_ss()
        return self.x


    @property
    def v(self):
        return Series(OD([(rxn.id, self.evaluate_expr(rxn.kineticLaw)) 
                          for rxn in self.reactions]), 
                      dtype=np.float)


    @property
    def J(self):
        self.set_ss()
        return self.v


    def update(self, p=None, x=None, t=None):
        """
        """
        if p is not None:
            self.p = p

        if x is not None:
            self.x = x

        if t is not None:
            if t == np.inf:
                if not self.test_ss():
                    self.set_ss()
            else:
                pass



def _eqn2stoich(eqn):
    """Convert reaction equation (a str) to stoichiometry (a mapping).
    """
    def _unpack(s):
        unpacked = filter(None, s.split(' '))  # an example of s: ' 2 ATP '
        if len(unpacked) == 1:
            sc_unsigned, spid = 1, unpacked[0]  # sc: stoichcoef
        elif len(unpacked) == 2:
            sc_unsigned, spid = eval(unpacked[0]), unpacked[1]
        else:
            raise 
        return spid, sc_unsigned
    
    # remove annotating species
    # eg, '(ST+)P->(ST+)G1P', where 'ST' (starch) is kept there to better
    # represent the chemistry
    eqn = re.sub('\(.*?\)', '', eqn)
    
    # re: '<?': 0 or 1 '<'; '[-|=]': '-' or '=' 
    subs, pros = re.split('<?[-|=]>', eqn)
    stoich = OD()
    
    if subs:
        for sub in subs.split('+'):
            subid, sc_unsigned = _unpack(sub)
            stoich[subid] = -1 * sc_unsigned
            
    if pros:
        for pro in pros.split('+'):
            proid, sc_unsigned = _unpack(pro)
            if proid in stoich:
                stoich[proid] = stoich[proid] + sc_unsigned
            else:
                stoich[proid] = sc_unsigned
        
    return stoich

