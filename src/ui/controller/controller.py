"""
Process GUI events
"""

from ui.controller.effectsrack_controller import EffectsRackController

class Controller:
    def __init__(self):
        # sub controllers for various activities
        self.effects_rack_controller = EffectsRackController()
