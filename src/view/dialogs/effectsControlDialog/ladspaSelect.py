import sys
from PyQt6.QtWidgets import (QApplication, QDialog, QListWidget, QPushButton, 
                            QHBoxLayout, QVBoxLayout, QListWidgetItem)
from PyQt6.QtCore import Qt
from models.effect import Effect
from services.effectRepo import EffectRepository



class LadspaSelectDialog(QDialog):
    e_repo = EffectRepository()


    def selected_list_item_clicked(self, item):
        print(f"{item.text()} clicked")
        e = self.e_repo.get(item.text())


    def accept(self):
        """Update database with selected/unselected ladspa plugins"""
        selected = []
        elist = []
        for i in range(0,self.selected_list.count()):
            item = self.selected_list.item(i)
            if item:
                selected.append(item.text())
        ladspa_names = self.e_repo.getNames()
        for name in ladspa_names:
            e = self.e_repo.get(name)
            e.selected = name in selected
            elist.append(e)                  
        self.e_repo.update(elist)

        super().accept()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select ladspa effects")
        self.setMinimumSize(400, 300)

        # Create main layout
        main_layout = QHBoxLayout()

        # Left list (source)
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        # Right list (destination)
        self.selected_list = QListWidget()
        self.selected_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.selected_list.itemClicked.connect(self.selected_list_item_clicked)

        ladspa_names = self.e_repo.getNames()
        ladspa_names.sort()

        for name in ladspa_names:
            e = self.e_repo.get(name)
            if e.selected == True:
                self.selected_list.addItem(QListWidgetItem(name))
            else:
                self.available_list.addItem(QListWidgetItem(name))

        # Buttons
        self.right_button = QPushButton(">")
        self.right_button.clicked.connect(self.move_right)
        self.left_button = QPushButton("<")
        self.left_button.clicked.connect(self.move_left)
        self.right_all_button = QPushButton(">>")
        self.right_all_button.clicked.connect(self.move_all_right)
        self.left_all_button = QPushButton("<<")
        self.left_all_button.clicked.connect(self.move_all_left)

        # OK/Cancel buttons
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        # Layout for buttons
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.right_button)
        button_layout.addWidget(self.left_button)
        button_layout.addWidget(self.right_all_button)
        button_layout.addWidget(self.left_all_button)
        button_layout.addStretch()

        # Layout for bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.ok_button)
        bottom_layout.addWidget(self.cancel_button)

        # Main layout setup
        main_layout.addWidget(self.available_list)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.selected_list)

        # Overall layout
        overall_layout = QVBoxLayout()
        overall_layout.addLayout(main_layout)
        overall_layout.addLayout(bottom_layout)
        self.setLayout(overall_layout)

    def move_right(self):
        selected_items = self.available_list.selectedItems()
        for item in selected_items:
            self.selected_list.addItem(self.available_list.takeItem(self.available_list.row(item)))

    def move_left(self):
        selected_items = self.selected_list.selectedItems()
        for item in selected_items:
            self.available_list.addItem(self.selected_list.takeItem(self.selected_list.row(item)))

    def move_all_right(self):
        while self.available_list.count() > 0:
            self.selected_list.addItem(self.available_list.takeItem(0))

    def move_all_left(self):
        while self.selected_list.count() > 0:
            self.available_list.addItem(self.selected_list.takeItem(0))

    def get_selected_items(self):
        return [self.selected_list.item(i).text() for i in range(self.selected_list.count())]




# Example usage
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Sample items
    
    dialog = LadspaSelectDialog()
    #if dialog.exec():

    dialog.show()
    #    selected = dialog.get_selected_items()
    #    print("Selected items:", selected)
    #print("entering app.exec")
    sys.exit(app.exec())
