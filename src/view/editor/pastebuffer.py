from typing import List
from models.measure import TabEvent
from view.editor.tabEventPresenter import TabEventPresenter
from singleton_decorator import singleton


@singleton
class PasteBufferSingleton:
    items : List[TabEventPresenter] = [] 
    active = False

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
        self.items.append(item)

    def activate(self):
        self.active = True 

    def deactivate(self):
        self.active = False

    def isActive(self):
        return self.active    
    




