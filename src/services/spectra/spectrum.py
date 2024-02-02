from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
import matplotlib.pyplot as plt

import sys


def plot_frequencies(freqs):
    plt.plot(freqs)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude')
    plt.title('Frequency Plot')
    plt.show()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Audio Frequencies Plot")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        self.plot_button = QPushButton("Plot Frequencies")
        layout.addWidget(self.plot_button)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())

