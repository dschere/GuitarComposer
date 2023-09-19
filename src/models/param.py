"""
Representation of a parameter
"""


class Parameter:
    def __init__(self, **kwargs):
        defval = kwargs.get('defval')
        assert(defval != None)
        name = kwargs.get('name')
        assert(name != None)
        
        self.dtype = type(defval)
        self.defval = defval
        self.value =  kwargs.get('value',defval)
        self.name = name
        
        self.manditory = kwargs.get('manditory')
        
        
class BoolParam(Parameter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        assert(self.dtype == type(True))
            
class IntParam(Parameter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        assert(self.dtype == type(0))
                
        self.minval = kwargs.get('minval')
        assert(self.minval != None)
        
        self.maxval = kwargs.get('maxval')
        assert(self.maxval != None)
        
class FloatParam(Parameter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        assert(self.dtype == type(0.0))
                
        self.minval = kwargs.get('minval')
        assert(self.minval != None)
        
        self.maxval = kwargs.get('maxval')
        assert(self.maxval != None)
        
