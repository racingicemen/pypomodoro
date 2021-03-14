import sys
from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QWidget, QLCDNumber, QPushButton, QGridLayout
from PySide2.QtCore import QTimer
from PySide2.QtGui import QIcon, QColor, QPalette, QFont
from PySide2.QtMultimedia import QSoundEffect

MINUTE = 60000  # milliseconds
POMODORO_TIME = 30*MINUTE
SHORT_BREAK_TIME = 6 * MINUTE
LONG_BREAK_TIME = 60 * MINUTE
TICK_INTERVAL = 500  # milliseconds
LONG_BREAK_AFTER = 6  # pomodoros


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
        self.time_limit = SHORT_BREAK_TIME
        self.lcd_color.setColor(QPalette.Foreground, QColor("yellow"))

    def __str__(self):
        return "ShortBreak"


class LongBreakState(State):
    def __init__(self):
        super().__init__()
        self.time_limit = LONG_BREAK_TIME
        self.lcd_color.setColor(QPalette.Foreground, QColor("green"))

    def __str__(self):
        return "LongBreak"


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

        self.last_task_time = 0
        self.pomodoro_count = 0

        self.ticking_sound = PomodoroTimer.initialize_sound_files('ticking-sound.wav')
        self.beeping_sound = PomodoroTimer.initialize_sound_files('beeping-sound.wav')

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
        main_layout.addWidget(self.timer_lcd, 0, 0, 3, 9)
        self.timer_lcd.display(self.calculate_display_time())

        main_layout.addWidget(self.start_button, 3, 3, 1, 3)
        main_layout.addWidget(self.pause_resume_button, 4, 3, 1, 3)
        main_layout.addWidget(self.stop_button, 5, 3, 1, 3)

        main_layout.addWidget(self.pomodoro_count_lcd, 3, 0, 3, 3)
        self.pomodoro_count_lcd.display(self.calculate_pomodoro_count())
        main_layout.addWidget(self.task_minutes_lcd, 3, 6, 3, 3)
        self.task_minutes_lcd.display(self.calculate_last_task_time())

        self.timer_lcd.setPalette(self.state.lcd_color)
        self.setLayout(main_layout)

        self.show()

    def handle_pause_resume(self):
        self.state.paused = not self.state.paused
        self.pause_resume_button.setText(self.calculate_pause_resume_btn_text())
        if self.state.paused:
            self.timer.stop()
            self.ticking_sound.stop()
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
            if self.pomodoro_count % LONG_BREAK_AFTER == 0:
                self.state = self.long_break_state
            else:
                self.state = self.short_break_state
        else:
            self.state = self.pomodoro_state

        self.timer_lcd.setPalette(self.state.lcd_color)
        self.reset_countdown()
        self.ticking_sound.stop()
        self.beeping_sound.stop()

    def timer_fired(self):
        if self.state.current_time >= self.state.time_limit:
            self.state.show_blink = not self.state.show_blink
            if self.state is self.pomodoro_state:   # exceeding time limit in PomodoroState results in ticking sound
                self.ticking_sound.stop()           # continuing to be played. Blinking LCD display is the only
                self.ticking_sound.play()           # indication that time is up.
            else:
                self.ticking_sound.stop()           # exceeding time limit in Short/LongBreakState results in the
                self.beeping_sound.stop()           # beeping sound being played, along with the blinking LCD display
                self.beeping_sound.play()           # we also shut off the ticking sound
        else:
            self.ticking_sound.stop()
            self.ticking_sound.play()

        current_time = self.calculate_display_time()
        self.state.current_time += TICK_INTERVAL

        if self.state is self.pomodoro_state:
            self.last_task_time += TICK_INTERVAL

        self.timer_lcd.display(current_time)
        self.pomodoro_count_lcd.display(self.calculate_pomodoro_count())
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
