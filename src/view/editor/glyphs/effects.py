from typing import Dict, List, Tuple
from models.effect import Effect
from models.param import EffectParameter
from view.editor.glyphs.common import (
        STAFF_SYM_WIDTH,
        EFFECTS_SYM_HEIGHT 
    )

from view.editor.glyphs.canvas import Canvas
from models.track import TabEvent
from PyQt6.QtGui import QIcon, QKeyEvent, QMouseEvent, QPixmap, QImage
from PyQt6.QtCore import Qt

from view.dialogs.effectsControlDialog.dialog import ( 
    EffectsDialog, EffectPreview, EffectChangeEvent)


EffectChanges = Dict[Effect, List[Tuple[str, EffectParameter]]]
    


from view.editor.trackEditorView import TrackEditorData
from PyQt6 import QtGui
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton
from view.events import Signals



def invert_pixmap(pixmap):
    image = pixmap.toImage()
    image.invertPixels()
    return QPixmap.fromImage(image)

class EffectsGlyph(QLabel):


    def set_icon(self):
        e = self.te.getEffects()
        w,h = self.width(),self.height()
        preset = "audio-card"
        
        icon = QIcon.fromTheme(preset)
        assert(icon)
        pixmap = icon.pixmap(int(w/2),int(h/2)) 
        if e:
            pixmap = invert_pixmap(pixmap)
        self.setPixmap(pixmap)
        self.setAlignment(Qt.AlignmentFlag.AlignBottom |Qt.AlignmentFlag.AlignCenter )
        

    def on_eff_preview(self, evt: EffectPreview):
        Signals.preview_effect.emit(evt)
        
        
    def on_eff_update(self, evt: EffectChangeEvent):
        self.te.setEffects(evt.effects)
        self.dialog.close() 
        self.dialog_being_shown = False
        self.set_icon()

    def show_dialog(self):
        track_model = TrackEditorData().get_active_track_model()
        assert(track_model != None) 

        # get the effects settings for this tab event within the 
        # track. 
        e = track_model.get_effects(self.te)

        self.dialog = EffectsDialog(self, e)
        self.dialog.effect_preview.connect(self.on_eff_preview)
        self.dialog.effect_updated.connect(self.on_eff_update)
        self.dialog.exec()
        self.dialog_being_shown = True

    def mousePressEvent(self, ev: QMouseEvent | None) -> None:
        if not self.dialog_being_shown:
            self.show_dialog()
        return super().mousePressEvent(ev)         

    def __init__(self, te: TabEvent):
        super().__init__()
        w,h = STAFF_SYM_WIDTH, EFFECTS_SYM_HEIGHT
        self.setFixedHeight(h) 
        self.setFixedWidth(w)

        self.te = te 
        self.dialog_being_shown = False
        self.setToolTip("effects")

        self.set_icon()

        
        