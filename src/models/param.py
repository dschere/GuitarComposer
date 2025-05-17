"""
sample data for reference 
{'c_index': 4, 'has_default': True, 
'default_value': 0.0, 'upper_bound': 20.0, 
'lower_bound': -20.0, 'name': 'drivegain', 
'is_bounded_above': True, 'is_bounded_below': True, 
'is_integer': False, 'is_logarithmic': False, 
'is_toggled': False}
"""
from typing import List


def create_choices(low, high, defval, is_integer) -> List[float]:
    r = []
    if is_integer:
        r = range(int(low),int(high)+1)
    else:
        step = (high - low) / 100.0
        for i in range(0,101):
            v = low + (step * i)
            if v > defval and (v-step) < defval:
                r.append(defval)
            r.append(v)
        if defval not in r:
            raise ValueError
    return r    

class EffectParameter:
    BOUNDED_REAL = 0
    BOUNDED_INTEGER = 1
    UNBOUNDED_REAL = 2
    UNBOUNDED_INTEGER = 3
    BOOLEAN = 4

    def __str__(self):
        msg = f"{self.name} {self.current_value}"
        return msg

    def __init__(self, spec: dict):
        self.c_index = 0
        self.has_default = False
        self.default_value = 0.0
        self.upper_bound = 0.0
        self.is_bounded_above= False
        self.lower_bound = 0.0
        self.is_bounded_below = False
        self.name = ""
        self.is_integer = False
        self.is_logarithmic = False
        self.is_toggled = False
        self.pres_type = -1
        self.current_value = 0.0
        self.choices : List[float] = []
        
        for k,v in spec.items():
            setattr(self, k, v) 

        self.current_value = self.default_value


        bounded = self.is_bounded_below and self.is_bounded_above
        if self.is_toggled:
            self.pres_type = self.BOOLEAN
        elif bounded and not self.is_logarithmic:
            if self.is_integer:
                self.pres_type = self.BOUNDED_INTEGER
            else:
                self.pres_type = self.BOUNDED_REAL
            if not self.has_default:
                diff = self.upper_bound - self.lower_bound
                self.default_value = self.lower_bound + (diff/2)

            try:
                self.choices = create_choices(self.lower_bound, 
                    self.upper_bound, self.default_value, self.is_integer)  
            except ValueError:
                # punt ...  
                self.pres_type = self.UNBOUNDED_REAL
        else:
            if self.is_integer:
                self.pres_type = self.UNBOUNDED_INTEGER
            else:
                self.pres_type = self.UNBOUNDED_REAL

        


        

