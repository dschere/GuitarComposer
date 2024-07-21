from PyQt6.QtWidgets import QApplication, QWidget, QListWidget, QListWidgetItem, QHBoxLayout, QFrame, QVBoxLayout, QLabel

class TrackItemWidget(QWidget):
    def __init__(self, track_name, instrument_name, parent=None):
        super().__init__(parent)
        self.track_name = track_name
        self.instrument_name = instrument_name
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        # Display track name and instrument name
        label_text = f"{self.track_name} - {self.instrument_name}"
        label = QLabel(label_text)
        layout.addWidget(label)

        def handler(i):
            print("%s box %d clicked" % (self.track_name,i))

        # Display visualization boxes
        for i in range(16):
            box = QFrame()
            
            box.setFixedSize(8, 8)
            box.setStyleSheet("background-color: white; border: 1px solid black;")
            box.mousePressEvent = lambda event, index=i: handler(index)
            layout.addWidget(box)

        self.setLayout(layout)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Track List")

        list_widget = QListWidget()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(list_widget)

        # Example data (replace with your own data)
        track_data = [
            {"track_name": "Track 1", "instrument_name": "Piano"},
            {"track_name": "Track 2", "instrument_name": "Guitar"}
        ]

        for data in track_data:
            item = QListWidgetItem()
            visualization_widget = TrackItemWidget(data['track_name'], data['instrument_name'])
            item.setSizeHint(visualization_widget.sizeHint())
            list_widget.addItem(item)
            list_widget.setItemWidget(item, visualization_widget)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.resize(600, 400)
    window.show()
    app.exec()
