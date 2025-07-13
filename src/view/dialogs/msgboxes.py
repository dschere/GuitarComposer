
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QMessageBox, QPushButton
from PyQt6.QtGui import QIcon



def alert(message: str, **kw_args):
    # Modal dialog showing error message, blocking call.
    msg_box = QMessageBox()

    title = kw_args.get("title","Error")

    msg_box.setIcon(QMessageBox.Icon.Critical)  # Set the icon
    msg_box.setWindowTitle(title)  # Set the window title
    msg_box.setText(message)  # Set the main message
    msg_box.setStandardButtons(
        QMessageBox.StandardButton.Ok
    )  # Set standard buttons

    # Execute the message box and get the user's response
    msg_box.exec()




if __name__ == "__main__":
    class TestWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("message box tester")
            layout = QVBoxLayout()

            alert_test = QPushButton("alert test", self)
            alert_test.clicked.connect(lambda *args: alert("test"))

            layout.addWidget(alert_test)
            self.setLayout(layout)


    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

