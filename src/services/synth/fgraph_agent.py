"""
The filter graph agent binds a FilterGraph model to a datastructure
in gcsynth so that changes to model are reflected in gcsynth.

The lifecycle of the FilterGraphAgent is linked to the lifecycle of 
the filter graph in gcsynth. When the agent is created a filter graph
is created and when it is destroyed the filter graph is destroyed.

"""
from PyQt6 import QtCore
from models.filterGraph import *

import gcsynth 


## Agents

""" 
Agents represent data structures within the gcsynth extension module. The graphical
data structure for teh filter graph is eventually represented here are agents that
control C data structures. 
"""

class NodeAgent:
    def __init__(self, graph: 'FilterGraphAgent', model : GraphNode, typeid: int):
        self.model = model
        self.graph = graph
        self.handle = model.uuid

        graph_id = graph.handle


        gcsynth.fgraph_api(gcsynth.FG_API_ADD_NODE, graph_id, self.handle, typeid)

    def __del__(self):
        gcsynth.fgraph_api(gcsynth.FG_API_REMOVE_NODE, self.graph.handle, self.handle)


class InputNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : InputNode):
        super().__init__(graph, model, gcsynth.FG_NODE_TYPE_INPUT)


class OutputNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : OutputNode):
        super().__init__(graph, model, gcsynth.FG_NODE_TYPE_OUTPUT)


class SplitterNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : SplitterNode):
        super().__init__(graph, model, gcsynth.FG_NODE_TYPE_SPLITTER)


class MixerNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : GraphNode):
        super().__init__(graph, model, gcsynth.FG_NODE_TYPE_MIXER)

class EffectNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : GraphNode):
        super().__init__(graph, model, gcsynth.FG_NODE_TYPE_EFFECT)

    def setup(self, path: str, label: str):
        "Setup internal ladspa filter"
        fg_uuid = self.graph.handle
        effect_uuid = self.handle          
        cmd = gcsynth.FG_API_EFFECT_SETUP
        gcsynth.fgraph_api(cmd, fg_uuid, effect_uuid, path, label)

    def __del__(self):
        # TODO
        # deallocate ladspa filter
        super().__del__()


class LowPassNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : GraphNode):
        super().__init__(graph, model, gcsynth.FG_NODE_TYPE_LOWPASS)

class HighPassNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : GraphNode):
        super().__init__(graph, model, gcsynth.FG_NODE_TYPE_HIGHPASS)

class BandPassNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : GraphNode):
        super().__init__(graph, model, gcsynth.FG_NODE_TYPE_BANDPASS)


def agent_from_model(graph: 'FilterGraphAgent', model : GraphNode):
    if isinstance(model, SplitterNode):
        return SplitterNodeAgent(graph, model)
    elif isinstance(model, MixerNode):
        return MixerNodeAgent(graph, model)
    elif isinstance(model, EffectNode):
        return EffectNodeAgent(graph, model)
    elif isinstance(model, LowPassNode):
        return LowPassNodeAgent(graph, model)
    elif isinstance(model, HighPassNode):
        return HighPassNodeAgent(graph, model)
    elif isinstance(model, BandPassNode):
        return BandPassNodeAgent(graph, model)
    elif isinstance(model, InputNode):
        return InputNodeAgent(graph, model)
    elif isinstance(model, OutputNode):
        return OutputNodeAgent(graph, model)
    raise TypeError



class FilterGraphAgent(QtCore.QObject):
    updated = QtCore.pyqtSignal(FilterGraph)

    def _add_node(self, gn_model: GraphNode):
        nagent = agent_from_model(self, gn_model)
        self.node_agents[gn_model.uuid] = nagent


    def on_update(self, new_model: FilterGraph):
        report = new_model.diff(self.model)
        if report['change_occured']:
            pass

    def setup(self):
        """ 
        Construct a gcsynth filter graph based on the Filter Graph model. 
        """
        self.input_node = None 
        self.output_node = None

        # setup nodes first.
        for gn_model in self.model.nodes.values():
            nagent = agent_from_model(self, gn_model)
            if isinstance(gn_model, InputNode):
                self.input_node = nagent
            elif isinstance(gn_model, OutputNode):
                self.output_node = nagent
            else:
                self.node_agents[gn_model.uuid] = nagent

        # setup connections.
        for gn_model in self.model.nodes.values():
            for conn_model in gn_model.out_ports:
                in_idx = conn_model.in_idx
                out_idx = conn_model.out_idx
                in_uuid = conn_model.in_uuid
                out_uuid = conn_model.out_uuid

                gcsynth.fgraph_api(
                   gcsynth.FG_API_ADD_CONNECTION, 
                   self.handle, 
                   conn_model.uuid, 
                   in_uuid, 
                   in_idx, 
                   out_uuid, 
                   out_idx)
        
        # filter setup, now enable it.
        gcsynth.fgraph_api(gcsynth.FG_API_ENABLE, self.handle)

    def __init__(self, model : FilterGraph):
        super().__init__()

        self.node_agents = {}
        self.model = model
        self.updated.connect(self.on_update)
        self.handle = model.uuid 
        gcsynth.fgraph_api(gcsynth.FG_API_CREATE, self.handle)

        self.setup()

    def __del__(self):
        if self.handle is not None:
            # first disable this filter.
            #TODO.
            gcsynth.fgraph_api(gcsynth.FG_API_DISABLE, self.handle)

            # remove the nodes 
            for uuid in list(self.node_agents.keys()):
                # cleanup resources.
                del self.node_agents[uuid]
           
            gcsynth.fgraph_api(gcsynth.FG_API_DESTROY, self.handle)




if __name__ == '__main__':
    from services.synth.synthservice import synthservice

    def connect_nodes(gnode1 : GraphNode, out_idx : int, gnode2 : GraphNode, in_idx : int):
        gc = GraphConnection()
        # from left to right
        # output port of gnode1 connected to input port of g2 
        gc.in_uuid = gnode2.uuid
        gc.in_idx = in_idx
        gc.out_uuid = gnode1.uuid
        gc.out_idx = out_idx
        
        try:
            gnode2.in_ports[in_idx] = gc
            gnode1.out_ports[out_idx] = gc
        except:
            print(gnode2)
            print(f"{gnode2.__class__.__name__} {gnode2.in_ports} {in_idx}")
            print(f"{gnode1.out_ports}")
            raise


    s = synthservice()
    s.start()

    from services.effectRepo import EffectRepository

    model = FilterGraph()

    input_node = InputNode()
    output_node = OutputNode()

    input_node.x = 50
    input_node.y = 250
    output_node.x = 600
    output_node.y = 250

    splitter_node = SplitterNode()
    splitter_node.set_num_in_ports(1)
    splitter_node.set_num_out_ports(2)

    repo = EffectRepository()
    effects = repo.getEffects()
    assert(len(effects) > 2)
    

    effect1 = EffectNode(effects[0])
    effect1.set_num_in_ports(1)
    effect1.set_num_out_ports(1)
    
    effect2 = EffectNode(effects[1])
    effect2.set_num_in_ports(1)
    effect2.set_num_out_ports(1)


    mixer_node = MixerNode()
    mixer_node.set_num_in_ports(2)
    mixer_node.set_num_out_ports(1)

    # wire the nodes 
    connect_nodes(input_node, 0, splitter_node, 0)
    connect_nodes(splitter_node, 0, effect1, 0)
    connect_nodes(splitter_node, 1, effect2, 0)
    connect_nodes(effect1, 0, mixer_node, 0)
    connect_nodes(effect2, 0, mixer_node, 1)
    connect_nodes(mixer_node, 0, output_node, 0)


    model.add_node(input_node)
    model.add_node(output_node)
    model.add_node(splitter_node)
    model.add_node(effect1)
    model.add_node(effect2)
    model.add_node(mixer_node)


    fga = FilterGraphAgent(model)
    del fga

    s.stop()
    s.shutdown()