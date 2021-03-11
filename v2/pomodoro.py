import sys
from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QWidget, QLCDNumber, QPushButton, QGridLayout
from PySide2.QtCore import QTimer, Qt
from PySide2.QtGui import QIcon, QColor, QPalette
from PySide2.QtMultimedia import QSoundEffect
from random import randint, randrange


class Pomodoro(QWidget):
    def __init__(self):
        super().__init__()

        self.timer_lcd = QLCDNumber()
        self.timer_lcd.setDigitCount(5)
        self.timer_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.timer_lcd.setStyleSheet("""QLCDNumber { background-color: black; }""")

        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet("""QPushButton { background: black; color: white }""")
        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.setStyleSheet("""QPushButton { background: black; color: white }""")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("""QPushButton { background: black; color: white }""")

        self.pomodoro_count_lcd = QLCDNumber()
        self.pomodoro_count_lcd.setDigitCount(2)
        self.pomodoro_count_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.pomodoro_count_lcd.setStyleSheet("""QLCDNumber { background-color: black; color: orange; }""")

        self.task_minutes_lcd = QLCDNumber()
        self.task_minutes_lcd.setDigitCount(2)
        self.task_minutes_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.task_minutes_lcd.setStyleSheet("""QLCDNumber { background-color: black; color: orange; }""")

        self.total_minutes_lcd = QLCDNumber()
        self.total_minutes_lcd.setDigitCount(3)
        self.total_minutes_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.total_minutes_lcd.setStyleSheet("""QLCDNumber { background-color: black; color: orange; }""")

        red = QColor("red")
        yellow = QColor("yellow")
        green = QColor("green")

        self.pomodoro_color = QPalette()
        self.pomodoro_color.setColor(QPalette.Foreground, red)

        self.short_break_color = QPalette()
        self.short_break_color.setColor(QPalette.Foreground, yellow)

        self.long_break_color = QPalette()
        self.long_break_color.setColor(QPalette.Foreground, green)

        self.setup_ui()

    def setup_ui(self):
        self.setFixedSize(540, 360)
        self.setWindowTitle("LeastAction Pomodoro")

        main_layout = QGridLayout()
        main_layout.addWidget(self.timer_lcd, 0, 0, 3, 9)
        self.timer_lcd.display("00:00")

        button_layout = QGridLayout()
        button_layout.addWidget(self.start_button, 0, 0, 1, 3)
        button_layout.addWidget(self.pause_resume_button, 0, 3, 1, 3)
        button_layout.addWidget(self.stop_button, 0, 6, 1, 3)
        main_layout.addLayout(button_layout, 3, 0, 1, 9)

        counter_layout = QGridLayout()
        counter_layout.addWidget(self.pomodoro_count_lcd, 0, 0, 1, 2)
        self.pomodoro_count_lcd.display("00")
        counter_layout.addWidget(self.task_minutes_lcd, 0, 3, 1, 2)
        self.task_minutes_lcd.display("00")
        counter_layout.addWidget(self.total_minutes_lcd, 0, 6, 1, 3)
        self.total_minutes_lcd.display("000")
        main_layout.addLayout(counter_layout, 4, 0, 2, 9)

        number = randint(0, 100)
        if number < 33:
            self.timer_lcd.setPalette(self.pomodoro_color)
        elif number < 66:
            self.timer_lcd.setPalette(self.short_break_color)
        else:
            self.timer_lcd.setPalette(self.long_break_color)

        self.setLayout(main_layout)

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Pomodoro()
    sys.exit(app.exec_())
