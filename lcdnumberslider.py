import sys
from PySide2.QtWidgets import QApplication, QWidget, QLCDNumber, QGridLayout, QSlider
from PySide2.QtCore import Qt, Signal


class LCDNumberSlider(QWidget):
    current_value = Signal(int)

    def __init__(self, minval, maxval, startval, numdigits, background, color):
        super().__init__()

        self.lcd = QLCDNumber()
        self.lcd.setDigitCount(numdigits)
        self.lcd.setSegmentStyle(QLCDNumber.Flat)
        self.lcd.setStyleSheet(f"""QLCDNumber {{ background-color: {background}; color: {color}; }}""")

        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(minval)
        self.slider.setMaximum(maxval)
        self.slider.valueChanged.connect(self.display_slider_value_in_lcd)

        self.slider.setValue(startval)
        self.display_slider_value_in_lcd()

        grid = QGridLayout()
        grid.addWidget(self.lcd, 0, 0, 4, 4)
        grid.addWidget(self.slider, 0, 4, 4, 1)
        self.setLayout(grid)

        self.show()

    def display_slider_value_in_lcd(self):
        self.lcd.display(f'{{:0{self.lcd.digitCount()}}}'.format(self.slider.value()))
        self.current_value.emit(self.slider.value())

    def get_current_value(self):
        return self.slider.value()

    def setEnabled(self, enabled):
        self.slider.setEnabled(enabled)
        self.lcd.setSegmentStyle(QLCDNumber.Flat) if not enabled else self.lcd.setSegmentStyle(QLCDNumber.Filled)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    lcd_slider = LCDNumberSlider(minval=0, maxval=10, startval=3, numdigits=3, background="#7BB661", color="black")

    print(f"starting value is {lcd_slider.get_current_value()}")

    def print_current_value(value):
        print(f"The current value is {value}")

    lcd_slider.current_value.connect(print_current_value)

    sys.exit(app.exec_())
