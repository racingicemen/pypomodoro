import sys
from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QWidget, QLCDNumber, QPushButton, QGridLayout, QLabel
from PySide2.QtCore import QTimer
from PySide2.QtGui import QIcon, QColor, QPalette, QFont
from PySide2.QtMultimedia import QSoundEffect

MINUTES = 60*1000
POMODORO_TIME = 30*MINUTES
SHORT_BREAK_TIME = 6*MINUTES
LONG_BREAK_TIME = 60*MINUTES
TICK_INTERVAL = 500  # milliseconds
LONG_BREAK_AFTER = 6  # pomodoros
INTERRUPTION_MARKER = "\u2b24"  # Black Large Circle


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


class ShortBreakState(State):
    def __init__(self):
        super().__init__()
        self.time_limit = SHORT_BREAK_TIME
        self.lcd_color.setColor(QPalette.Foreground, QColor("yellow"))


class LongBreakState(State):
    def __init__(self):
        super().__init__()
        self.time_limit = LONG_BREAK_TIME
        self.lcd_color.setColor(QPalette.Foreground, QColor("green"))


class PomodoroTimer(QWidget):
    def __init__(self):
        super().__init__()

        self.pomodoro_state = PomodoroState()
        self.short_break_state = ShortBreakState()
        self.long_break_state = LongBreakState()
        self.state = self.pomodoro_state

        self.timer_lcd = QLCDNumber()
        self.timer_lcd.setDigitCount(5)
        self.timer_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.timer_lcd.setStyleSheet("""QLCDNumber { background-color: black; }""")

        self.start_button = QPushButton("Start")
        self.start_button.setFont(QFont("Jetbrains Mono Nerd Font Mono", 18))
        self.start_button.clicked.connect(self.handle_start)

        self.skip_button = QPushButton("Skip")
        self.skip_button.setFont(QFont("Jetbrains Mono Nerd Font Mono", 18))
        self.skip_button.clicked.connect(self.handle_skip)

        self.pause_resume_button = QPushButton(self.calculate_pause_resume_btn_text(), enabled=False)
        self.pause_resume_button.setFont(QFont("Jetbrains Mono Nerd Font Mono", 18))
        self.pause_resume_button.clicked.connect(self.handle_pause_resume)

        self.stop_button = QPushButton("Stop", enabled=False)
        self.stop_button.setFont(QFont("Jetbrains Mono Nerd Font Mono", 18))
        self.stop_button.clicked.connect(self.handle_stop)

        self.pomodoros_till_long_break_lcd = QLCDNumber()
        self.pomodoros_till_long_break_lcd.setDigitCount(1)
        self.pomodoros_till_long_break_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.pomodoros_till_long_break_lcd.setStyleSheet("""QLCDNumber { background-color: black; color: orange; }""")

        self.task_minutes_lcd = QLCDNumber()
        self.task_minutes_lcd.setDigitCount(2)
        self.task_minutes_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.task_minutes_lcd.setStyleSheet("""QLCDNumber { background-color: black; color: orange; }""")

        self.total_minutes_lcd = QLCDNumber()
        self.total_minutes_lcd.setDigitCount(3)
        self.total_minutes_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.total_minutes_lcd.setStyleSheet("""QLCDNumber { background-color: black; color: orange; }""")

        self.interruptions_label = QLabel()
        self.interruptions_label.setFont(QFont("PT Mono", 18))
        self.interruptions_label.setStyleSheet("border: 3px solid black;")

        self.last_task_time = 0
        self.all_tasks_time = 0
        self.pomodoros_till_long_break = LONG_BREAK_AFTER

        self.ticking_sound = PomodoroTimer.initialize_sound_files('ticking-sound.wav')
        self.beeping_sound = PomodoroTimer.initialize_sound_files('beeping-sound.wav')
        self.time_exceeded_sound = PomodoroTimer.initialize_sound_files("time-exceeded-sound.wav")

        self.setup_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timer_fired)

    @staticmethod
    def initialize_sound_files(sound_file_name):
        sound = QSoundEffect()
        sound.setSource(QtCore.QUrl.fromLocalFile(sound_file_name))
        sound.setVolume(1.0)
        return sound

    def setup_ui(self):
        self.setFixedSize(600, 400)
        self.setWindowTitle("LeastAction Pomodoro")
        self.setWindowIcon(QIcon("tomato.png"))

        main_layout = QGridLayout()
        main_layout.addWidget(self.timer_lcd, 0, 0, 3, 12)
        self.timer_lcd.display(self.calculate_display_time())

        button_layout = QGridLayout()
        button_layout.addWidget(self.start_button, 0, 0, 1, 3)
        button_layout.addWidget(self.skip_button, 0, 3, 1, 3)
        button_layout.addWidget(self.pause_resume_button, 0, 6, 1, 3)
        button_layout.addWidget(self.stop_button, 0, 9, 1, 3)
        main_layout.addLayout(button_layout, 3, 0, 1, 12)

        counter_layout = QGridLayout()
        counter_layout.addWidget(self.pomodoros_till_long_break_lcd, 0, 0, 1, 2)
        self.pomodoros_till_long_break_lcd.display(self.calculate_pomodoros_till_long_break())
        counter_layout.addWidget(self.task_minutes_lcd, 0, 2, 1, 4)
        self.task_minutes_lcd.display(self.calculate_last_task_time())
        counter_layout.addWidget(self.total_minutes_lcd, 0, 6, 1, 6)
        self.total_minutes_lcd.display(self.calculate_all_tasks_time())
        main_layout.addLayout(counter_layout, 4, 0, 2, 12)

        main_layout.addWidget(self.interruptions_label, 6, 0, 1, 12)

        self.timer_lcd.setPalette(self.state.lcd_color)
        self.setLayout(main_layout)

        self.show()

    def handle_pause_resume(self):
        self.state.paused = not self.state.paused
        self.pause_resume_button.setText(self.calculate_pause_resume_btn_text())
        if self.state.paused:
            self.timer.stop()
            self.ticking_sound.stop()
            old_text = self.interruptions_label.text()
            self.interruptions_label.setText(old_text + INTERRUPTION_MARKER + " ")
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

    def calculate_pomodoros_till_long_break(self):
        return "{:01d}".format(self.pomodoros_till_long_break)

    def calculate_last_task_time(self):
        return "{:02d}".format(round(self.last_task_time / 60000.0))

    def calculate_all_tasks_time(self):
        return "{:03d}".format(self.all_tasks_time)

    def handle_start(self):
        self.state.started = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.skip_button.setEnabled(False)
        if self.state is self.pomodoro_state:
            self.pause_resume_button.setEnabled(True)
            self.last_task_time = 0
            self.interruptions_label.setText("")
        self.start_countdown()

    def handle_stop(self):
        self.state.started = False
        self.pause_resume_button.setEnabled(False)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.skip_button.setEnabled(True)
        self.state.paused = False
        self.pause_resume_button.setText(self.calculate_pause_resume_btn_text())

        if self.state is self.pomodoro_state:
            # 1. Add the last task's time (rounded to nearest minute) to all tasks time,
            self.all_tasks_time += round(self.last_task_time / 60000.0)
            self.total_minutes_lcd.display(self.calculate_all_tasks_time())
            # 2. decrement the pomodoros_till_long_break counter and update the lcd
            self.pomodoros_till_long_break -= 1
            self.pomodoros_till_long_break_lcd.display(self.calculate_pomodoros_till_long_break())
            # 3. transition to the appropriate break state
            if self.pomodoros_till_long_break == 0:
                self.state = self.long_break_state
            else:
                self.state = self.short_break_state
        elif self.state is self.long_break_state:
            # we are stopping the long break. So reset pomodoros_till_long_break to LONG_BREAK_AFTER and update the lcd
            self.pomodoros_till_long_break = LONG_BREAK_AFTER
            self.pomodoros_till_long_break_lcd.display(self.calculate_pomodoros_till_long_break())
            # transition to the pomodoro state
            self.state = self.pomodoro_state
        else:
            # we are stopping the short break; only allowed action is to start a new pomodoro
            self.state = self.pomodoro_state

        self.timer_lcd.setPalette(self.state.lcd_color)
        self.reset_countdown()
        self.ticking_sound.stop()
        self.beeping_sound.stop()
        self.time_exceeded_sound.stop()

    def handle_skip(self):
        self.handle_start()
        self.handle_stop()

    def timer_fired(self):
        if self.state.current_time >= self.state.time_limit:
            self.state.show_blink = not self.state.show_blink
            self.ticking_sound.stop()
            if self.state is self.pomodoro_state:
                self.time_exceeded_sound.stop()
                self.time_exceeded_sound.play()
            else:
                self.beeping_sound.stop()
                self.beeping_sound.play()
        else:
            self.ticking_sound.stop()
            self.ticking_sound.play()

        current_time = self.calculate_display_time()
        self.state.current_time += TICK_INTERVAL

        if self.state is self.pomodoro_state:
            self.last_task_time += TICK_INTERVAL

        self.timer_lcd.display(current_time)
        self.task_minutes_lcd.display(self.calculate_last_task_time())

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
