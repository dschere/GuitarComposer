""" 
Filter graph models.
"""
import uuid
from typing import List, Dict, Optional, Callable, Tuple
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
        self.in_idx = -1
        self.out_uuid = ""
        self.out_idx = -1    

    def inuse(self):
        "Is this connection in use?"
        return self.in_uuid != "" and self.out_uuid != ""

    def pretty_print(self, graph: 'FilterGraph', indent = ""):
        in_node = graph.nodes.get(self.in_uuid)
        out_node = graph.nodes.get(self.out_uuid)
        if in_node is None or out_node is None or self.out_idx < 0 or self.in_idx < 0:
            print(f"{indent} Invalid connection")
        else:
            print(f"{indent} {in_node.__class__.__name__}.out[{self.out_idx}] --> {out_node.__class__.__name__}.in[{self.in_idx}]")
        




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

    def pretty_print(self, fg: 'FilterGraph', indent = ""):
        print(f"{indent} {self.__class__.__name__} uuid = {self.uuid}")
        print(f"{indent}   In ports:")
        for port in self.in_ports:
            port.pretty_print(fg, indent=indent+"    ")
        print(f"{indent}   Out ports:")
        for port in self.out_ports:
            port.pretty_print(fg, indent=indent+"    ")
        
        
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

    def pretty_print(self):
        print(f"=== FilterGraph uuid = {self.uuid} ===")
        print("Nodes:")
        for (uuid, node) in self.nodes.items():
            node.pretty_print(self, indent="    ")  
        print("Connections:")
        for (uuid, conn) in self.connections.items():
            conn.pretty_print(self, indent="    ")

    def add_node(self, node : GraphNode):
        self.nodes[node.uuid] = node

    def remove_connection(self, conn_uuid: str):
        c = self.connections.get(conn_uuid)
        if c is not None:
            if c.in_idx != -1 and c.out_idx != -1:
                in_uuid = self.nodes[c.in_uuid]
                out_uuid = self.nodes[c.out_uuid]
                in_uuid.out_ports[c.in_idx].clear()
                out_uuid.in_ports[c.out_idx].clear()

            del self.connections[conn_uuid]
            

    def add_connection(self, conn : GraphConnection):
        self.connections[conn.uuid] = conn

        try:        
            in_node = self.nodes.get(conn.in_uuid)
            if in_node is not None and conn.in_idx < len(in_node.out_ports) and conn.in_idx >= 0:
                in_node.out_ports[conn.in_idx] = conn

            out_node = self.nodes.get(conn.out_uuid)
            if out_node is not None and conn.out_idx < len(out_node.in_ports) and conn.out_idx >= 0:
                out_node.in_ports[conn.out_idx] = conn

        except:
            print(f"connection {vars(conn)}")
            print(f"in_node {vars(self.nodes.get(conn.in_uuid))}")
            print(f"out_node {vars(self.nodes.get(conn.out_uuid))}")
            raise
    

    def validate(self, current_node : GraphNode | None = None, visited = set()) -> Tuple[bool, str, object]:
        """ 
        Return true or false if the filter graph is valid.        
        """
        if current_node is None:
            # search for input.
            input_node = None
            for n_uuid in self.nodes.keys():
                node = self.nodes[n_uuid]
                if isinstance(node, InputNode):
                    input_node = node
                    break 
            if input_node is None:
                return (False, "No input node",None)
            return self.validate(input_node, visited)
        #elif current_node is not None and current_node.uuid in visited:
        #    return (False, "Cycle detected, node connection loop",current_node)
        elif isinstance(current_node, InputNode):
            assert(len(current_node.out_ports) == 1)
            assert(len(current_node.in_ports) == 0)
            c = current_node.out_ports[0]
            if c.out_uuid == "":
                return (False, "Input node has no output connection",current_node)
            
            next_node = self.nodes[c.out_uuid]
            visited.add(current_node.uuid)

            if next_node is current_node:
                raise RuntimeError("validation logic error")
            return self.validate(next_node, visited)

        elif isinstance(current_node, SplitterNode):
            for c in current_node.out_ports:
                next_node = self.nodes.get(c.out_uuid)
                if next_node is None:
                    return (False, "No output node for splitter connection",c)
                visited.add(current_node.uuid)
                (valid, error, eo) = self.validate(next_node, visited)
                if not valid:
                    return (False, error, eo)
            #self.pretty_print()
            return (True, "", None)    

        elif isinstance(current_node, OutputNode):
            assert(len(current_node.in_ports) == 1)
            assert(len(current_node.out_ports) == 0)

            return (True, "", None) # This path lead to the output.

        else:
            try:
                c = current_node.out_ports[0]
                next_node = self.nodes[c.out_uuid]
                visited.add(current_node.uuid)
            except:
                return (False,f"{current_node.__class__.__name__} has no output connection",current_node)
            return self.validate(next_node, visited)

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
        
        

    
