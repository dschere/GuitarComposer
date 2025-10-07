"""
Uses a QStyledItemDelegate to create a widget within the tree view
   <title of song> <close button>

"""

from PyQt6.QtGui import QStandardItemModel, QHelpEvent, QAction, QStandardItem, QColor, QPalette, QIcon
from PyQt6.QtWidgets import (
    QApplication, QStyleOptionFrame, QTreeView, QStyledItemDelegate,
    QStyle, QStyleOptionButton, QLineEdit,QStyleOption, QToolTip
)

from PyQt6.QtCore import QRect, QEvent, QSize, Qt, QModelIndex

from models.song import Song
from view.events import Signals, DeleteTrack




# from PyQt6.QtWidgets import (
#     QApplication, QTreeView, QStyledItemDelegate, QLineEdit,
#     QStyleOptionFrame, QStyleOptionButton, QStyle, QStandardItemModel, QStandardItem
# )
# from PyQt6.QtCore import QRect, Qt
# import sys

class SongDelegate(QStyledItemDelegate):
    CLOSE_TAG = "close"
    ADD_TRACK_TAG = "add"
    REMOVE_TRACK_TAG = "del"

    def __init__(self, parent):
        super().__init__(parent)
        #self.song = song 
        self._parent = parent
        self.button_rects = {}
        self.close_icon_rec = QRect()

    def toolTipText(self, tag):
        return {
            self.CLOSE_TAG: "close song project",
            self.ADD_TRACK_TAG: "add new track",
            self.REMOVE_TRACK_TAG: "remove track"
        }.get(tag,"")
        

    def paint_title_row(self, text, painter, option, index):

        # 1. Draw normal text first
        super().paint(painter, option, index)

        # 2. Define a smaller rectangle for the button inside the cell
        button_rect = QRect(
            option.rect.right() - 16,  # 60px from right edge
            option.rect.top() + 2,
            16,
            16
        )

        self.close_icon_rec = button_rect

        # 3. Create and style the button
        button = QStyleOptionButton()
        button.rect = button_rect
        button.text = ""
        button.icon = QIcon.fromTheme("folder-close")
        button.iconSize = QSize(16, 16)
        button.state = (
            QStyle.StateFlag.State_Enabled |
            QStyle.StateFlag.State_Active
        )

        # add track
        add_button_rect = QRect(
            option.rect.right() - 32,  # 60px from right edge
            option.rect.top() + 2,
            16,
            16
        )
        add_btn = QStyleOptionButton()
        add_btn.rect = add_button_rect
        add_btn.palette.setColor(QPalette.ColorRole.Button, QColor("silver"))
        add_btn.text = "+"
        #        add_btn.icon = QIcon.fromTheme("folder-new")
        add_btn.iconSize = QSize(16, 16)
        add_btn.state = (
            QStyle.StateFlag.State_Enabled |
            QStyle.StateFlag.State_Active
        )
        
        self.button_rects[index] = [
            (button_rect, self.CLOSE_TAG),
            (add_button_rect,self.ADD_TRACK_TAG)
        ]

        # Draw the button after the text
        QApplication.style().drawControl(QStyle.ControlElement.CE_PushButton, button, painter) # type: ignore
        QApplication.style().drawControl(QStyle.ControlElement.CE_PushButton, add_btn, painter) # type: ignore

    def paint_track_row(self, text, painter, option, index):
        # 1. Draw normal text first
        super().paint(painter, option, index)

        # 2. Define a smaller rectangle for the button inside the cell
        button_rect = QRect(
            option.rect.right() - 16,  # 60px from right edge
            option.rect.top() + 2,
            16,
            16
        )

        self.close_icon_rec = button_rect

        # 3. Create and style the button
        button = QStyleOptionButton()
        button.rect = button_rect
        button.text = "-"
        button.palette.setColor(QPalette.ColorRole.Button, QColor("red"))
        button.iconSize = QSize(16, 16)
        button.state = (
            QStyle.StateFlag.State_Enabled |
            QStyle.StateFlag.State_Active
        )

        self.button_rects[index] = [
            (button_rect, self.REMOVE_TRACK_TAG)
        ]

        # Draw the button after the text
        QApplication.style().drawControl(QStyle.ControlElement.CE_PushButton, button, painter) # type: ignore

    def paint(self, painter, option, index):
        #super().paint(painter, option, index)
        text = index.data()
        if text == 'properties':
            super().paint(painter, option, index)
        elif text.startswith('track:'):
            self.paint_track_row(text, painter, option, index)
        else:    
            self.paint_title_row(text, painter, option, index)

    
    def helpEvent(self, event : QHelpEvent, view, option, index):
        if event.type() == QEvent.Type.ToolTip:
            try:
                for b, tag in self.button_rects[index]:
                    if b.contains(event.pos()):
                        # e.g. detect if inside button rect
                        QToolTip.showText(event.globalPos(), self.toolTipText(tag), view)
                        return True        
            except KeyError:
                pass
            QToolTip.hideText()

        return super().helpEvent(event, view, option, index)

    def editorEvent(self, event, model, option, index):
        """Catch mouse clicks in the button area."""
        if event.type() == event.Type.MouseButtonRelease: # type: ignore
            try:
                for (button_rect,tag) in self.button_rects[index]:
                    if not button_rect.contains(event.pos()): # type: ignore
                        continue

                     
                    if tag == self.CLOSE_TAG:
                        Signals.close_song.emit(index.data())
                        return True
                    elif tag == self.ADD_TRACK_TAG:
                        Signals.add_track.emit(index.data())
                        return True
                    elif tag == self.REMOVE_TRACK_TAG:
                        song_title = index.parent().data()
                        song_model = None 
                        i = 0
                        while True:
                            si = model.item(i,0) # type: ignore
                            if si is None:
                                return True 
                            song_model = si.data()
                            if song_model.title == song_title:
                                break
                            i += 1

                        s = song_model 
                        t = s.tracks[index.row()]
                        st = DeleteTrack(s, t)
                        Signals.delete_track.emit(st)
                        return True
                    
            except KeyError:
                pass

        return super().editorEvent(event, model, option, index)

