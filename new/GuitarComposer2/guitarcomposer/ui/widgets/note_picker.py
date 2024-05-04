import sys
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton, QButtonGroup, QGridLayout
from PyQt6.QtGui import QPainter, QColor, QFontMetrics


from guitarcomposer.ui.config import config
import copy

class note_picker(QWidget):
    """
    button_info = [
     {'text': ..., 'tooltip": 'tools tip text'},
     ...
    ] 
    
    selected_cb -> callback called when  text is selected.
    """
    def __init__(self, button_info, selected_cb, exclusive=True, **opts):
        self.config = copy.copy(config().note_picker)
        # allow config to be overriden
        for (k,v) in opts.items():
            setattr(self.config,k,v)
            
        super().__init__()
        self.exclusive = exclusive
        self.button_info = button_info
        self.selected_cb = selected_cb
        self.setupUI()
        
    # if title exists draw a border with a title.    
    def paintEvent(self, event):
        if not self.config.title:
            return # no border + title
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # Enable anti-aliasing for smooth edges

        # Define the background color and border color
        background_color = QColor(240, 240, 240)
        border_color = QColor(100, 100, 100)

        # Set painter colors
        painter.setBrush(background_color)
        painter.setPen(border_color)

        # Calculate the rectangle for the rounded border
        rect = self.rect().adjusted(5, 5, -5, -5)  # Adjust for padding
        
        # Draw the rounded rectangle border
        painter.drawRoundedRect(rect, 10, 10)

        # Draw the title text centered inside the border
        font = self.font()
        font.setBold(True)
        painter.setFont(font)

        text_rect = painter.boundingRect(rect, 0, self.config.title)
        text_x = int(rect.x() + (rect.width() - text_rect.width()) / 2)
        text_y = int(rect.y() + 16)  # Adjust vertical position
        painter.drawText(text_x, text_y, self.config.title)
        
    def set_css(self, button):
        if self.config.hover_font_size_change:
            s = button._size - 4
        else:
            s = 12    
        b = ""
        if button._selected:
            b = "border: 2px solid red;"        
        css = "QPushButton { font-size: %dpx; %s }" % (s,b)
        button.setStyleSheet(css)
        

    def setupUI(self):
        layout = QGridLayout()
        layout.setSpacing(0)
        layout.setHorizontalSpacing(-1)  # Set horizontal spacing to zero
        layout.setVerticalSpacing(-1) 
        

        button_group = QButtonGroup(self)
        button_group.setExclusive(self.exclusive)  # Set exclusive selection

        self.setLayout(layout)

        for (i,info) in enumerate(self.button_info):
            
            button = QPushButton(info["text"])
            button.setFixedSize(self.config.size, self.config.size)  # Fixed size for each button
            button.setStyleSheet("QPushButton { font-size: 14px; }")
            button.setToolTip(info["tooltip"])  # Set tooltip for the button

            button._text = info["text"]
            button._size = self.config.size
            button._selected = False

            button_group.addButton(button)  # Add button to the button group

            # Connect hover events to slots
            button.enterEvent = lambda event, btn=button: self.onButtonEnter(btn)
            button.leaveEvent = lambda event, btn=button: self.onButtonLeave(btn)

            column = i % self.config.max_buttons_per_column
            row = int(i / self.config.max_buttons_per_column) 
            layout.addWidget(button, row, column)
            

        button_group.buttonClicked.connect({
            True: self.onButtonClicked_exclusive,
            False: self.onButtonClicked_non_exclusive
        }[self.exclusive])  # Connect buttonClicked signal
        self.button_group = button_group
        
    def select(self, text):
        for btn in self.button_group.buttons():
            
            if btn._text == text:
                btn._size = self.config.size
                btn._selected = True
                self.set_css(btn)
                if not self.exclusive:
                    return
                
            elif self.exclusive:    
                btn._size = self.config.size
                btn._selected = False
                self.set_css(btn)


    def onButtonEnter(self, button):
        button.setFixedSize(self.config.hover_size, self.config.hover_size)  # Increase button size when mouse enters
        button._size = self.config.hover_size
        self.set_css(button) 

    def onButtonLeave(self, button):
        button._size = self.config.size
        button.setFixedSize(self.config.size, self.config.size)  # Restore button size when mouse leaves
        self.set_css(button)
        
    def onButtonClicked_exclusive(self, button):    
        # Clear previous selection styles
        for btn in button.group().buttons():
            btn._size = self.config.size
            btn._selected = False
            self.set_css(btn)
            
        button._selected = True 
        self.set_css(button)
        self.selected_cb(button._text)

    def onButtonClicked_non_exclusive(self, button):        
        if button._selected:
            button._size = self.config.size
            button._selected = False
            self.set_css(button)
        else:
            button._selected = True 
            self.set_css(button)
            self.selected_cb(button._text)
                    
