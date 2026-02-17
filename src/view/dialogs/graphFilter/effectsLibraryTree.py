
import uuid
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QToolBar, QHBoxLayout, QGraphicsView, QGridLayout,
                             QGraphicsScene, QTreeWidget, QTreeWidgetItem, QWidget, QLabel, QSplitter, QMenuBar,
                             QGraphicsPathItem, QMenu, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QAction, QPen, QColor, QPainterPath, QTransform

from models.filterGraph import FilterGraph, BandPassNode, GainBalanceNode, GraphNode, InputNode, OutputNode, SplitterNode, MixerNode, EffectNode, LowPassNode, HighPassNode

from services.effectRepo import EffectRepository


class EffectsLibrary(QWidget):
# GraphNode type map.
    gnode_tmap = {
        "Input": InputNode,
        "Output": OutputNode,
        "Effect": EffectNode,
        "Splitter": SplitterNode,
        "Mixer": MixerNode,
        "Low Pass": LowPassNode,
        "High Pass": HighPassNode,
        "Band Pass": BandPassNode,
        "Gain Balance": GainBalanceNode
    }

    # set of labels that are draggable. 
    drag_item_labels = set(gnode_tmap.keys()) - set(['Effect'])
    # effect objects grouped by effect class
    effects_classes = {}
    effect_labels = set()

    def setup_effect_models(self):
        e_repo = EffectRepository()
        effectList = e_repo.getEffects()
        self.effects_classes = {}
        for e in effectList:
            eclass = e.get_eclass()
            labels = self.effects_classes.get(eclass, [])
            labels.append(e.plugin_label())
            self.drag_item_labels.add(e.plugin_label())
            self.effect_labels.add(e.plugin_label())
            self.effects_classes[eclass] = labels

    def getSelectedItem(self) -> GraphNode | None:
        items = self.library_list.selectedItems()
        if not items:
            return
        
        text = items[0].text(0)
        if text not in self.drag_item_labels:
            return

        klass = self.gnode_tmap.get(text, None)
        if klass:
            return klass()
        elif text in self.effect_labels:
            e_repo = EffectRepository()
            effect = e_repo.getEffect(text)
            return EffectNode(effect)
        else:
            return None
        


    def make_effect_branches(self, effect_item, e_class):
        """
        Creates the subbranch below 'effect' 
        """
        e_class_branch = QTreeWidgetItem(effect_item, [e_class])
        labels = self.effects_classes.get(e_class, [])
        labels.sort()
        for label in labels:
            QTreeWidgetItem(e_class_branch, [label])

    def __init__(self):
        super().__init__()
        self.setup_effect_models()
        layout = QVBoxLayout() 

        self.library_list = QTreeWidget()
        self.library_list.setHeaderHidden(True)
        self.library_list.setDragEnabled(True)

        effect_item = QTreeWidgetItem(self.library_list, ["Effect"])
        for e_class in self.effects_classes:
            if e_class != 'other':
                self.make_effect_branches(effect_item, e_class)   
        self.make_effect_branches(effect_item, 'other')            
        effect_item.setExpanded(True)

        QTreeWidgetItem(self.library_list, ["Splitter"])
        QTreeWidgetItem(self.library_list, ["Mixer"])
        QTreeWidgetItem(self.library_list, ["Low Pass"])
        QTreeWidgetItem(self.library_list, ["High Pass"])
        QTreeWidgetItem(self.library_list, ["Band Pass"])
        QTreeWidgetItem(self.library_list, ["Gain Balance"])

        self.setMinimumHeight(400)
        self.setMinimumWidth(200)
            
        layout.addWidget(self.library_list)
        self.setLayout(layout)
        

