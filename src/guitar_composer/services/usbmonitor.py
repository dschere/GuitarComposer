import pyudev
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import threading
import time
from singleton_decorator import singleton

@singleton
class UsbMonitor(QObject):
    device_changed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='usb')
        self.observer = pyudev.MonitorObserver(self.monitor, self._handle_udev_event)
        self.observer.start()
        self.current_state = None 
        self.timer_inflight = threading.Event()

    def _delayed_notification(self):
        time.sleep(0.25)
        self.device_changed.emit(self.current_state)
        self.timer_inflight.clear() 

    def _handle_udev_event(self, action, device):
        self.current_state = action
        # tests have shown a flurry of events happening with 100ms
        # in addition calling SDL to check for devices returns a false
        # negative. we have to give the system some time for an
        # accurate read. 
        if not self.timer_inflight.is_set():
            self.timer_inflight.set() 
            t = threading.Thread(daemon=True, target=self._delayed_notification)
            t.start()
            




"""
    # In your PyQt6 application:
    class MyWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.usb_monitor = UsbMonitor()
            self.usb_monitor.device_added.connect(self.on_usb_added)
            self.usb_monitor.device_removed.connect(self.on_usb_removed)

        def on_usb_added(self, device):
            print(f"USB Device Added: {device.device_node}")

        def on_usb_removed(self, device):
            print(f"USB Device Removed: {device.device_node}")
"""