import sys
import gettext
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget, QScrollArea, QLabel, QHBoxLayout, QSplitter
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from guitarcomposer.ui.widgets.main_menu_bar import main_menu_bar
from guitarcomposer.ui.config import config
from guitarcomposer.ui.localization import _

from guitarcomposer.ui.widgets.main_left_pane import main_left_pane


class MainWindow(QMainWindow):
    
    
    def __init__(self):
        super().__init__()
        conf = config()
        
        # create menu bar
        main_menu_bar(self)

        # Set up the main window
        self.setWindowTitle(_("Guitar Composer"))
        self.setGeometry(conf.main_win.x, conf.main_win.y, conf.main_win.width, conf.main_win.height)


        # Create the central widget and set the layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create the tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel(_("Compositions"))
        self.populate_tree()
        
        tree_scroll = QScrollArea()
        tree_scroll.setWidgetResizable(True)
        tree_scroll.setWidget(self.tree_widget)
        
        splitter.addWidget(tree_scroll)

        # Create the scrolling canvas
        self.editor_tabs = main_left_pane()
        self.editor_tabs.add_new_tab("<song name>", QLabel("score editor goes here"))
        splitter.addWidget(self.editor_tabs)
        
        # Add the tree widget and scrolling canvas to the horizontal layout
        layout.addWidget(splitter)
        
        # set initial position of splitter
        total_width = self.width()
        left_size = int(total_width * 0.17)
        right_size = total_width - left_size
        splitter.setSizes([left_size, right_size])
        

    def populate_tree(self):
        """
        List songs here
          <song name>
            - score
            - audio files
        """
        # dummy data        
        parent_item = QTreeWidgetItem(self.tree_widget)
        parent_item.setText(0, "<song name>")
        score_item = QTreeWidgetItem(parent_item)
        score_item.setText(0, "score")
        audio_item = QTreeWidgetItem(parent_item)
        audio_item.setText(0, "audio files")
        
        afile_item = QTreeWidgetItem(audio_item)
        afile_item.setText(0, "recording1.wav")
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
