#!/usr/bin/env python3

from PyQt6.QtGui import QAction, \
                        QPainter, \
                        QPen, \
                        QColor
                        
from PyQt6.QtWidgets import QApplication, \
                            QMainWindow, \
                            QToolBar, \
                            QToolButton, \
                            QSplitter, \
                            QListWidget, \
                            QTabWidget, \
                            QWidget, \
                            QVBoxLayout

from PyQt6.QtCore import Qt


from common.dispatch import DispatchTable, TOPIC_EFFECTS_RACK_DIALOG



class MainWindow(QMainWindow):
    
    def _create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        
        self.new_action = QAction('New', self)
        self.open_action = QAction('Open', self)
        self.save_action = QAction('Save', self)
        self.exit_action = QAction('Exit', self)
        
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
    def _create_tool_bar(self):
        toolbar = QToolBar(self)
        self.addToolBar(toolbar)

       # Create a toggle button
        toggle_button = QToolButton(self)
        toggle_button.setCheckable(True)
        toggle_button.setText('EffectsRack')
        toolbar.addWidget(toggle_button)
        
        # Connect the toggled signal to a slot (function)        
        toggle_button.toggled.connect(\
            lambda clicked: DispatchTable.publish(\
                TOPIC_EFFECTS_RACK_DIALOG, toggle_button, {
                    'clicked': clicked
                }))
                
    def _create_content(self):
        # Create a vertical layout
        layout = QVBoxLayout()

        # Create the first window
        music_comp_win = QWidget()
        music_comp_win_layout = QVBoxLayout()

        # Add a splitter with a QListWidget and a QTabWidget
        splitter = QSplitter(Qt.Orientation.Horizontal)
        list_widget = QListWidget()
        #list_widget.addItems(['Item 1', 'Item 2', 'Item 3'])
        tab_widget = QTabWidget()
        #for i in range(3):
        #    list_widget_tab = QListWidget()
        #    list_widget_tab.addItems(['Subitem 1', 'Subitem 2', 'Subitem 3'])
        #    tab_widget.addTab(list_widget_tab, f'Tab {i+1}')
        splitter.addWidget(list_widget)
        splitter.addWidget(tab_widget)

        music_comp_win_layout.addWidget(splitter)
        music_comp_win.setLayout(music_comp_win_layout)
        
        
    def __init__(self):
        super().__init__()

        self._create_menu_bar()
        self._create_tool_bar()
        self._create_content()

def mainloop():
    app = QApplication([])

    main_win = MainWindow()
    main_win.show()

    app.exec()

if __name__ == '__main__':
    mainloop()
    
