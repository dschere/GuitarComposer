import sys
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QTabWidget,
    QWidget, QSplitter, QStatusBar, QVBoxLayout, QFileDialog,
    QMenuBar, QMenu
)
from PyQt6.QtGui import QAction, QKeyEvent, QMouseEvent

from view.fretboard_view import fretboard_view

from view.events import (Signals, EditorEvent)
from view.config import ORAGANIZATION, APP_NAME
from view.config import EditorKeyMap


from view.projectNavigator.navigator import Navigator
from view.editor.trackEditorView import TrackEditorView
import logging
from controllers.editorcontroller import EditorController
from view.player.playerView import PlayerView
import signal


class MainWindow(QMainWindow):    
    def saveSong(self):
        Signals.save_song.emit()

    def saveAsSong(self):
        Signals.save_as_song.emit()

    def openSong(self):
        Signals.open_song.emit()

    def newSong(self):
        Signals.new_song.emit()

    def closeSong(self):
        Signals.close_song.emit()   

    def undoEdit(self):
        evt = EditorEvent(EditorEvent.UNDO_EVENT)
        Signals.editor_event.emit(evt)
        
    def redoEdit(self):
        evt = EditorEvent(EditorEvent.REDO_EVENT)
        Signals.editor_event.emit(evt)

    def create_menubar(self):
        # Create the menu bar
        menu_bar : QMenuBar | None = self.menuBar()
        assert(menu_bar)
        # File menu
        file_menu : QMenu | None = menu_bar.addMenu("File")
        assert(file_menu)

        new_action = QAction("New", self)
        new_action.triggered.connect(self.newSong)  

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.openSong) 

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.saveSong)   

        saveas_action = QAction("SaveAs", self)
        saveas_action.triggered.connect(self.saveAsSong)   

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(saveas_action)
        file_menu.addSeparator()  # Adds a separator line
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu : QMenu | None = menu_bar.addMenu("Edit")
        assert(edit_menu)

        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self.undoEdit)
        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(self.redoEdit)

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
        view_menu : QMenu | None = menu_bar.addMenu("View")
        assert(view_menu)
        fullscreen_action = QAction("Full Screen", self)
        normal_action = QAction("Normal Size", self)

        fullscreen_action.triggered.connect(self.showFullScreen)
        normal_action.triggered.connect(self.showNormal)

        view_menu.addAction(fullscreen_action)
        view_menu.addAction(normal_action)

        # Tools menu
        tools_menu : QMenu | None = menu_bar.addMenu("Tools")
        assert(tools_menu)
        settings_action = QAction("Settings", self)
        options_action = QAction("Options", self)

        # settings_action.triggered.connect(self.show_message)
        # options_action.triggered.connect(self.show_message)

        tools_menu.addAction(settings_action)
        tools_menu.addAction(options_action)

    _ctrl_key_pressed = False
    _shift_key = False
    _arrow_keys = (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        editor_keymap = EditorKeyMap()
        key = event.key()
        mod = event.modifiers()
        
        if mod == Qt.KeyboardModifier.NoModifier:
            self._ctrl_key_pressed = False
        
        if Qt.Key.Key_Shift == key:
            self._shift_key = False
        # generate key event for right/left arrows on key release
        elif key in self._arrow_keys:
            e_evt = EditorEvent()
            e_evt.ev_type = EditorEvent.KEY_EVENT
            e_evt.key = key
            e_evt.control_key_pressed = self._ctrl_key_pressed
            Signals.editor_event.emit(e_evt) 
        
        elif mod & Qt.KeyboardModifier.ControlModifier:
            if key == editor_keymap.UNDO:
                self.undoEdit()
            elif key == editor_keymap.REDO:
                self.redoEdit()    


            
        return super().keyReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        editor_keymap = EditorKeyMap()
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._ctrl_key_pressed = True
        elif event.modifiers() & Qt.KeyboardModifier.AltModifier:
            pass
        else:
            key = event.key()
            if key in self._arrow_keys:
                pass
            elif key == Qt.Key.Key_Shift:
                self._shift_key = True
            else:
                if not self._shift_key and ord('Z') >= key >= ord('A'):     
                    key += 32 # make lower case

                e_evt = EditorEvent()
                e_evt.ev_type = EditorEvent.KEY_EVENT
                e_evt.key = key
                e_evt.control_key_pressed = self._ctrl_key_pressed
                Signals.editor_event.emit(e_evt)

    def __init__(self, ec: EditorController ):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Set up the window
        self.setWindowTitle("Guitar Music Composer")
        self.setGeometry(100, 100, 800, 600)

        self.create_menubar()

        # Create a toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        pv = PlayerView(self) 
        toolbar.addWidget(pv) 


        # Create a status bar
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Create the tree view for the left pane
        # self.tree_view = QTreeView()
        self.tree_view = Navigator()

        # Create the tab widget for the top-right pane
        #self.tab_widget = QTabWidget()

        #self.tab_widget.addTab(TrackEditor(), "Tab 1")
        self.track_editor = TrackEditorView()
        ec.set_editor(self.track_editor)
        # self.tab_widget.addTab(QWidget(), "Tab 2")

        # Create a simple QWidget for the bottom-right pane
        # FINDME
        # self.bottom_widget = QWidget()
        self.bottom_widget = fretboard_view()

        # Create the vertical splitter for the left and right panes
        self.vertical_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.vertical_splitter.addWidget(self.tree_view)

        # Create the horizontal splitter for the right pane (top and bottom)
        self.horizontal_splitter = QSplitter(Qt.Orientation.Vertical)
        self.horizontal_splitter.setHandleWidth(0)
        
        self.horizontal_splitter.addWidget(self.track_editor)
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
        # instruct the os to send this process the a SIGNALRM
        # in a second to make sure the app doesn't get stuck.
        signal.alarm(1)
        super().closeEvent(event)
        

    def save_settings(self):
        """Save the splitter sizes and window geometry."""
        settings = QSettings(ORAGANIZATION, APP_NAME)
        # Save window size and position
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("vertical_splitter_state",
                          self.vertical_splitter.saveState())
        settings.setValue("horizontal_splitter_state",
                          self.horizontal_splitter.saveState())

        Signals.save_settings.emit(settings)

    def load_settings(self):
        """Restore the splitter sizes and window geometry."""
        settings = QSettings(ORAGANIZATION, APP_NAME)
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.contains("vertical_splitter_state"):
            self.vertical_splitter.restoreState(
                settings.value("vertical_splitter_state"))
        if settings.contains("horizontal_splitter_state"):
            self.horizontal_splitter.restoreState(
                settings.value("horizontal_splitter_state"))

        Signals.load_settings.emit(settings)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
