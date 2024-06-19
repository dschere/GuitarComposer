"""
Left side of the splitter window in the main window.

1. Contains a note/suration picker
2. An editor for each track

3. A track navigator that scrolls (.2)
"""
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QInputDialog, QTabBar
)
from PyQt6.QtCore import Qt


class song_tab_widget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setTabsClosable(True)
        self.setMovable(True)

        self.tabCloseRequested.connect(self.close_tab)
        self.tabBarDoubleClicked.connect(self.edit_tab_title)

    def close_tab(self, index):
        if self.count() > 1:
            self.removeTab(index)

    def edit_tab_title(self, index):
        current_title = self.tabText(index)
        new_title, ok = QInputDialog.getText(self, "Edit Song Title", "New Song Title:", QLineEdit.EchoMode.Normal, current_title)
        if ok and new_title:
            self.setTabText(index, new_title)


class main_left_pane(QWidget):
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout()
        self.tab_widget = song_tab_widget()
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)  
    
    def add_new_tab(self, title, tab_content):
        new_tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(tab_content)
        new_tab.setLayout(layout)
        self.tab_widget.addTab(new_tab, title)

    
