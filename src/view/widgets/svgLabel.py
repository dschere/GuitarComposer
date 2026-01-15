from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtSvg import QSvgRenderer
import os


class SvgLabel(QtWidgets.QLabel):
    FILTER_SVG = os.environ['GC_DATA_DIR']+os.sep+'assets'+os.sep+'filter_alt_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg'

    default_width  = 26
    default_height = 26 

    def __init__(self):
        super().__init__()


    def _load_svg_into_label(self, svg_path: str):
        renderer = QSvgRenderer(svg_path)
        if not renderer.isValid():
            return  # handle error as needed

        size = self.size()
        pixmap = QtGui.QPixmap(size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)

        painter = QtGui.QPainter(pixmap)
        # render scaled to label rect
        renderer.render(painter, QtCore.QRectF(0, 0, size.width(), size.height()))
        painter.end()

        self.setPixmap(pixmap)

    def setSvgImage(self, filename, **opts):
        w = opts.get("width", self.default_width)
        h = opts.get("height", self.default_height)
        self.setFixedSize(w, h)
        self._load_svg_into_label(filename)