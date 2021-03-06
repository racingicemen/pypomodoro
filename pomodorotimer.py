import sys
from time import strftime, localtime
from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QWidget, QLCDNumber, QPushButton, QGridLayout, QLabel
from PySide2.QtCore import QTimer
from PySide2.QtGui import QIcon, QFont
from PySide2.QtMultimedia import QSoundEffect
from states import PomodoroState, ShortBreakState
from datetime import datetime

TICK_INTERVAL = 500  # milliseconds
INTERRUPTION_MARKER = "\u25c9"  # Fisheye
MINUTES = 60*1000
POMODORO_MINUTES = 30
POMODORO_TIME = POMODORO_MINUTES*MINUTES
SHORT_BREAK_MINUTES = 6
SHORT_BREAK_TIME = SHORT_BREAK_MINUTES*MINUTES
BUD_GREEN = "#7bb661"


class PomodoroTimer(QWidget):
    def __init__(self, width, height):
        super().__init__()

        self.width = width
        self.height = height

        self.today = datetime.now().strftime("%d%b%Y%a")

        self.timer_lcd = PomodoroTimer.create_lcd(digit_count=5, lcd_color="orangered")
        self.pomodoros_till_long_break_lcd = PomodoroTimer.create_lcd(digit_count=1, lcd_color="slategray")
        self.task_minutes_lcd = PomodoroTimer.create_lcd(digit_count=2, lcd_color="firebrick")
        self.total_minutes_lcd = PomodoroTimer.create_lcd(digit_count=3, lcd_color="yellowgreen")
        self.total_pomodoros_lcd = PomodoroTimer.create_lcd(digit_count=2, lcd_color="peru")
        self.total_pomodoro_minutes_lcd = PomodoroTimer.create_lcd(digit_count=3, lcd_color="dodgerblue")
        self.total_non_pomodoro_minutes_lcd = PomodoroTimer.create_lcd(digit_count=3, lcd_color="blueviolet")

        self.non_pomodoro_start_hhmm_lcd = PomodoroTimer.create_lcd(digit_count=6, lcd_color="skyblue")
        self.non_pomodoro_minutes_lcd = PomodoroTimer.create_lcd(digit_count=3, lcd_color="tomato")
        self.non_pomodoro_stop_hhmm_lcd = PomodoroTimer.create_lcd(digit_count=6, lcd_color="springgreen")

        self.start_button = PomodoroTimer.create_button("Start", self.handle_start)
        self.skip_button = PomodoroTimer.create_button("Skip", self.handle_skip)
        self.pause_resume_button = PomodoroTimer.create_button("Pause", self.handle_pause_resume, enabled=False)
        self.stop_button = PomodoroTimer.create_button("Stop", self.handle_stop, enabled=False)
        self.non_pomodoro_start_button = PomodoroTimer.create_button("Start", self.handle_non_pomodoro_start)
        self.non_pomodoro_stop_button = PomodoroTimer.create_button("Stop", self.handle_non_pomodoro_stop, enabled=False)

        self.interruptions_label = QLabel()
        self.interruptions_label.setFont(QFont("MesloLGS Nerd Font Mono", 42))
        self.interruptions_label.setStyleSheet("border: 3px solid black;")

        self.last_task_time = 0
        self.all_pomodoro_time = 0
        self.all_non_pomodoro_time = 0
        self.total_pomodoro_count = 0
        self.pomodoro_state = PomodoroState(POMODORO_TIME)
        self.short_break_state = ShortBreakState(SHORT_BREAK_TIME)
        self.state = self.pomodoro_state

        self.last_non_pomodoro_time = 0

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

    @staticmethod
    def create_lcd(digit_count, lcd_color):
        lcd = QLCDNumber()
        lcd.setDigitCount(digit_count)
        lcd.setSegmentStyle(QLCDNumber.Flat)
        lcd.setStyleSheet(f"""QLCDNumber {{ background-color: black; color: {lcd_color}; }}""")
        return lcd

    @staticmethod
    def create_button(label, callback, enabled=True):
        button = QPushButton(label, enabled=enabled)
        button.setFont(QFont("Jetbrains Mono Nerd Font Mono", 18))
        button.clicked.connect(callback)
        return button

    def setup_ui(self):
        self.setFixedSize(self.width, self.height)
        self.setWindowTitle(self.today)
        self.setWindowIcon(QIcon("tomato.png"))

        main_layout = QGridLayout()
        today = QLabel(self.today)
        font = QFont("MesloLGS Nerd Font Mono", 42)
        font.setBold(True)
        today.setFont(font)
        today.setStyleSheet("border: 3px solid black;")
        main_layout.addWidget(today, 0, 0, 3, 8)
        main_layout.addWidget(self.total_minutes_lcd, 0, 8, 3, 8)
        self.total_minutes_lcd.display(self.calculate_all_tasks_time())
        main_layout.addWidget(self.timer_lcd, 3, 0, 6, 16)
        self.timer_lcd.display(self.calculate_display_time())

        button_layout = QGridLayout()
        button_layout.addWidget(self.start_button, 0, 0, 1, 1)
        button_layout.addWidget(self.skip_button, 0, 1, 1, 1)
        button_layout.addWidget(self.pause_resume_button, 0, 2, 1, 1)
        button_layout.addWidget(self.stop_button, 0, 3, 1, 1)
        button_layout.addWidget(self.interruptions_label, 1, 0, 1, 4)

        counter_layout = QGridLayout()
        counter_layout.addWidget(self.task_minutes_lcd, 0, 0, 1, 4)
        self.task_minutes_lcd.display(self.calculate_last_task_time())
        counter_layout.addLayout(button_layout, 0, 4, 1, 12)

        main_layout.addLayout(counter_layout, 10, 0, 3, 16)

        non_pomodoro_layout = QGridLayout()
        non_pomodoro_layout.addWidget(self.non_pomodoro_start_button, 0, 0, 1, 1)
        non_pomodoro_layout.addWidget(self.non_pomodoro_start_hhmm_lcd, 0, 1, 1, 5)
        self.non_pomodoro_start_hhmm_lcd.display("------")
        non_pomodoro_layout.addWidget(self.non_pomodoro_minutes_lcd, 0, 6, 1, 4)
        self.non_pomodoro_minutes_lcd.display("---")
        non_pomodoro_layout.addWidget(self.non_pomodoro_stop_hhmm_lcd, 0, 10, 1, 5)
        non_pomodoro_layout.addWidget(self.non_pomodoro_stop_button, 0, 15, 1, 1)
        self.non_pomodoro_stop_hhmm_lcd.display("------")
        main_layout.addLayout(non_pomodoro_layout, 14, 0, 1, 16)

        counter_layout = QGridLayout()
        counter_layout.addWidget(self.total_pomodoros_lcd, 0, 0, 1, 4)
        self.total_pomodoros_lcd.display(self.calculate_total_pomodoro_count())
        counter_layout.addWidget(self.total_pomodoro_minutes_lcd, 0, 4, 1, 6)
        self.total_pomodoro_minutes_lcd.display(self.calculate_pomodoro_tasks_time())
        counter_layout.addWidget(self.total_non_pomodoro_minutes_lcd, 0, 10, 1, 6)
        self.total_non_pomodoro_minutes_lcd.display(self.calculate_non_pomodoro_tasks_time())

        main_layout.addLayout(counter_layout, 15, 0, 3, 16)

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
            self.non_pomodoro_start_button.setEnabled(True)
        else:
            self.timer.start()
            self.non_pomodoro_start_button.setEnabled(False)

    def handle_non_pomodoro_start(self):
        self.state.non_pomodoro_started = True
        self.non_pomodoro_start_button.setEnabled(False)
        self.non_pomodoro_stop_button.setEnabled(True)
        if self.state.paused:
            self.pause_resume_button.setEnabled(False)
            self.stop_button.setEnabled(False)
        else:
            self.start_button.setEnabled(False)
            self.skip_button.setEnabled(False)
        self.timer.start(TICK_INTERVAL)
        self.non_pomodoro_start_hhmm_lcd.display(PomodoroTimer.calculate_hhmmss())
        self.non_pomodoro_minutes_lcd.display(self.calculate_non_pomodoro_minutes())
        self.non_pomodoro_stop_hhmm_lcd.display(PomodoroTimer.calculate_hhmmss())

    def handle_non_pomodoro_stop(self):
        self.state.non_pomodoro_started = False
        self.non_pomodoro_start_button.setEnabled(True)
        self.non_pomodoro_stop_button.setEnabled(False)
        if self.state.paused:
            self.pause_resume_button.setEnabled(True)
            self.stop_button.setEnabled(True)
        else:
            self.start_button.setEnabled(True)
            self.skip_button.setEnabled(True)
        self.timer.stop()
        self.all_non_pomodoro_time = 60000 * round(self.all_non_pomodoro_time / 60000.0)
        self.last_non_pomodoro_time = 0

    def calculate_pause_resume_btn_text(self):
        return "Resume" if self.state.paused else "Pause"

    def calculate_display_time(self):
        if not self.state.show_blink:
            return ""
        minutes = self.state.current_time // (1000 * 60)
        seconds = (self.state.current_time // 1000) % 60
        amount_of_time = "{:02d}:{:02d}".format(minutes, seconds)
        return amount_of_time

    def calculate_total_pomodoro_count(self):
        return "{:02d}".format(self.total_pomodoro_count)

    def calculate_last_task_time(self):
        return "{:02d}".format(round(self.last_task_time / 60000.0))

    def calculate_all_tasks_time(self):
        return "{:03d}".format(round(self.all_pomodoro_time/60000.0) + round(self.all_non_pomodoro_time/60000.0))

    def calculate_pomodoro_tasks_time(self):
        return "{:03d}".format(round(self.all_pomodoro_time / 60000.0))

    def calculate_non_pomodoro_tasks_time(self):
        return "{:03d}".format(round(self.all_non_pomodoro_time/60000.0))

    @staticmethod
    def calculate_hhmmss():
        return strftime("%H%M%S", localtime())

    def calculate_non_pomodoro_minutes(self):
        return "{:03d}".format(round(self.last_non_pomodoro_time / 60000.0))

    def handle_start(self):
        self.state.started = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.skip_button.setEnabled(False)
        self.non_pomodoro_start_button.setEnabled(False)
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
        self.non_pomodoro_start_button.setEnabled(True)
        self.state.paused = False
        self.pause_resume_button.setText(self.calculate_pause_resume_btn_text())
        self.setWindowTitle(self.today)

        if self.state is self.pomodoro_state:
            # 1. Set all_tasks_time rounded to the nearest minute, in milliseconds
            self.all_pomodoro_time = 60000*round(self.all_pomodoro_time / 60000.0)
            # 2. increment the total_pomodoro_count counter and update the lcd
            self.total_pomodoro_count += 1
            self.total_pomodoros_lcd.display(self.calculate_total_pomodoro_count())
            # 3. transition to the short break state
            self.state = self.short_break_state
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

    def handle_config_changes(self):
        self.pomodoro_state.time_limit = self.pomodoro_time_lcdslider.get_current_value()*MINUTES
        self.short_break_state.time_limit = self.short_break_time_lcdslider.get_current_value()*MINUTES
        self.long_break_state.time_limit = self.long_break_time_lcdslider.get_current_value()*MINUTES

    def timer_fired(self):
        if self.state.non_pomodoro_started:
            self.last_non_pomodoro_time += TICK_INTERVAL
            self.all_non_pomodoro_time += TICK_INTERVAL
            self.non_pomodoro_minutes_lcd.display(self.calculate_non_pomodoro_minutes())
            self.total_minutes_lcd.display(self.calculate_all_tasks_time())
            self.total_non_pomodoro_minutes_lcd.display(self.calculate_non_pomodoro_tasks_time())
            self.non_pomodoro_stop_hhmm_lcd.display(PomodoroTimer.calculate_hhmmss())
            return

        if self.state.current_time >= self.state.time_limit:
            self.state.show_blink = not self.state.show_blink
            self.ticking_sound.stop()
            self.pause_resume_button.setEnabled(False)
            if self.state is self.pomodoro_state:
                self.time_exceeded_sound.stop()
                self.time_exceeded_sound.play()
            else:
                self.beeping_sound.stop()
                self.beeping_sound.play()
        else:
            self.ticking_sound.stop()
            self.ticking_sound.play()

        self.state.current_time += TICK_INTERVAL

        if self.state is self.pomodoro_state:
            self.last_task_time += TICK_INTERVAL
            self.all_pomodoro_time += TICK_INTERVAL

        self.timer_lcd.display(self.calculate_display_time())
        self.task_minutes_lcd.display(self.calculate_last_task_time())
        self.total_minutes_lcd.display(self.calculate_all_tasks_time())
        self.total_pomodoro_minutes_lcd.display(self.calculate_pomodoro_tasks_time())
        self.setWindowTitle(self.state.prefix + " " + self.calculate_display_time())

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
    width = 600
    height = 400
    if len(sys.argv) == 3:
        width = int(sys.argv[1])
        height = int(sys.argv[2])
    window = PomodoroTimer(width=width, height=height)
    sys.exit(app.exec_())
