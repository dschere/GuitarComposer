import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QPushButton, QMessageBox

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 List Box Example")

        # Create a QListWidget
        self.list_widget = QListWidget()

        # Add items to the list
        self.list_widget.addItem("Apple")
        self.list_widget.addItem("Banana")
        self.list_widget.addItem("Orange")

        # Create a button to add new items
        self.add_button = QPushButton("Add Item")
        #self.add_button.clicked.connect(self.add_item)

        # Connect itemClicked signal to custom slot
        self.list_widget.itemClicked.connect(self.item_clicked)

        # Create a layout
        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        layout.addWidget(self.add_button)

        # Set the layout on the QWidget
        self.setLayout(layout)

    def add_item(self):
        # Add a new item to the list when the button is clicked
        text, ok = QInputDialog.getText(self, 'Add Item', 'Enter item name:')
        if ok:
            self.list_widget.addItem(text)

    def item_clicked(self, item):
        # Handle the item clicked event
        QMessageBox.information(self, "Item Clicked", f"You clicked: {item.text()}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())


