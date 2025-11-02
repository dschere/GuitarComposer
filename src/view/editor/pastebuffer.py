from typing import List
from models.measure import TabEvent
from view.editor.tabEventPresenter import TabEventPresenter
from singleton_decorator import singleton
from models.track import Track

from PyQt6.QtWidgets import QWidget

@singleton
class PasteBufferSingleton:
    items : List[TabEventPresenter] = [] 
    active = False
    tab_items : List[TabEvent] = []

    def __init__(self):
        super().__init__()

    def clear(self):
        for item in self.items:
            item.clear_copy_highlight()
        self.items : List[TabEventPresenter] = []

    def get_tab_events(self) -> List[TabEvent]:
        return [item.get_tab_event() for item in self.items]    

    def isEmpty(self):
        return len(self.items) == 0
    
    def append(self, item: TabEventPresenter):
        self.tab_items : List[TabEvent] = []
        self.items.append(item)

    def activate(self):
        self.active = True 

    def deactivate(self):
        self.active = False

    def isActive(self):
        return self.active

    def paste(self, track: Track, track_view : QWidget):
        if len(self.tab_items) > 0:
            # this is a cut and past operation
            # track_view is a TrackEditorView
            self.tab_items.reverse()
            track_view.insert_tab_events(self.tab_items) # type: ignore
            self.tab_items.reverse()
            self.clear()
            track_view.update()
        else:
            # this is a copy and paste operation.
            self.tab_items = self.get_tab_events()
            track.insert_tab_events(self.tab_items)
            self.clear()
            track_view.update()
        
    def cut(self, track: Track, track_view: QWidget):
        self.tab_items = self.get_tab_events()
        track.remove_tab_events(self.tab_items)
        self.clear()
        track_view.update()





