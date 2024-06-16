import sys
import gettext
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget, QScrollArea, QLabel, QHBoxLayout
)
from PyQt6.QtGui import QAction

from guitarcomposer.ui.config import config
from guitarcomposer.ui.localization import _


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        conf = config()

        # Set up the main window
        self.setWindowTitle(_("PyQt6 App with Tree Widget and Scrolling Canvas"))
        self.setGeometry(conf.main_win.x, conf.main_win.y, conf.main_win.width, conf.main_win.height)

        # Set up the toolbar
        toolbar = QToolBar(_("Guitar Music Composer"))
        self.addToolBar(toolbar)

        # Add a sample action to the toolbar
        action = QAction(_("Sample Action"), self)
        toolbar.addAction(action)

        # Create the central widget and set the layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Create the tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel(_("Tree Widget"))
        self.populate_tree()

        # Create the scrolling canvas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Create a widget to hold the content of the scroll area
        scroll_content = QWidget()
        scroll_content.setGeometry(0, 0, 800, 800)  # Set a large size for demonstration
        scroll_layout = QVBoxLayout(scroll_content)

        # Add some content to the scroll area
        for i in range(10):
            label = QLabel(_("Label {i}").format(i=i))
            scroll_layout.addWidget(label)

        self.scroll_area.setWidget(scroll_content)

        # Add the tree widget and scrolling canvas to the horizontal layout
        layout.addWidget(self.tree_widget)
        layout.addWidget(self.scroll_area)

    def populate_tree(self):
        # Sample tree items
        for i in range(5):
            parent_item = QTreeWidgetItem(self.tree_widget)
            parent_item.setText(0, _("Parent {i}").format(i=i))
            for j in range(3):
                child_item = QTreeWidgetItem(parent_item)
                child_item.setText(0, _("Child {i}.{j}").format(i=i, j=j))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
