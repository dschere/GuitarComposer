import sys
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QTreeView, QTabWidget, 
    QWidget, QSplitter, QStatusBar, QVBoxLayout, 
)
from PyQt6.QtGui import QAction

class MainWindow(QMainWindow):
    def create_menubar(self):
         # Create the menu bar
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        new_action = QAction("New", self)
        open_action = QAction("Open", self)
        save_action = QAction("Save", self)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()  # Adds a separator line
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        undo_action = QAction("Undo", self)
        redo_action = QAction("Redo", self)
        cut_action = QAction("Cut", self)
        copy_action = QAction("Copy", self)
        paste_action = QAction("Paste", self)

        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(cut_action)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)

        # View menu
        view_menu = menu_bar.addMenu("View")
        fullscreen_action = QAction("Full Screen", self)
        normal_action = QAction("Normal Size", self)

        fullscreen_action.triggered.connect(self.showFullScreen)
        normal_action.triggered.connect(self.showNormal)

        view_menu.addAction(fullscreen_action)
        view_menu.addAction(normal_action)

        # Tools menu
        tools_menu = menu_bar.addMenu("Tools")
        settings_action = QAction("Settings", self)
        options_action = QAction("Options", self)

        #settings_action.triggered.connect(self.show_message)
        #options_action.triggered.connect(self.show_message)

        tools_menu.addAction(settings_action)
        tools_menu.addAction(options_action)

        # Create a toolbar and add some actions
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        #toolbar.addAction(new_action)
        #toolbar.addAction(open_action)
        #toolbar.addAction(save_action)

    def __init__(self):
        super().__init__()

        # Set up the window
        self.setWindowTitle("PyQt6 Splitter Example with Saved State")
        self.setGeometry(100, 100, 800, 600)

        self.create_menubar()

        # Create a toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Create a status bar
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Create the tree view for the left pane
        self.tree_view = QTreeView()

        # Create the tab widget for the top-right pane
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(QWidget(), "Tab 1")
        #self.tab_widget.addTab(QWidget(), "Tab 2")

        # Create a simple QWidget for the bottom-right pane
        self.bottom_widget = QWidget()

        # Create the vertical splitter for the left and right panes
        self.vertical_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.vertical_splitter.addWidget(self.tree_view)

        # Create the horizontal splitter for the right pane (top and bottom)
        self.horizontal_splitter = QSplitter(Qt.Orientation.Vertical)
        self.horizontal_splitter.addWidget(self.tab_widget)
        self.horizontal_splitter.addWidget(self.bottom_widget)
        self.horizontal_splitter.setSizes([300, 100])  # Set initial sizes

        # Add the right pane splitter to the vertical splitter
        self.vertical_splitter.addWidget(self.horizontal_splitter)

        # Set the central widget
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.vertical_splitter)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Restore saved state (window size, splitter sizes)
        self.load_settings()

    def closeEvent(self, event):
        # Save window and splitter state before closing
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self):
        """Save the splitter sizes and window geometry."""
        settings = QSettings("MyCompany", "MyApp")
        settings.setValue("geometry", self.saveGeometry())  # Save window size and position
        settings.setValue("vertical_splitter_state", self.vertical_splitter.saveState())
        settings.setValue("horizontal_splitter_state", self.horizontal_splitter.saveState())

    def load_settings(self):
        """Restore the splitter sizes and window geometry."""
        settings = QSettings("MyCompany", "MyApp")
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.contains("vertical_splitter_state"):
            self.vertical_splitter.restoreState(settings.value("vertical_splitter_state"))
        if settings.contains("horizontal_splitter_state"):
            self.horizontal_splitter.restoreState(settings.value("horizontal_splitter_state"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
