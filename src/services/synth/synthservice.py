import logging
import gcsynth
import faulthandler
import os

from singleton_decorator import singleton
from services.synth.instrument_info import instrument_info
from services.synth.sequencer import sequencer
from multiprocessing import Process, Queue, SimpleQueue
import traceback


import sys, signal

def gcsynth_proc(q, r):
    (reader, writer) = os.pipe()
    w_error = os.fdopen(writer, "w")
    r_error = os.fdopen(reader, "r")
    faulthandler.enable(file=w_error)

    # Optional: Write a custom signal handler for SIGSEGV
    def cmoderror_handler(signum, frame):
        print("Segmentation fault (SIGSEGV) detected!")
        faulthandler.dump_traceback()  # Print the stack trace
        sys.exit(1)

    # Set the custom SIGSEGV handler
    signal.signal(signal.SIGSEGV, cmoderror_handler)
    signal.signal(signal.SIGBUS, cmoderror_handler)

    while True:
        msg = q.get()
        if not msg:
            break
        
        try:
            (funcname, args) = msg
            if hasattr(gcsynth, funcname):
                f = getattr(gcsynth, funcname)

                #sys.stdout.write("%s%s\n" % (funcname,str(args)))
                #sys.stdout.flush()
                # -- execute gcsynth function
                result = (False, f(*args))

                #sys.stdout.write(" -> %s\n"  % str(result))
                #sys.stdout.flush()
            else:
                result = (True,"Unknown method name " + funcname)

        except gcsynth.GcsynthException:
            logging.error("gcsynth.%s( %s ) -> caused exception!" %
                          (funcname, str(args)))
            result = (True, traceback.format_exc())
        except:
            logging.error("gcsynth.%s%s -> caused exception!" %
                          (funcname, str(args)))
            result = (True, traceback.format_exc())

        r.put(result)


class midi_channel_manager:
    DRUM_CHANNEL = 9

    def __init__(self, synth):
        self.c_index = 1
        self.synth = synth
        self.num_channels = gcsynth.NUM_CHANNELS
        self.channel_state = [None for i in range(self.num_channels)]

    def checkout_channel(self):
        chan = None
        for i in range(self.num_channels):
            if not self.channel_state[self.c_index]:
                chan = self.c_index

            # ring increment counter, skip over the drum channel
            self.c_index = (self.c_index + 1) % self.num_channels
            if self.c_index == self.DRUM_CHANNEL:
                self.c_index += 1

            if chan:
                break
        return chan

    def reset(self):
        self.c_index = 1

    def dealloc(self, chan):
        self.synth.reset_channel(chan)
        self.channel_state[chan] = None

    def alloc(self, instrument_name):
        spec = self.synth.find(instrument_name)
        if not spec:
            raise ValueError("Unknown instrument name '%s'" %
                             instrument_name)
        chan = self.checkout_channel()
        if not chan:
            raise RuntimeError("Not enough channels!")

        self.channel_state[chan] = spec
        self.synth.select(
            chan,
            spec.sfont_id,
            spec.bank_num,
            spec.preset_num
        )
        return chan


@singleton
class synthservice:
    def __init__(self):
        # scan soundfonts and produce an archive of information
        # filenames, instrument data etc.
        self.db = instrument_info()
        self.cm = midi_channel_manager(self)

        # create message queues
        self.send_q = SimpleQueue()
        self.recv_q = SimpleQueue()

        self.p = Process(target=gcsynth_proc, args=(
            self.send_q, self.recv_q,), daemon=True)
        self.p.start()

    def reset_channel_manager(self):
        self.cm.reset()

    def dealloc(self, chan):
        self.cm.dealloc(chan)

    def alloc(self, instrument_name):
        return self.cm.alloc(instrument_name)

    def find(self, instrument_name):
        """lookup instrument information that can be used to setup a channel"""
        return self.db.find(instrument_name)

    def transact(self, funcname, *args):
        if not self.p.is_alive():
            raise RuntimeError("gcsynth parent process is no longer running!")

        msg = (funcname, args)
        print(f"transact {msg}")
        self.send_q.put(msg)
        
        print("sent waiting for reply")

        (error, result) = self.recv_q.get()
        print(f"reply received {result}")
        if error:
            raise RuntimeError(error)
        return result

    def shutdown(self):
        self.send_q.put(None)
        self.p.join(2.0)

    def getSequencer(self):
        return sequencer(self)

    def reset_channel(self, chan):
        return self.transact("reset_channel", chan)

    def start(self):
        return self.transact("start", {"sfpaths": self.db.sfpaths})

    def stop(self):
        return self.transact("stop")

    def noteoff(self, channel: int, midicode: int):
        return self.transact("noteoff", channel, midicode)

    def noteon(self, channel: int, midicode: int, velocity: int):
        return self.transact("noteon", channel, midicode, velocity)

    def select(self,
               channel: int,
               sfont_id: int,
               bank_num: int,
               preset_num: int):
        return self.transact("select", channel, sfont_id, bank_num, preset_num)

    def filter_add(self, channel: int,
                   filepath: str, plugin_label: str):
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

    def filter_set_control_by_name(self, channel: int,
                                   plugin_label: str,
                                   name: str, value: float):
        return self.transact("filter_set_control_by_name",
                             channel, plugin_label, name, value)

    def filter_set_control_by_index(self,
                                    channel: int, plugin_label: str,
                                    index: int, value: float):
        return self.transact("filter_set_control_by_index",
                             channel, plugin_label, index, value)

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
