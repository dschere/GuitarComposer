from typing import List


class custom_instrument_string_list_item_spec:
    def __init__(self):
        self.instrument_name = ""
        self.weight = 0.0  # Weighting factor for the instrument in the blend

    def set_name(self, instrument_name):
        self.instrument_name = instrument_name

    def set_weight(self, weight):
        self.weight = weight

class custom_instrument_string_spec:
    def __init__(self):
        self.components : List[custom_instrument_string_list_item_spec] = []  


class custom_instrument_spec:

    new_instrument_counter = 1  # Class variable to keep track of the number of new instruments created



    def __init__(self):
        self.name = ""
        self.strings : List[custom_instrument_string_spec] = []  # List of strings, each string is a list of (instrument_name, weight) tuples

    def setup_new_instrument(self):
        self.name = f"New Custom Instrument - {custom_instrument_spec.new_instrument_counter}"
        custom_instrument_spec.new_instrument_counter += 1
        self.strings = []
        for _ in range(6):  # Assuming a standard 6-string guitar
            string_spec = custom_instrument_string_spec()
            componet = custom_instrument_string_list_item_spec()
            componet.instrument_name = "Steel Guitar"
            componet.weight = 1.0
            string_spec.components.append(componet)            
            self.strings.append(string_spec)

    def setup_from_dict(self, key, value):
        self.name = key
        self.strings = []
        for string_dict in value["string_map"]:
            string_spec = custom_instrument_string_spec()
            for instrument_name, weight in string_dict.items():
                component = custom_instrument_string_list_item_spec()
                component.instrument_name = instrument_name
                component.weight = weight
                string_spec.components.append(component)
            self.strings.append(string_spec)

    def add_to_dictionary(self, d):
        """
        Example of how to represent the custom instrument spec as a JSON string for debugging purposes.

        "Acoustic Guitar" : { "string_map": [
        {
            "Harp": 0.2,
            "Steel Guitar": 0.8
        },
        {
            "Nylon Guitar": 0.2,
            "Steel Guitar": 0.8
        },
        {
            "Nylon + Steel": 0.2,
            "Steel Guitar": 0.8
        },
        {
            "Nylon + Steel": 0.5,
            "Steel Guitar": 0.8
        },
        {
            "12-str.GT": 0.4,
            "Steel Guitar": 0.8
        },
        {
            "12-str.GT": 0.8,
            "Steel Guitar": 0.8
        }
    ]}
        
        """
        value = {"string_map": []}
        for string_spec in self.strings:
            string_dict = {}
            for component in string_spec.components:
                string_dict[component.instrument_name] = component.weight
            value["string_map"].append(string_dict)
        d[self.name] = value

