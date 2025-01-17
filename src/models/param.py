"""

spec sample -> 
{'c_index': 4, 'has_default': True, 
'default_value': 0.0, 'upper_bound': 20.0, 
'lower_bound': -20.0, 'name': 'drivegain', 
'is_bounded_above': True, 'is_bounded_below': True, 
'is_integer': False, 'is_logarithmic': False, 
'is_toggled': False}

"""


class EffectParamBase:
    def __init__(self, spec: dict):
        self.spec = spec
        if spec['has_default']:
            self.defval = spec['default_value']
            self.val = self.defval
            self.required = False 
        else:
            self.val = None
            self.required = True
            self.defval = None

    def get_default_value(self):
        return self.defval

    def has_lower_bound(self):
        return self.spec['is_bounded_below']
    
    def has_upper_bound(self):
        return self.spec['is_bounded_above']
    
    def lower_bound(self):
        return self.spec['lower_bound']
    
    def upper_bound(self):
        return self.spec['upper_bound']
    
    def is_logarithmic(self):
        return self.spec['is_logarithmic']
        
    def is_required(self):
        return self.required 

    def name(self):
        return self.spec['name']    

    def setValue(self, value):
        self.val = value

    def getValue(self):
        return self.val    

    def isRequiredParam(self):
        return self.required    

class BooleanEffectParam(EffectParamBase):
    def __init__(self, spec: dict):
        super().__init__(spec)

    def getValue(self) -> bool:
        return self.val != 0.0
    

class IntegerEffectParam(EffectParamBase):
    def __init__(self, spec: dict):
        super().__init__(spec)



class FloatingEffectParam(EffectParamBase):
    def __init__(self, spec: dict):
        super().__init__(spec)


def ParameterFactory(spec: dict):
    if spec['is_toggled']:
        return BooleanEffectParam(spec)
    elif spec['is_integer']:
        return IntegerEffectParam(spec) 
    else:
        return FloatingEffectParam(spec)


        

