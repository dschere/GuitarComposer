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



class NodeAgent:

    
    def __init__(self, graph: 'FilterGraphAgent', model : GraphNode, typeid: int):
        self.model = model
        self.graph = graph
        self.handle = model.uuid

        graph_id = graph.handle

        gcsynth.fgraph_api(gcsynth.FG_API_ADD_NODE, graph_id, typeid, self.handle)

class InputNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : InputNode):
        super().__init__(graph, model, gcsynth.FG_INPUT)


class OutputNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : OutputNode):
        super().__init__(graph, model, gcsynth.FG_OUTPUT)


class SplitterNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : SplitterNode):
        super().__init__(graph, model, gcsynth.FG_SPLITTER)


class MixerNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : GraphNode):
        super().__init__(graph, model, gcsynth.FG_MIXER)

class EffectNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : GraphNode):
        super().__init__(graph, model, gcsynth.FG_EFFECT)

class LowPassNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : GraphNode):
        super().__init__(graph, model, gcsynth.FG_LOW_PASS)

class HighPassNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : GraphNode):
        super().__init__(graph, model, gcsynth.FG_HIGH_PASS)

class BandPassNodeAgent(NodeAgent):
    def __init__(self, graph: 'FilterGraphAgent', model : GraphNode):
        super().__init__(graph, model, gcsynth.FG_BAND_PASS)


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
        self.input_node = None 
        self.output_node = None

        # setup nodes first.
        self.node_agents = {}
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
                gcsynth.fgraph_api(gcsynth.FG_API_ADD_CONNECTION, 
                    self.handle, in_uuid, in_idx, out_uuid, out_idx)
        

    def __init__(self, model : FilterGraph):
        super().__init__()

        self.model = model
        self.updated.connect(self.on_update)
        self.handle = model.uuid 
        gcsynth.fgraph_api(gcsynth.FG_API_CREATE, self.handle)

        self.setup()

    def __del__(self):
        if self.handle is not None:
            gcsynth.fgraph_api(gcsynth.FG_API_DESTROY, self.handle)




if __name__ == '__main__':
    from services.synth.synthservice import synthservice

    s = synthservice()
    s.start()
    
    model = FilterGraph()
    fga = FilterGraphAgent(model)
    del fga

    s.stop()
    s.shutdown()