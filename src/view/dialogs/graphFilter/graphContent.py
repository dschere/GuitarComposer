
import uuid

from PyQt6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsPathItem
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QToolBar, QHBoxLayout, QGraphicsView, QGridLayout,
                             QGraphicsScene, QTreeWidget, QTreeWidgetItem, QWidget, QLabel, QSplitter, QMenuBar,
                             QGraphicsPathItem, QMenu, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QAction, QBrush, QPen, QColor, QPainterPath, QTransform, QFont

from models.filterGraph import (FilterGraph, GraphConnection, GraphNode, InputNode, OutputNode, SplitterNode, MixerNode, EffectNode, LowPassNode, HighPassNode)
from view.events import Signals



class PortItem(QGraphicsRectItem):
    """ 
    The yellow squares that users can click on to tie filters together
    """
    def __init__(self, parent, port_type, index, radius=6):
        super().__init__(parent)
        self.port_type = port_type # "in" or "out"
        self.index = index
        self.radius = radius
        self.setRect(-radius, -radius, 3*radius, 3*radius)
        self.setBrush(QBrush(QColor("yellow")))
        self.setPen(QPen(QColor("black")))
        self.setAcceptHoverEvents(True)
        self.connections = []

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor("orange")))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor("yellow")))
        super().hoverLeaveEvent(event)

class SceneNodeItem(QGraphicsItem):


    def __init__(self, node_data : GraphNode):
        super().__init__()
        self.node_data = node_data
        self.width = 100

        if isinstance(node_data, EffectNode):
            e : EffectNode = node_data
            self.width = len(e.label()) * 10
            if self.width < 100:
                self.width = 100
            if self.width > 200:
                self.width = 200


        self.height = 60
        self.space_per_port = 30
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        self.inputs = []
        self.outputs = []
        self._create_ports()
        self._prior_rect = None    

        self.setPos(node_data.x, node_data.y)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)    
#        Signals.gnodeSelected.emit(self.node_data)

    def onPortDataUpdated(self, dialog):
        dialog.remove_connections_of_a_node(self)
        for item in self.inputs + self.outputs:
            dialog.scene.removeItem(item)
        
        self._create_ports()
        # force redraw.    
        self.update()

    def _create_ports(self):
        num_in = self.node_data.num_in_ports()
        num_out = self.node_data.num_out_ports()

        if isinstance(self.node_data, SplitterNode) or isinstance(self.node_data, MixerNode):
            needed_height = max(num_in, num_out) * self.space_per_port
            if needed_height != self.height:
                self.prepareGeometryChange()
                self.height = needed_height
        
        # Create input ports
        for i in range(num_in):
            port = PortItem(self, "in", i)
            y = (i + 1) * (self.height / (num_in + 1))
            port.setPos(0, y)
            self.inputs.append(port)
            
        # Create output ports
        for i in range(num_out):
            port = PortItem(self, "out", i)
            y = (i + 1) * (self.height / (num_out + 1))
            port.setPos(self.width, y)
            self.outputs.append(port)

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter : QPainter, option, widget):
        rect = self.boundingRect()
        painter.drawRect(self.boundingRect())
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        if self.isSelected():
            painter.setPen(QPen(QColor("cyan"), 2))
        else:
            painter.setPen(QPen(QColor("black"), 1))
        painter.drawRoundedRect(rect, 5, 5)
        
        painter.setPen(QColor("white"))
        font = QFont()
        font.setBold(True)
        painter.setFont(font)
        
        label = self.node_data.label()
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label) # type: ignore

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.node_data.x = value.x()
            self.node_data.y = value.y()
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for port in self.inputs + self.outputs:
                for connection in port.connections:
                    connection.update_path()
        return super().itemChange(change, value)

class ConnectionItem(QGraphicsPathItem):
    def __init__(self, start_port, end_port):
        super().__init__()
        self.uuid = str(uuid.uuid4())
        self.start_port = start_port
        self.end_port = end_port
        if self.start_port:
            self.start_port.connections.append(self)
        if self.end_port:
            self.end_port.connections.append(self)
        self.setPen(QPen(QColor("white"), 2))
        self.setZValue(-1) # Behind nodes
        self.update_path()

    def update_path(self):
        if not self.start_port or not self.end_port:
            return
        start_pos = self.start_port.scenePos()
        end_pos = self.end_port.scenePos()
        path = QPainterPath()
        path.moveTo(start_pos)
        dx = end_pos.x() - start_pos.x()
        ctrl1 = QPointF(start_pos.x() + dx * 0.5, start_pos.y())
        ctrl2 = QPointF(end_pos.x() - dx * 0.5, end_pos.y())
        path.cubicTo(ctrl1, ctrl2, end_pos)
        self.setPath(path)


class GraphScene(QGraphicsScene):


    def __init__(self, parent=None):
        super().__init__(parent)
        self.temp_line = None
        self.start_port = None
        self.node_items = {} # uuid -> NodeItem
        self.input_node = None
        self.output_node = None


        Signals.graph_node_changed.connect(self.update_node_item)

    def clear(self):
        super().clear()
        self.node_items = {}
        self.input_node = None
        self.output_node = None
        self.temp_line = None
        self.start_port = None
        self.update()

    def mousePressEvent(self, event):
        items = self.items(event.scenePos()) # type: ignore
        port = None
        for item in items:
            if isinstance(item, SceneNodeItem):
                node_item : SceneNodeItem = item
                gnode = node_item.node_data
                Signals.graph_node_selected.emit(gnode)
                

            if isinstance(item, PortItem):
                port = item
                break
        
        if port:
            if port.connections:
                if self.parent():
                    for conn in list(port.connections):
                        self.parent().remove_connection(conn) # type: ignore
                event.accept() # type: ignore
                return

            self.start_port = port
            self.temp_line = QGraphicsPathItem()
            self.temp_line.setPen(QPen(QColor("white"), 2, Qt.PenStyle.DashLine))
            self.addItem(self.temp_line)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.temp_line and self.start_port:
            path = QPainterPath()
            path.moveTo(self.start_port.scenePos())
            path.lineTo(event.scenePos()) # type: ignore
            self.temp_line.setPath(path)
            event.accept() # type: ignore
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.temp_line and self.start_port:
            items = self.items(event.scenePos()) # type: ignore
            end_port = None
            for item in items:
                if isinstance(item, PortItem):
                    end_port = item
                    break
            
            if end_port and end_port != self.start_port:
                if self.parent():
                    self.parent().create_connection(self.start_port, end_port) # type: ignore
            
            self.removeItem(self.temp_line)
            self.temp_line = None
            self.start_port = None
            event.accept() # type: ignore
        else:
            super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        
        node_item = item
        while node_item and not isinstance(node_item, SceneNodeItem):
            node_item = node_item.parentItem()
            
        if isinstance(node_item, SceneNodeItem):
            if isinstance(node_item.node_data, InputNode) or isinstance(node_item.node_data, OutputNode):
                return

            if self.parent():
                self.parent().remove_node(node_item)

            event.accept()
        else:
            super().contextMenuEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            for item in self.selectedItems():
                if isinstance(item, SceneNodeItem):
                    if isinstance(item.node_data, InputNode) or isinstance(item.node_data, OutputNode):
                        return
                    if self.parent():
                        self.parent().remove_node(item)
                elif isinstance(item, ConnectionItem):
                    if self.parent():
                        self.parent().remove_connection(item)
            event.accept()
        else:
            super().keyPressEvent(event)

    def add_node_item(self, node_data : GraphNode) -> SceneNodeItem:
        item = SceneNodeItem(node_data)
        self.addItem(item)
        self.node_items[node_data.uuid] = item    
        return item

    def update_node_item(self, node_data : GraphNode):
        if node_data.uuid in self.node_items:            
            item = self.node_items[node_data.uuid]  
            self.removeItem(item)
            self.add_node_item(node_data)


    def connect_nodes(self, uuid1, out_idx, uuid2, in_idx):
        node1 = self.node_items[uuid1]
        node2 = self.node_items[uuid2]

        port1 = node1.outputs[out_idx]
        port2 = node2.inputs[in_idx]

        gnode1 : GraphNode = node1.node_data
        gnode2 : GraphNode = node2.node_data

        port2_usage = gnode2.in_ports[in_idx].inuse()
        if port2_usage:
            return

        conn = ConnectionItem(port1, port2)
        self.addItem(conn)

        gc = GraphConnection()
        # from left to right
        # output port of gnode1 connected to input port of g2 
        gc.in_uuid = gnode2.uuid
        gc.in_idx = in_idx
        gc.out_uuid = gnode1.uuid
        gc.out_idx = out_idx
        
        gnode2.in_ports[in_idx] = gc
        gnode1.out_ports[out_idx] = gc


        #print(f"connect_nodes: connected {gnode1.__class__.__name__}'s output port {gc.in_idx} to {gnode2.__class__.__name__}'s input port {gc.out_idx} ")




class GraphView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.scene : QGraphicsScene = scene
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self._first_show = True



    def showEvent(self, event):
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            sbar = self.horizontalScrollBar()
            if sbar:
                sbar.setValue(0)
            vbar = self.verticalScrollBar()
            if vbar:
                vbar.setValue(0)
                