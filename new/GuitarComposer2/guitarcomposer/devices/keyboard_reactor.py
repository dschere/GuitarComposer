from singleton_decorator import singleton

@singleton
class keyboard_reactor:
    def __init__(self):
        self.keypress_event_handlers = {}
        self.keyrelease_event_handlers = {}
        
    def register(self, kmovement, key, handler):
        if kmovement == 'press':
             handlers = self.keypress_event_handlers.get(key,[])
             handlers.append(handler)
             self.keypress_event_handlers[key] = handlers
        else:
             handlers = self.keyrelease_event_handlers.get(key)
             handlers.append(handler)
             self.keyrelease_event_handlers[key] = handlers
                 
    def unregister(self, handler):
        for t in (self.keypress_event_handlers,self.keyrelease_event_handlers):
            for (k, hlist) in t.items():
                new_list = []
                for (i,h) in enumerate(hlist):
                    if h is not handler:
                        new_list.append(h)
                t[k] = new_list        
        
        
    def keyPressEvent(self, event):
        key = event.key()
        for handlers in self.keypress_event_handlers.get(key,[]):
            handlers(key)
                 
    def keyReleaseEvent(self, event):
        key = event.key()
        for handlers in self.keyrelease_event_handlers.get(key,[]):
            handlers(key)


def unittest():
    def handler(key):
        print(key)
    kr = keyboard_reactor()
    kr.register("press", "a", handler)
    
    class fake_event:
        def __init__(self, k):
            self.k = k
        def key(self):
            return self.k     
    
    kr.keyPressEvent(fake_event('a'))
    kr.keyPressEvent(fake_event('b'))
    
    kr.unregister(handler)
    
    kr.keyPressEvent(fake_event('a'))
    kr.keyPressEvent(fake_event('b'))

    print("should only see 'a'")
        

if __name__ == '__main__':
    unittest()
