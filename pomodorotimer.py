import sys
from time import strftime, localtime
from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QWidget, QLCDNumber, QPushButton, QGridLayout, QLabel
from PySide2.QtCore import QTimer
from PySide2.QtGui import QIcon, QFont
from PySide2.QtMultimedia import QSoundEffect
from states import PomodoroState, ShortBreakState, LongBreakState

TICK_INTERVAL = 500  # milliseconds
LONG_BREAK_AFTER = 6  # pomodoros
INTERRUPTION_MARKER = "\u2b24"  # Black Large Circle


class PomodoroTimer(QWidget):
    def __init__(self, width, height):
        super().__init__()

        self.width = width
        self.height = height

        self.pomodoro_state = PomodoroState()
        self.short_break_state = ShortBreakState()
        self.long_break_state = LongBreakState()
        self.state = self.pomodoro_state

        self.timer_lcd = PomodoroTimer.create_lcd(digit_count=5, lcd_color="red")
        self.pomodoros_till_long_break_lcd = PomodoroTimer.create_lcd(digit_count=1, lcd_color="orange")
        self.task_minutes_lcd = PomodoroTimer.create_lcd(digit_count=2, lcd_color="orange")
        self.total_minutes_lcd = PomodoroTimer.create_lcd(digit_count=3, lcd_color="orange")
        self.non_pomodoro_start_hhmm_lcd = PomodoroTimer.create_lcd(digit_count=4, lcd_color="blue")
        self.non_pomodoro_minutes_lcd = PomodoroTimer.create_lcd(digit_count=3, lcd_color="pink")
        self.non_pomodoro_stop_hhmm_lcd = PomodoroTimer.create_lcd(digit_count=4, lcd_color="blue")

        self.start_button = PomodoroTimer.create_button("Start", self.handle_start)
        self.skip_button = PomodoroTimer.create_button("Skip", self.handle_skip)
        self.pause_resume_button = PomodoroTimer.create_button("Pause", self.handle_pause_resume, enabled=False)
        self.stop_button = PomodoroTimer.create_button("Stop", self.handle_stop, enabled=False)
        self.non_pomodoro_start_stop_button = PomodoroTimer.create_button("Start", self.handle_non_pomodoro_start_stop)

        self.interruptions_label = QLabel()
        self.interruptions_label.setFont(QFont("PT Mono", 18))
        self.interruptions_label.setStyleSheet("border: 3px solid black;")

        self.last_task_time = 0
        self.all_tasks_time = 0
        self.pomodoros_till_long_break = LONG_BREAK_AFTER

        self.last_non_pomodoro_time = 0
        self.non_pomodoro_started = False

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

        non_pomodoro_layout = QGridLayout()
        non_pomodoro_layout.addWidget(self.non_pomodoro_start_stop_button, 0, 0, 1, 1)
        non_pomodoro_layout.addWidget(self.non_pomodoro_start_hhmm_lcd, 0, 1, 1, 4)
        self.non_pomodoro_start_hhmm_lcd.display("----")
        non_pomodoro_layout.addWidget(self.non_pomodoro_minutes_lcd, 0, 5, 1, 3)
        self.non_pomodoro_minutes_lcd.display("---")
        non_pomodoro_layout.addWidget(self.non_pomodoro_stop_hhmm_lcd, 0, 8, 1, 4)
        self.non_pomodoro_stop_hhmm_lcd.display("----")
        main_layout.addLayout(non_pomodoro_layout, 7, 0, 1, 12)

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
            self.non_pomodoro_start_stop_button.setEnabled(True)
        else:
            self.timer.start()

    def handle_non_pomodoro_start_stop(self):
        self.non_pomodoro_started = not self.non_pomodoro_started
        self.non_pomodoro_start_stop_button.setText(self.calculate_start_stop_btn_text())
        if self.non_pomodoro_started:
            if self.state.paused:
                self.pause_resume_button.setEnabled(False)
                self.stop_button.setEnabled(False)
            else:
                self.start_button.setEnabled(False)
                self.skip_button.setEnabled(False)
            self.timer.start(TICK_INTERVAL)
            self.non_pomodoro_start_hhmm_lcd.display(PomodoroTimer.calculate_hhmm())
            self.non_pomodoro_minutes_lcd.display(self.calculate_non_pomodoro_minutes())
            self.non_pomodoro_stop_hhmm_lcd.display(PomodoroTimer.calculate_hhmm())
        else:
            if self.state.paused:
                self.pause_resume_button.setEnabled(True)
                self.stop_button.setEnabled(True)
            else:
                self.start_button.setEnabled(True)
                self.skip_button.setEnabled(True)
            self.timer.stop()
            self.all_tasks_time += round(self.last_non_pomodoro_time / 60000.0)
            self.total_minutes_lcd.display(self.calculate_all_tasks_time())
            self.last_non_pomodoro_time = 0


    def calculate_pause_resume_btn_text(self):
        if self.state.paused:
            return "Resume"
        else:
            return "Pause"

    def calculate_start_stop_btn_text(self):
        if self.non_pomodoro_started:
            return "Stop"
        else:
            return "Start"

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

    @staticmethod
    def calculate_hhmm():
        return strftime("%H%M", localtime())

    def calculate_non_pomodoro_minutes(self):
        return "{:03d}".format(round(self.last_non_pomodoro_time / 60000.0))

    def handle_start(self):
        self.state.started = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.skip_button.setEnabled(False)
        self.non_pomodoro_start_stop_button.setEnabled(False)
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
        self.non_pomodoro_start_stop_button.setEnabled(True)
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
        if self.non_pomodoro_started:
            self.last_non_pomodoro_time += TICK_INTERVAL
            self.non_pomodoro_minutes_lcd.display(self.calculate_non_pomodoro_minutes())
            self.non_pomodoro_stop_hhmm_lcd.display(PomodoroTimer.calculate_hhmm())
            return

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

        self.state.current_time += TICK_INTERVAL

        if self.state is self.pomodoro_state:
            self.last_task_time += TICK_INTERVAL

        self.timer_lcd.display(self.calculate_display_time())
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
    width = 600
    height = 400
    if len(sys.argv) == 3:
        width = int(sys.argv[1])
        height = int(sys.argv[2])
    window = PomodoroTimer(width=width, height=height)
    sys.exit(app.exec_())
