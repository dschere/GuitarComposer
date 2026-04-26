""" 
Filter Graph Dialog

Allows user to perform CRUD operations on a filter graph.  

"""

import copy
import uuid
import pickle
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QInputDialog, QFileDialog, QLineEdit, QToolBar, QHBoxLayout, QGraphicsView, QGridLayout,
                             QGraphicsScene, QTreeWidget, QTreeWidgetItem, QWidget, QLabel, QSplitter, QMenuBar,
                             QGraphicsPathItem, QMenu, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QAction, QPen, QColor, QPainterPath, QTransform

from models.filterGraph import (FilterGraph, GraphConnection, GraphNode, InputNode, 
                                OutputNode, SplitterNode, MixerNode, EffectNode, LowPassNode, 
                                HighPassNode, BandPassNode, GainBalanceNode)

from view.dialogs.graphFilter.effectsLibraryTree import EffectsLibrary
from view.dialogs.graphFilter.graphContent import GraphView, GraphScene
from view.dialogs.graphFilter.nodeProperties import PropertiesPanel
from view.dialogs.graphFilter.preview import FGPreviewToolbar

from models.effect import EffectParameter
from services.effectRepo import EffectRepository
from util.popup import show_alert, ask_question
from services.modelManager import ModelManager





class FilterGraphDialog(QDialog):


    def on_remove_preset(self):
        yes = ask_question(self, "Delete Preset", "DO YOU WISH TO DELETE THIS PRESET")
        if not yes:
            return

        assert(self.preset_submenu)
        preset = self.model.preset
        self.store.remove_model(preset)
        self.create_new_graph()
        for action in self.preset_submenu.actions():
            if action.text() == preset:
                self.preset_submenu.removeAction(action)


    def on_load(self, preset_name):
        model = self.store.get_model(preset_name)
        self.setModel(model)

    def add_preset_submenu(self, preset_name):
        action = QAction(preset_name, self)
        assert(self.preset_submenu)
        self.preset_submenu.addAction(action)
        action.triggered.connect(lambda checked=False, name=preset_name: self.on_load(name))


    def create_menu_bar(self) -> QMenuBar:
        menu_bar = QMenuBar()
        # File menu
        self.file_menu = menu_bar.addMenu("File")
        save_action = QAction("Save Preset", self)
        assert(self.file_menu)
        assert(save_action)
        
        self.file_menu.addAction(save_action)

        presets = self.store.get_presets()
        self.preset_submenu = self.file_menu.addMenu("Presets")
        assert(self.preset_submenu)

        if len(presets) > 0:
            presets.sort()    
            for preset in presets:
                self.add_preset_submenu(preset)

        remove_action = QAction("Remove Preset", self)
        self.file_menu.addAction(remove_action)


        save_action.triggered.connect(self.on_save)
        remove_action.triggered.connect(self.on_remove_preset)


        return menu_bar

    def create_connection(self, start_port, end_port):
        start_node = start_port.parentItem().node_data
        end_node = end_port.parentItem().node_data

        conn = self.graph_scene.connect_nodes(start_node.uuid, start_port.index, end_node.uuid, end_port.index)
        if conn:
            self.model.add_connection(conn)
        self.on_model_change()

        return conn


    def remove_connection(self, connection):
        start_node = connection.start_port.parentItem().node_data
        start_port = connection.start_port.index
        end_node = connection.end_port.parentItem().node_data
        end_port = connection.end_port.index

        start_node.out_ports[start_port].clear()
        end_node.in_ports[end_port].clear()

        if connection.start_port and connection in connection.start_port.connections:
            connection.start_port.connections.remove(connection)
        if connection.end_port and connection in connection.end_port.connections:
            connection.end_port.connections.remove(connection)

        self.graph_scene.removeItem(connection)        
        self.model.remove_connection(connection.uuid)
        self.on_model_change()

    def remove_node(self, node_item):
        for port in node_item.inputs + node_item.outputs:
            for conn in list(port.connections):
                self.remove_connection(conn)

        self.graph_scene.removeItem(node_item)
        if node_item.node_data.uuid in self.graph_scene.node_items:
            del self.graph_scene.node_items[node_item.node_data.uuid]
            if node_item.node_data.uuid in self.model.nodes:
                self.model.nodes.pop(node_item.node_data.uuid)

        self.on_model_change()
    
    def getModel(self) -> FilterGraph:
        return self.model
    
    def setModel(self, model: FilterGraph):
        self.model = model
        self.graph_scene.clear()
        self.properties_panel.clear()

        gnode_uuid_2_scene_node = {}
        for gnode in model.nodes.values():
            item = self.graph_scene.add_node_item(gnode)
            gnode_uuid_2_scene_node[gnode.uuid] = item


        for gnode in model.nodes.values():
            for (in_idx,conn_model) in enumerate(gnode.out_ports):
                cm : GraphConnection = conn_model 
                # scene_node1 = gnode_uuid_2_scene_node[cm.in_uuid]
                # scene_node2 = gnode_uuid_2_scene_node[cm.out_uuid]

                # self.graph_scene.connect_nodes(scene_node1.uuid, cm.out_idx, scene_node2.out_uuid, cm.in_idx)
                self.graph_scene.connect_nodes(cm.in_uuid, cm.in_idx, cm.out_uuid, cm.out_idx)

        self.on_model_change()

    def on_save(self):
        preset_name, ok = QInputDialog.getText(self, 'Preset Name', 'Enter preset name:')
        if not ok:
            return
        
        if preset_name == "":
            show_alert(self, text="No preset name provided", icon="error")
            return

        existing_presets = self.store.get_presets()
        if preset_name in existing_presets:
            yes = ask_question(self, "Preset already exists", "Do you wish to overwrite?")
            if not yes:
                return

        self.model.preset = preset_name
        self.store.add_model(self.model)
        self.on_model_change()
        self.add_preset_submenu(preset_name)
        

    def create_new_graph(self):
        self.graph_scene.clear()
        self.properties_panel.clear()
        self.model = FilterGraph()

        self.input_node = InputNode()
        self.output_node = OutputNode()

        self.input_node.x = 50
        self.input_node.y = 250
        self.output_node.x = 600
        self.output_node.y = 250

        self.model.add_node(self.input_node)
        self.model.add_node(self.output_node)
        
        self.graph_scene.add_node_item(self.input_node)
        self.graph_scene.add_node_item(self.output_node)

        gc = self.graph_scene.connect_nodes(self.input_node.uuid, 0, self.output_node.uuid, 0)
        if not gc:
            raise RuntimeError("Unable to create default filter graph")
    
        self.model.add_connection(gc)
        self.on_model_change()

        print(f"after create_new_graph {self.model.connections}")
        for conn_model in self.model.connections.values():
            print(type(conn_model))
            conn_model.pretty_print(self.model)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        pos = self.graph_view.mapToScene(event.position().toPoint())
        gnode = self.graph_nodes_selection.getSelectedItem() 
        if gnode is None:
            return
        
        gnode.x = pos.x()
        gnode.y = pos.y()
        
        self.model.add_node(gnode)
        self.on_model_change()
        self.graph_scene.add_node_item(gnode)
        self.properties_panel.setup(gnode)
        event.accept()
        

    def dragMoveEvent(self, event):
        event.accept()

 
    def __init__(self):
        super().__init__()
        self.model = FilterGraph()
        self.store = ModelManager()

        self.setWindowTitle("Filter Graph Editor")
        self.setMinimumWidth(1400)
        
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        menu_bar = self.create_menu_bar()
        main_layout.addWidget(menu_bar)

        self.preview_tb = FGPreviewToolbar(self.model)
        main_layout.addWidget(self.preview_tb)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # right side of splitter
        self.graph_nodes_selection = EffectsLibrary()
        splitter.addWidget(self.graph_nodes_selection)

        # center is the interactive filter graph. 
        self.graph_scene = GraphScene(self)
        self.graph_view = GraphView(self.graph_scene)
        self.graph_scene.setSceneRect(0, 0, 2000, 2000)
        splitter.addWidget(self.graph_view)

        # Event filters/handlers for drag and drop on the view
        self.graph_view.dragEnterEvent = self.dragEnterEvent
        self.graph_view.dragMoveEvent = self.dragMoveEvent
        self.graph_view.dropEvent = self.dropEvent

        # left side of splitter is the properties of 
        # graph nodes. 
        self.properties_panel = PropertiesPanel()
        splitter.addWidget(self.properties_panel)


        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

    # def regenerate_model(self):
    #     """
    #     Clear self.model then rebuild based on the objects in the graph scene. 
    #     """
    #     new_model = FilterGraph()

    #     # 1. Collect all GraphNode objects from the SceneNodeItem's node_data
    #     #    and add them to the new model. We deepcopy each GraphNode to ensure
    #     #    new, independent instances are created, including their internal
    #     #    port lists and any embedded GraphConnection objects.
    #     #    This also captures the current visual position (x, y) from the scene item.
    #     original_uuid_to_new_node = {}
    #     for scene_node_item in self.graph_scene.node_items.values():
    #         original_gnode = scene_node_item.node_data
    #         new_gnode = copy.deepcopy(original_gnode)
    #         new_model.add_node(new_gnode)
    #         original_uuid_to_new_node[original_gnode.uuid] = new_gnode

    #     # 2. Iterate through the newly added GraphNodes in new_model to populate
    #     #    new_model.connections with their associated GraphConnection objects.
    #     #    The deepcopy operation already copied the GraphConnection objects into
    #     #    the new_gnode's in_ports and out_ports. We just need to ensure
    #     #    these copied connections are also registered in the FilterGraph's
    #     #    central connections dictionary.
    #     for new_gnode in new_model.nodes.values():
    #         for conn_model in new_gnode.out_ports:
    #             if conn_model.inuse():
    #                 # FilterGraph.add_connection will add the GraphConnection to new_model.connections
    #                 # and also re-establish the in_ports/out_ports references within new_model's nodes.
    #                 new_model.add_connection(conn_model)

    #     self.model.nodes = new_model.nodes
    #     self.model.connections = new_model.connections


    def on_model_change(self):
        (valid, errmsg, eo) = self.model.validate(None, set())
        if not valid:
            self.preview_tb.disable_preview()
            self.preview_tb.set_errmsg(errmsg)
        else:
            self.preview_tb.set_model(self.model)
            self.preview_tb.enable_preview()
            self.preview_tb.set_errmsg("")
        #print("model changed >>>>>>>")
        #self.model.pretty_print()    
            

            

def unittest():
    import sys
    from PyQt6.QtWidgets import QApplication
    import qdarktheme
    from services.synth.synthservice import synthservice
   
    ss = synthservice()
    ss.start()

    app = QApplication(sys.argv)
    # Apply dark theme
    theme = qdarktheme.load_stylesheet('dark')
    app.setStyleSheet(theme)

    window = FilterGraphDialog()
    window.create_new_graph()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    unittest()