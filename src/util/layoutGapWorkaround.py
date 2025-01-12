# I have tried using setSpacing, and setting the margins to no 
# avail, this is a work around method.
def adjust_size_to_fit(layout, parent_widget):
    """
    Adjust the parent widget's size to fit the layout's contents
    without any gaps.
    """
    total_width = 0
    total_height = 0

    for i in range(layout.count()):
        item = layout.itemAt(i)
        widget = item.widget()
        if widget:
            widget_width = widget.sizeHint().width()
            widget_height = widget.sizeHint().height()
            total_width += widget_width
            total_height = max(total_height, widget_height)  # Take the tallest widget's height

    parent_widget.setFixedSize(total_width, total_height)