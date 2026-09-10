from guitar_composer.services.usbmonitor import UsbMonitor
from guitar_composer.services.synth.synthservice import synthservice
import time
from PyQt6.QtWidgets import QMessageBox

from guitar_composer.view.events import Signals, LiveCaptureConfig
from guitar_composer.view.dialogs.effectsControlDialog.dialog import EffectChanges





class LiveAudioController:
    """Controls real-time live audio input capture, USB audio device detection, and live effects processing."""

    def on_usb_device_change(self):
        """Update available audio capture devices when USB devices change, stopping capture if device disappears."""
        self.input_devices = self.synth.list_capture_devices()
        if len(self.input_devices) == 0 and self.capture_active:
            self.synth.stop_capture()
            self.capture_active = False

    def update_effect_changes(self, ec: EffectChanges):
        """Apply real-time LADSPA filter updates and parameter adjustments to the live audio channel.

        Args:
            ec: Dictionary mapping Effect instances to changed parameters.
        """
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
        """Toggle live audio stream capture on or off based on incoming configuration event.

        Args:
            evt: LiveCaptureConfig specifying device and desired active state.
        """
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
        """Initialize LiveAudioController, enumerate capture devices, and connect event listeners."""
        self.synth = synthservice()
        self.input_devices = self.synth.list_capture_devices()
        self.usb_monitor = UsbMonitor()
        self.capture_active = False

        self.usb_monitor.device_changed.connect(self.on_usb_device_change)
        Signals.live_capture.connect(self.live_capture)
        Signals.live_effects.connect(self.update_effect_changes)