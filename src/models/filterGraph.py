""" 
Filter graph models.
"""
import uuid
from typing import List, Dict, Optional, Callable
import pickle

from models.effect import Effect
from models.param import EffectParameter




class GraphConnection:
    """
    Represents a connection between a port of a graph node to another port on a different
    graph node. 

    +---------------+
    | node out port |  <- connection in_uuid/in_idx      +--------------+
    |               |     connection out_uuid/out_idx -> | node in port | 
    +---------------+                                    +--------------+
    
    """
    def __init__(self):
        self.uuid = str(uuid.uuid4())
        self.in_uuid = ""  # GraphNode uuid input 
        self.in_idx = 0    # GraphNode port number input
        self.out_uuid = "" # GraphNode uuid output
        self.out_idx = 0   # GraphNode port number output
        
    def clear(self):
        self.in_uuid = ""
        self.in_idx = 0
        self.out_uuid = ""
        self.out_idx = 0    

    def inuse(self):
        "Is this connection in use?"
        return self.in_uuid != "" and self.out_uuid != ""





class GraphNode:
    """ 
    Abstract filter node, it has an input, output and 
    a set of properties depending upon its ntype. Specfic 
    properties are dependent upon derived classes. 
    """
    def __init__(self):
        self.uuid = str(uuid.uuid4())
        self.x = 0.0
        self.y = 0.0
        self.in_ports : List[GraphConnection] = []
        self.out_ports : List[GraphConnection] = []
        
    def changed(self, other):

        def non_presentation_data(obj : GraphNode):
            p = {
                'in_port_data': [],
                'out_port_data': [],
                'properties': []
            }
            for port in obj.in_ports:
                port_data = vars(port)
                del port_data['uuid']
                port_data = {}
                p['in_port_data'].append(port_data)
            for port in obj.out_ports:
                port_data = vars(port)
                del port_data['uuid']
                p['out_port_data'].append(port_data)
            if hasattr(obj, 'properties'):
                p['properties'] = getattr(obj,'properties')
            if hasattr(obj,'enabled'):
                p['enabled'] = getattr(obj,'enabled')
            if hasattr(obj,'threshold'):
                p['threshold'] = getattr(obj,'threshold')
            if hasattr(obj,'low_threshold'):
                p['low_threshold'] = getattr(obj,'low_threshold')
            if hasattr(obj,'high_threshold'):
                p['high_threshold'] = getattr(obj,'high_threshold')

            return p
        
        return non_presentation_data(self) != non_presentation_data(other)


    def num_in_ports(self) -> int:
        return len(self.in_ports)

    def num_out_ports(self) -> int:
        return len(self.out_ports)

    def _set_num_ports(self, conn_list, num):
        new_conn_list = []
        for i in range(num):
            if i < len(conn_list):
                new_conn_list.append(conn_list[i])
            else:
                new_conn_list.append(GraphConnection())
        return new_conn_list

    def set_num_in_ports(self, num):
        self.in_ports = self._set_num_ports(self.in_ports, num)

    def set_num_out_ports(self, num):
        self.out_ports = self._set_num_ports(self.out_ports, num)
      

    # reuse legacy code for effects which can generate a 
    # UI based on a list of EffectParameter model objects.
    def paramData(self) -> List[EffectParameter]:
        return []


    def label(self) -> str:
        raise RuntimeError("abstract method must be overriden")
    

    

class InputNode(GraphNode):

    def label(self) -> str:
        return "Input"

    def __init__(self):
        super().__init__()
        self.set_num_out_ports(1)

class OutputNode(GraphNode):

    def label(self) -> str:
        return "Output"

    def __init__(self):
        super().__init__()
        self.set_num_in_ports(1)
       
class SplitterNode(GraphNode):
    MIN_NUM_OUT_PORTS = 2
    MAX_NUM_OUT_PORTS = 8

    def label(self) -> str:
        return "Splitter"

    def __init__(self):
        super().__init__()
        self.set_num_out_ports(2)
        self.set_num_in_ports(1)

class MixerNode(GraphNode):
    MIN_NUM_IN_PORTS = 2
    MAX_NUM_IN_PORTS = 8

    def label(self) -> str:
        return "Mixer"

    def __init__(self):
        super().__init__()
        self.set_num_in_ports(2)
        self.set_num_out_ports(1)


class EffectNode(GraphNode):

    def __getstate__(self):
        """Return state values to be pickled, excluding callbacks ."""
        state = self.__dict__.copy()
        del state['onPropertyChange']
        del state['onEnabledChange']
        # If you have other unpicklable attributes, exclude them similarly
        # del state['log_file'] 
        return state


    def label(self) -> str:
        return self.effect.plugin_label()
  
    def set_enabled(self, enabled):
        self.enabled = enabled
        if callable(self.onEnabledChange):
            self.onEnabledChange(self.uuid, self.enabled)

    def set_property(self, key: str, value: float):
        self.properties[key] = value
        if callable(self.onPropertyChange):
            self.onPropertyChange(self.uuid, key, value)        

    def get_effect(self) -> Effect:
        return self.effect    

    def __init__(self, effect : Effect):
        super().__init__()
        self.properties : Dict[str, float] = {}
        self.enabled = True
        
        self.onPropertyChange : Callable | None = None
        self.onEnabledChange : Callable | None = None

        self.set_num_in_ports(1)
        self.set_num_out_ports(1)
        for ep in effect.getParameters():
            self.properties[ep.name] = ep.default_value
        self.effect_label = effect.plugin_label()
        self.effect = effect

class LowPassNode(GraphNode):

    def label(self) -> str:
        return "LowPass"

    def __init__(self):
        super().__init__()
        self.threshold = 261.63 # middle c in standard tuning
        # if specified then the midi_code is used for the frequency
        self.midi_code_threshold = -1
        self.set_num_in_ports(1)
        self.set_num_out_ports(1)



class HighPassNode(GraphNode):

    def label(self) -> str:
        return "HighPass"

    def __init__(self):
        super().__init__()
        self.threshold = 261.63 # middle c in standard tuning
        # if specified then the midi_code is used for the frequency
        self.midi_code_threshold = -1
        self.set_num_in_ports(1)
        self.set_num_out_ports(1)

class BandPassNode(GraphNode):

    def label(self) -> str:
        return "BandPass"

    def __init__(self):
        super().__init__()
        self.low_threshold = 200.0
        self.high_threshold = 500.0
        self.low_midi_code_threshold = -1
        self.high_midi_code_threshold = -1
        self.set_num_in_ports(1)
        self.set_num_out_ports(1)


class GainBalanceNode(GraphNode):

    def label(self) -> str:
        return "GainBalance"

    def __init__(self):
        super().__init__()
        self.gain = 1.0
        self.balance = 0.0
        self.set_num_in_ports(1)
        self.set_num_out_ports(1)




class FilterGraph:
    def __init__(self):
        self.uuid = str(uuid.uuid4())
        self.nodes : Dict[str, GraphNode] = {}
        self.connections : Dict[str, GraphConnection] = {}
        self.filename = ""
        self.preset = ""

    def add_node(self, node : GraphNode):
        self.nodes[node.uuid] = node

    def add_connection(self, conn : GraphConnection):
        self.connections[conn.uuid] = conn

    def diff(self, past_node : 'FilterGraph'):
        """
        past_node is a pickled version of this node prior to
        a potential edit. 
        """
        report = {
            "nodes_added": [],
            "nodes_removed": [],
            "nodes_updated": [],
            "change_occured": False
        }

        for (uuid, node) in self.nodes.items():
            # check for node exists that is not past version
            if uuid not in past_node.nodes:
                report["nodes_added"].append(node)
            else:
                other_node = past_node.nodes[uuid]
                # see if something changed
                if node.changed(other_node):
                    report["nodes_updated"].append(node)


        for (uuid, node) in past_node.nodes.items():
            # check for node no longer exists that was in past version
            if uuid not in self.nodes:
                report["nodes_removed"].append(node)

        report['change_occured'] = len(report['nodes_added']) > 0 or \
            len(report['nodes_removed']) > 0 or len(report['nodes_updated']) > 0

        return report
        
        

    
