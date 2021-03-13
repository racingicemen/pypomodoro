import sys
from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QWidget, QLCDNumber, QPushButton, QGridLayout
from PySide2.QtCore import QTimer, Qt
from PySide2.QtGui import QIcon, QColor, QPalette, QFont
from PySide2.QtMultimedia import QSoundEffect

MINUTES = 60*1000
POMODORO_TIME = 30*MINUTES
SBREAK_TIME = 6*MINUTES
LBREAK_TIME = 60*MINUTES
TICK_INTERVAL = 500  # milliseconds
NUM_POMODOROS_BEFORE_LONG_BREAK = 6


class State:
    def __init__(self):
        self.started = False
        self.paused = False
        self.current_time = 0
        self.show_blink = True
        self.lcd_color = QPalette()


class PomodoroState(State):
    def __init__(self):
        super().__init__()
        self.time_limit = POMODORO_TIME
        self.lcd_color.setColor(QPalette.Foreground, QColor("red"))

    def __str__(self):
        return "Pomodoro"


class ShortBreakState(State):
    def __init__(self):
        super().__init__()
        self.time_limit = SBREAK_TIME
        self.lcd_color.setColor(QPalette.Foreground, QColor("yellow"))

    def __str__(self):
        return "ShortBreak"


class LongBreakState(State):
    def __init__(self):
        super().__init__()
        self.time_limit = LBREAK_TIME
        self.lcd_color.setColor(QPalette.Foreground, QColor("green"))

    def __str__(self):
        return "LongBreak"


class PomodoroTimer(QWidget):
    def __init__(self):
        super().__init__()

        self.pomodoro_state = PomodoroState()
        self.sbreak_state = ShortBreakState()
        self.lbreak_state = LongBreakState()
        self.state = self.pomodoro_state

        self.timer_lcd = QLCDNumber()
        self.timer_lcd.setDigitCount(5)
        self.timer_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.timer_lcd.setStyleSheet("""QLCDNumber { background-color: black; }""")

        self.start_button = QPushButton("Start")
        self.start_button.setFont(QFont("Jetbrains Mono Nerd Font Mono", 18))
        self.start_button.clicked.connect(self.handle_start)

        self.pause_resume_button = QPushButton(self.calculate_pause_resume_btn_text(), enabled=False)
        self.pause_resume_button.setFont(QFont("Jetbrains Mono Nerd Font Mono", 18))
        self.pause_resume_button.clicked.connect(self.handle_pause_resume)

        self.stop_button = QPushButton("Stop", enabled=False)
        self.stop_button.setFont(QFont("Jetbrains Mono Nerd Font Mono", 18))
        self.stop_button.clicked.connect(self.handle_stop)

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

        self.last_task_time = 0
        self.all_tasks_time = 0
        self.pomodoro_count = 0

        self.setup_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timer_fired)

    def setup_ui(self):
        self.setFixedSize(600, 400)
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

        self.timer_lcd.setPalette(self.state.lcd_color)
        self.setLayout(main_layout)

        self.show()

    def handle_pause_resume(self):
        self.state.paused = not self.state.paused
        self.pause_resume_button.setText(self.calculate_pause_resume_btn_text())
        if self.state.paused:
            self.timer.stop()
        else:
            self.timer.start()

    def calculate_pause_resume_btn_text(self):
        if self.state.paused:
            return "Resume"
        else:
            return "Pause"

    def calculate_display_time(self):
        if not self.state.show_blink:
            return ""
        minutes = self.state.current_time // (1000 * 60)
        seconds = (self.state.current_time // 1000) % 60
        amount_of_time = "{:02d}:{:02d}".format(minutes, seconds)
        return amount_of_time

    def calculate_pomodoro_count(self):
        return "{:02d}".format(self.pomodoro_count)

    def calculate_last_task_time(self):
        return "{:02d}".format(round(self.last_task_time / 60000.0))

    def calculate_all_tasks_time(self):
        return "{:03d}".format(round(self.all_tasks_time / 60000.0))

    def handle_start(self):
        self.state.started = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        if self.state is self.pomodoro_state:
            self.pause_resume_button.setEnabled(True)
            self.last_task_time = 0
            self.pomodoro_count += 1
        self.start_countdown()

    def handle_stop(self):
        self.state.started = False
        self.pause_resume_button.setEnabled(False)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.state.paused = False
        self.pause_resume_button.setText(self.calculate_pause_resume_btn_text())

        if self.state is self.pomodoro_state:
            if self.pomodoro_count % NUM_POMODOROS_BEFORE_LONG_BREAK == 0:
                self.state = self.lbreak_state
            else:
                self.state = self.sbreak_state
        else:
            self.state = self.pomodoro_state

        self.timer_lcd.setPalette(self.state.lcd_color)
        self.reset_countdown()

    def timer_fired(self):
        if self.state.current_time >= self.state.time_limit and self.state.started:
            self.state.show_blink = not self.state.show_blink

        current_time = self.calculate_display_time()
        self.state.current_time += TICK_INTERVAL

        if self.state is self.pomodoro_state:
            self.last_task_time += TICK_INTERVAL
            self.all_tasks_time += TICK_INTERVAL

        self.timer_lcd.display(current_time)
        self.pomodoro_count_lcd.display(self.calculate_pomodoro_count())
        self.task_minutes_lcd.display(self.calculate_last_task_time())
        self.total_minutes_lcd.display(self.calculate_all_tasks_time())

    def start_countdown(self):
        if self.state.current_time >= self.state.time_limit:
            self.reset_countdown()
        self.timer.start(TICK_INTERVAL)

    def stop_countdown(self):
        if self.timer.isActive():
            self.timer.stop()

    def reset_countdown(self):
        self.stop_countdown()
        self.state.current_time = 0
        self.state.show_blink = True
        self.timer_lcd.display(self.calculate_display_time())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PomodoroTimer()
    sys.exit(app.exec_())
