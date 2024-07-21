import sys
from PyQt6.QtWidgets import QSizePolicy, QApplication, QWidget, QHBoxLayout, QLabel, QPushButton


class ThreeWidgetsLayout(QWidget):
    def __init__(self):
        super().__init__()

        # Create a QHBoxLayout for the main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Set no margins

        # Create three widgets: QLabel, QPushButton, QLabel
        label1 = QLabel("Left Widget")
        button = QPushButton("Center Widget")
        label2 = QLabel("Right Widget")

        # Set size policies to Fixed for all widgets
        label1.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        label2.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Add widgets to the layout
        layout.addWidget(label1)
        layout.addWidget(button)
        layout.addWidget(label2)

        # Set spacing between widgets to 0
        layout.setSpacing(0)

        # Set the main layout of the widget
        self.setLayout(layout)


def main():
    app = QApplication(sys.argv)

    # Create a main window
    window = QWidget()
    window.setWindowTitle("Three Widgets Layout Example")

    # Create a ThreeWidgetsLayout instance
    three_widgets_layout = ThreeWidgetsLayout()

    # Set fixed size for the main window
    window.setFixedSize(400, 100)

    # Set the layout of the main window
    window.setLayout(three_widgets_layout.layout())

    # Show the window
    window.show()

    # Execute the application
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

