
def layoutRemoveAllItems(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None) # Remove from layout
                item.widget().deleteLater() # Optional: Delete the widget from memory
            elif item.layout():
                layoutRemoveAllItems(item.layout()) # Recursively clear nested layouts
