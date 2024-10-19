import logging
import gcsynth
from io import StringIO
import faulthandler
import os

from singleton_decorator import singleton
from services.synth.instrument_info import instrument_info
from services.synth.sequencer import sequencer
from multiprocessing import Process, SimpleQueue


def gcsynth_proc(q, r):
    (reader,writer) = os.pipe()
    w_error = os.fdopen(writer,"w")
    r_error = os.fdopen(reader,"r")
    faulthandler.enable(file=w_error)

    while True:
        msg = q.get()
        if not msg:
            break
        try:
            (funcname, args) = msg
            f = getattr(gcsynth, funcname)
            logging.debug("gcsynth.%s( %s )" % (funcname, str(args)))
            result = (False, f(*args))
        except gcsynth.GcsynthException as e_obj:
            logging.error("gcsynth.%s( %s ) -> caused exception!" %
                          (funcname, str(args)))
            result = (True, str(e_obj))
        except Exception as e_obj:
            logging.error("gcsynth.%s( %s ) -> caused exception!" %
                          (funcname, str(args)))
            logging.error(r_error.read())
            result = (True, "c exception")

        r.put(result)


@singleton
class synthservice:
    def __init__(self):
        # scan soundfonts and produce an archive of information
        # filenames, instrument data etc.
        self.db = instrument_info()

        # create message queues
        self.send_q = SimpleQueue()
        self.recv_q = SimpleQueue()

        self.p = Process(target=gcsynth_proc, args=(
            self.send_q, self.recv_q,), daemon=True)
        self.p.start()

    def transact(self, funcname, *args):
        msg = (funcname, args)
        self.send_q.put(msg)

        (error, result) = self.recv_q.get()
        if error:
            raise RuntimeError(error)
        return result

    def shutdown(self):
        self.send_q.put(None)
        self.p.join(2.0)

    def getSequencer(self):
        return sequencer(self)

    def start(self):
        return self.transact("start", {"sfpaths": self.db.sfpaths})

    def stop(self):
        return self.transact("stop")

    def noteoff(self, channel: int, midicode: int):
        return self.transact("noteoff", channel, midicode)

    def noteon(self, channel: int, midicode: int, velocity: int):
        return self.transact("noteon", channel, midicode, velocity)

    def select(self, channel: int, sfont_id: int, bank_num: int, preset_num: int):
        return self.transact("select", channel, sfont_id, bank_num, preset_num)

    def filter_add(self, channel: int, filepath: str, plugin_label: str):
        return self.transact("filter_add", channel, filepath, plugin_label)

    def filter_remove(self, channel: int, plugin_label: str):
        return self.transact("filter_remove", channel, plugin_label)

    def filter_remove_all(self, channel: int):
        return self.transact("filter_remove", channel)

    def filter_query(self, filepath: str, plugin_label: str):
        return self.transact("filter_query", filepath, plugin_label)

    def filter_enable(self, channel: int, plugin_label: str):
        return self.transact("filter_enable", channel, plugin_label)

    def filter_disable(self, channel: int, plugin_label: str):
        return self.transact("filter_disable", channel, plugin_label)

    def filter_set_control_by_name(self, channel: int, plugin_label: str, name: str, value: float):
        return self.transact("filter_set_control_by_name", channel, plugin_label, name, value)

    def filter_set_control_by_index(self, channel: int, plugin_label: str, index: int, value: float):
        return self.transact("filter_set_control_by_index", channel, plugin_label, index, value)

    def channel_gain(self, channel: int, change: float):
        return self.transact("channel_gain", channel, change)

    def timer_event(self, ev_or_ev_list):
        return self.transact("timer_event", ev_or_ev_list)

    def instrument_info(self):
        return self.db.instruments


if __name__ == '__main__':
    import time

    ss = synthservice()
    ss.start()
    ss.noteon(0, 60, 80)
    time.sleep(2.0)
    ss.stop()
    ss.shutdown()
