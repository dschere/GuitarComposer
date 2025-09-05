from services.usbmonitor import UsbMonitor
from services.synth.synthservice import synthservice
import time
from PyQt6.QtWidgets import QMessageBox

from view.events import Signals, LiveCaptureConfig
from view.dialogs.effectsControlDialog.dialog import EffectChanges





class LiveAudioController:
    def on_usb_device_change(self):
        self.input_devices = self.synth.list_capture_devices()
        if len(self.input_devices) == 0 and self.capture_active:
            self.synth.stop_capture()
            self.capture_active = False

    def update_effect_changes(self, ec: EffectChanges):
        chan = self.synth.get_live_channel()
        
        # see EffectsDialog.delta for details on EffectChanges
        for e in ec:
            path = e.plugin_path() 
            label = e.plugin_label() 

            if e.is_enabled():
                #if chan not in self.effect_enabled_state:
                self.synth.filter_add(chan, path, label)
                self.synth.filter_enable(chan, label)
                #self.effect_enabled_state.add(chan)

                # change/set parameters
                for (pname,param) in ec[e]:
                    self.synth.filter_set_control_by_name(
                        chan,
                        label,
                        pname,
                        param.current_value
                    )

            else:                   
                self.synth.filter_disable(chan, label)
                self.synth.filter_remove(chan, label)


    def live_capture(self, evt: LiveCaptureConfig):
        if evt.state == True and self.capture_active == False:
            err = self.synth.start_capture(evt.device)
            if err == -1:
                msg = "Unable to do audio capture please check logs for further details."
                msg_box = QMessageBox()
                msg_box.setWindowTitle("Error")
                msg_box.setText(msg)
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.show()
            else:
                self.capture_active = True    
        
        elif self.capture_active == True and evt.state == False:
            self.synth.stop_capture()
            self.capture_active = False            

    def __init__(self):
        self.synth = synthservice()
        self.input_devices = self.synth.list_capture_devices()
        self.usb_monitor = UsbMonitor()
        self.capture_active = False

        self.usb_monitor.device_changed.connect(self.on_usb_device_change)
        Signals.live_capture.connect(self.live_capture)
        Signals.live_effects.connect(self.update_effect_changes)