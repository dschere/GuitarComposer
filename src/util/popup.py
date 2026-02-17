from PyQt6.QtWidgets import QMessageBox

icon_map = {
    "error": QMessageBox.Icon.Critical,
    "warning": QMessageBox.Icon.Warning,
    "info": QMessageBox.Icon.Information,
    "question": QMessageBox.Icon.Question
}


def show_alert(parent, **kwargs):
    msg = QMessageBox(parent)
    msg.setWindowTitle(kwargs.get('title', "Success"))
    msg.setText(kwargs.get("text", "Your action was completed successfully!"))
    msg.setIcon(icon_map[kwargs.get("icon", "info")])
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()

def ask_question(self, title, question):
    reply = QMessageBox.question(
        self,
        title,
        question,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No # Optional: sets 'No' as the default button
    )

    if reply == QMessageBox.StandardButton.Yes:
        return True
    return False