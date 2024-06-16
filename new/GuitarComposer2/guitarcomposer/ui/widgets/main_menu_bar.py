"""
Menu that appears at the top of the main window.


"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QApplication,
    QLabel, QToolBar, QStatusBar, QMenu
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt

from guitarcomposer.ui.localization import _




def main_menu_bar(mainwin: QMainWindow, menu_callback):
    menu_bar = mainwin.menuBar()
    
    data = [
        ("File",menu_bar.addMenu( _("File") ), ("New","Open",None,"Exit")), 
        ("Edit",menu_bar.addMenu( _("Edit") ), ("Undo","Redo",None,"Cut","Copy","Paste"))
    ]
    
    class route_cb:
        def __init__(self, evt_name):
            self.evt_name = evt_name
        def __call__(self):
            menu_callback(self.evt_name) 
    
    # file menu and sub menus
    for (mname, menu, subitem_names) in data:
        for name in subitem_names:
            if name:
                 evt_name = "_".join((mname,name,))
                 
                 action = QAction( _(name), mainwin)
                 action.triggered.connect(route_cb(evt_name))
                 menu.addAction(action)
            else:
                 menu.addSeparator()
            
     
    # Create Help menu
    help_menu = QMenu( _("Help"), mainwin)
    about_action = QAction( _("Help"), mainwin)
    about_action.triggered.connect(route_cb("Help"))
    help_menu.addAction(about_action)

    # Add the Help menu to the menu bar, right justified
    menu_bar.setCornerWidget(help_menu, Qt.Corner.TopRightCorner)
    


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QMainWindow()
    def handler(evt_name):
        print(evt_name)
    
    main_menu_bar(window, handler)
    window.show()
    sys.exit(app.exec())



























# event handlers
class main_menu_controller:
    pass
    
    
    
    

class main_menu_bar(QToolBar):
    def __init__(self, mainwin: QMainWindow, controller: main_menu_controller):
        super(QToolBar, self).__init__()
        self.controller = controller

        menu = mainWin.menuBar()
        mainwin.addToolBar(self)

        button_action = QAction("Your button", self)
        button_action.setStatusTip("This is your button")
        button_action.triggered.connect(self.onMyToolBarButtonClick)
        toolbar.addAction(button_action)
        """
        button_action = QAction(QIcon("bug.png"), "&Your button", self)
        button_action.setStatusTip("This is your button")
        button_action.triggered.connect(self.onMyToolBarButtonClick)
        button_action.setCheckable(True)
        toolbar.addAction(button_action)
        """

if __name__ == '__main__':
    controller = main_menu_controller()
    app = QApplication(sys.argv)
    w = MainWindow()
    w.menu_bar = main_menu_bar(w, controller)
    w.show()
    app.exec()

