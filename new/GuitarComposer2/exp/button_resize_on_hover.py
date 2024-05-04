import sys
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton, QButtonGroup

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Horizontal List with Highlight on Selection")
        self.setGeometry(100, 100, 600, 80)

        self.setupUI()

    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.setSpacing(0)  # Set spacing between items to zero

        button_info = [
            {"text": "Button 1", "tooltip": "This is Button 1"},
            {"text": "Button 2", "tooltip": "This is Button 2"},
            {"text": "Button 3", "tooltip": "This is Button 3"},
            {"text": "Button 4", "tooltip": "This is Button 4"},
            {"text": "Button 5", "tooltip": "This is Button 5"}
        ]

        button_group = QButtonGroup(self)
        button_group.setExclusive(True)  # Set exclusive selection

        for info in button_info:
            button = QPushButton(info["text"])
            button.setFixedSize(120, 40)  # Fixed size for each button
            button.setStyleSheet("QPushButton { font-size: 14px; }")
            button.setToolTip(info["tooltip"])  # Set tooltip for the button
            button._text = info["text"]

            button_group.addButton(button)  # Add button to the button group

            # Connect hover events to slots
            button.enterEvent = lambda event, btn=button: self.onButtonEnter(btn)
            button.leaveEvent = lambda event, btn=button: self.onButtonLeave(btn)

            layout.addWidget(button)

        button_group.buttonClicked.connect(self.onButtonClicked)  # Connect buttonClicked signal

    def onButtonEnter(self, button):
        button.setFixedSize(150, 60)  # Increase button size when mouse enters

    def onButtonLeave(self, button):
        button.setFixedSize(120, 40)  # Restore button size when mouse leaves

    def onButtonClicked(self, button):
        # Clear previous selection styles
        for btn in button.group().buttons():
            btn.setStyleSheet("QPushButton { font-size: 14px; }")

        # Apply highlight style to the selected button
        button.setStyleSheet("QPushButton { font-size: 14px; border: 2px solid red; }")
        print(button._text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
