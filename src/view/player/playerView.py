""" 
widget
  toolbar 
  <play><back measure><skip measure><pause>    <stop> [eq settings]

"""
from typing import List
from PyQt6.QtWidgets import QToolBar, QPushButton, QApplication, QWidget,\
    QVBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from models.song import Song
from models.track import Track
from view.events import Signals, PlayerEvent



class PlayerView(QToolBar):
    
    def create_btn(self, icon, ev_type, tooltip, custom_color = None):
        evt = PlayerEvent() 
        evt.ev_type = ev_type
        evt.tracks = self.tracks_selected 

        class click_handler: 
            def __init__(self, evt):
                self.evt = evt 
            def __call__(self, *args):
                Signals.player_event.emit(self.evt)

        icon = QIcon.fromTheme(icon)
        
        button = QPushButton()
        button.setIcon(icon)
        button.setIconSize(QSize(16, 16))
        button.clicked.connect(click_handler(evt))
        button.setToolTip(tooltip)

        if custom_color:
            css = """
                QPushButton {
                    background-color: %s;
                }                
            """ % custom_color
            button.setStyleSheet(css)

        #button.setEnabled(False)

        self.addWidget(button)
        return button
    

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_track = None | Track
        self.current_song = None | Song
        self.tracks_selected : List[Track] = []

        self.play_btn = self.create_btn("media-playback-start", \
            PlayerEvent.PLAY ,"play")
        self.pause_btn = self.create_btn("media-playback-pause",\
            PlayerEvent.PAUSE,"pause")
        self.forward_btn = self.create_btn("media-seek-forward", \
            PlayerEvent.SKIP_FORWARD_MEASURE ,"skip forward")
        self.backward_btn = self.create_btn("media-seek-backward", 
            PlayerEvent.SKIP_BACKWARD_MEASURE, "skip backward")
        self.stop_btn = self.create_btn("media-playback-stop", 
            PlayerEvent.STOP ,"stop")
        self.play_moment_btn = self.create_btn("text-x-preview",
            PlayerEvent.PLAY_CURRENT_MOMENT, 
            "play the current selection only")
        

        # player settings
        self.settings_btn = QPushButton()
        icon = self.settings_btn.style().standardIcon(\
            self.settings_btn.style().StandardPixmap.SP_FileDialogDetailedView)
        self.settings_btn.setIcon(icon)
        self.settings_btn.setIconSize(QSize(32, 32))
        self.settings_btn.setToolTip("settings")
        
        self.play_moment_event = PlayerEvent(PlayerEvent.PLAY_CURRENT_MOMENT)

        self.play_moment_btn.clicked.connect(self.emit_play_moment_event)

        self.addWidget(self.settings_btn)

    def emit_play_moment_event(self):
        Signals.player_event.emit(self.play_moment_event)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    w = QWidget()
    layout = QVBoxLayout() 
    w.setLayout(layout) 

    viewer = PlayerView()
    layout.addWidget(viewer) 

    w.show()

    sys.exit(app.exec())




        


