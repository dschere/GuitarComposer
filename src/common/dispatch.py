
TOPIC_EFFECTS_RACK_DIALOG = "/mainwin/effectsrack/dialog"
TOPIC_EFFECTS_RACK_LIVE_START =  "/mainwin/effectsrack/live-start"
TOPIC_EFFECTS_RACK_LIVE_STOP =  "/mainwin/effectsrack/live-stop"


def EffectsParamTopic(effectName,paramName):
    p = "effect/%s/%s" % (effectName,paramName)
    r = TOPIC_EFFECTS_RACK_DIALOG+p
                 


class _DispatchTable(object):
    # path -> (QAction or a callback function)
    __event_table = {}
    
    def subscribe(self, topic, callback):
        handlers = self.__event_table.get(topic, [])
        handlers.append(callback)
        print("adding handler for %s" % topic)
        self.__event_table[topic] = handlers
        
    def publish(self, topic, obj, data):
        """
        topic: string that identifies a callback
        obj: object like a QtWidget that initiated this action
        data: any extra data needed 
        """
        handlers = self.__event_table.get(topic, [])
        if len(handlers) == 0:
            if topic:
                print("No handlers for %s" % topic)
        for handler in handlers:
            handler( topic, obj, data )
            
    def remove(self, topic, callback):
        handlers = self.__event_table.get(topic, [])
        for (i,handler) in enumerate(handlers):
            if callback is handler:
                del handlers[i]
        self.__event_table[topic] = handlers        
                
    def update(self, topic, old_callback, new_callback):
        handlers = self.__event_table.get(topic, [])
        for (i,handler) in enumerate(handlers):
            if old_callback is handler:
                handlers[i] = new_callback
        self.__event_table[topic] = handlers        
            
    # make this object a singleton 
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(_DispatchTable, cls).__new__(cls)
        return cls.instance


# one and only dispatch table
DispatchTable = _DispatchTable()


def unittest():
    thing1 = _DispatchTable()
    thing2 = _DispatchTable()

    class FakeQtWidget(object):
        pass

    def cbnew(topic, obj, data):
        print("new topic=%s, obj=%s, data=%s" % (topic,str(obj),str(data)))
    def cbopen(topic, obj, data):
        assert( isinstance(obj,FakeQtWidget) )
        data['status'] = 'ok'
        print("---> open topic=%s, obj=%s, data=%s" % (topic,str(obj),str(data)))
        
    thing1.subscribe("/menu/new", cbnew)
    thing2.subscribe("/menu/open", cbopen)

    print("end test 1")
    # prove these are the same object.
    data = {}
    thing1.publish("/menu/open", FakeQtWidget(), data)
    assert( data.get('status','') == 'ok' ) 
        

    def cbopen2(topic, obj, data):
        assert( isinstance(obj,FakeQtWidget) )
        data['status'] = 'ok'
        data['secondcb'] = 'hello'
        print("--> second open topic=%s, obj=%s, data=%s" % (topic,str(obj),str(data)))

    thing1.subscribe("/menu/open", cbopen2)

    data = {}
    thing1.publish("/menu/open", FakeQtWidget(), data)
    assert( data.get('secondcb','') == 'hello' ) 

    print("end test2")
        
    
if __name__ == '__main__':
    unittest()    

