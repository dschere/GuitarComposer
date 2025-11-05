from typing import List, Tuple
from models.measure import TabEvent
from view.editor.tabEventPresenter import TabEventPresenter
from singleton_decorator import singleton
from models.track import Track
from models.measure import TUPLET_DISABLED, TupletTypes

from view.dialogs.msgboxes import alert
from PyQt6.QtWidgets import QWidget

@singleton
class PasteBufferSingleton:
    highlighted_items : List[TabEventPresenter] = [] 
    active = False
    tab_items : List[TabEvent] = []

    def __init__(self):
        super().__init__()

    def clear(self):
        for item in self.highlighted_items:
            item.clear_copy_highlight()
        self.highlighted_items : List[TabEventPresenter] = []

    def get_tab_events(self) -> List[TabEvent]:
        return [item.get_tab_event() for item in self.highlighted_items]    

    def isEmpty(self):
        return len(self.highlighted_items) == 0
    
    def append(self, item: TabEventPresenter):
        self.tab_items : List[TabEvent] = []
        self.highlighted_items.append(item)

    def activate(self):
        self.active = True 

    def deactivate(self):
        self.active = False

    def isActive(self):
        return self.active
    
    def validate(self, tab_events: List[TabEvent]) -> Tuple[bool, str]:
        """ scan tab_items to ensure that only complete tuplets/triplets
            can be copy/pasted. 
        """
        valid = True 
        msg = ""
        expected_count = TUPLET_DISABLED
        tuplet_count = 0

        def errmsg() -> str:
            if expected_count == 3:
                return f"Invalid triplet only {tuplet_count} notes selected"
            (label, beats) = TupletTypes[expected_count]
            return f"Invalid {label}, only {tuplet_count} notes selected"

        for te in tab_events:
            if expected_count == TUPLET_DISABLED:
                if te.tuplet_code != TUPLET_DISABLED:
                    expected_count = te.tuplet_code
                    tuplet_count = 1
            else:
                if te.tuplet_code == TUPLET_DISABLED:
                    if tuplet_count != expected_count:
                        valid = False
                        break

                    # end of tuplet
                    expected_count = TUPLET_DISABLED
                    tuplet_count = 0

                else:
                    # failure hear 
                    assert(te.tuplet_code == expected_count)
                    tuplet_count += 1

        if tuplet_count != expected_count and expected_count != TUPLET_DISABLED:
            valid = False

        if not valid:
            msg = errmsg()
            
        return (valid, msg)
     

    def paste(self, track: Track, track_view : QWidget):
        if len(self.tab_items) > 0:
            # this is a cut and past operation
            # track_view is a TrackEditorView
            track.insert_tab_events(self.tab_items) # type: ignore
            self.clear()
            track_view.update()
        
    def cut(self, track: Track, track_view: QWidget) -> bool:
        tab_items = self.get_tab_events()
        (valid, errmsg) = self.validate(tab_items)
        if not valid:
            alert(errmsg, title="Unable to cut")
            return False
        self.tab_items = tab_items
        track.remove_tab_events(self.tab_items)
        self.clear()
        track_view.update()
        return True

    def copy(self, track: Track, track_view: QWidget) -> bool:
        tab_items = self.get_tab_events()
        (valid, errmsg) = self.validate(tab_items)
        if not valid:
            alert(errmsg, title="Unable to copy")
            return False
        self.tab_items = tab_items

        self.clear()
        track_view.update()
        return True




