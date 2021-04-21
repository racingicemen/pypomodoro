import sys
from time import strftime, localtime
from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QWidget, QLCDNumber, QPushButton, QGridLayout, QLabel
from PySide2.QtCore import QTimer
from PySide2.QtGui import QIcon, QFont
from PySide2.QtMultimedia import QSoundEffect
from states import PomodoroState, ShortBreakState, LongBreakState
from lcdnumberslider import LCDNumberSlider

TICK_INTERVAL = 500  # milliseconds
DISPLAY_UPDATE_TICK_INTERVAL = 60000  # 1 minute, in milliseconds
LONG_BREAK_AFTER = 6  # pomodoros
INTERRUPTION_MARKER = "\u2b24"  # Black Large Circle
MINUTES = 60*1000
POMODORO_MINUTES = 30
POMODORO_TIME = POMODORO_MINUTES*MINUTES
SHORT_BREAK_MINUTES = 6
SHORT_BREAK_TIME = SHORT_BREAK_MINUTES*MINUTES
LONG_BREAK_MINUTES = 60
LONG_BREAK_TIME = LONG_BREAK_MINUTES*MINUTES
BUD_GREEN = "#7bb661"


class PomodoroTimer(QWidget):
    def __init__(self, width, height):
        super().__init__()

        self.width = width
        self.height = height

        self.timer_lcd = PomodoroTimer.create_lcd(digit_count=5, lcd_color="orangered")
        self.pomodoros_till_long_break_lcd = PomodoroTimer.create_lcd(digit_count=1, lcd_color="darkcyan")
        self.task_minutes_lcd = PomodoroTimer.create_lcd(digit_count=2, lcd_color="firebrick")
        self.total_minutes_lcd = PomodoroTimer.create_lcd(digit_count=3, lcd_color="yellowgreen")
        self.total_pomodoros_lcd = PomodoroTimer.create_lcd(digit_count=2, lcd_color="peru")
        self.non_pomodoro_start_hhmm_lcd = PomodoroTimer.create_lcd(digit_count=6, lcd_color="skyblue")
        self.non_pomodoro_minutes_lcd = PomodoroTimer.create_lcd(digit_count=3, lcd_color="tomato")
        self.non_pomodoro_stop_hhmm_lcd = PomodoroTimer.create_lcd(digit_count=6, lcd_color="springgreen")

        self.start_button = PomodoroTimer.create_button("Start", self.handle_start)
        self.skip_button = PomodoroTimer.create_button("Skip", self.handle_skip)
        self.pause_resume_button = PomodoroTimer.create_button("Pause", self.handle_pause_resume, enabled=False)
        self.stop_button = PomodoroTimer.create_button("Stop", self.handle_stop, enabled=False)
        self.non_pomodoro_start_button = PomodoroTimer.create_button("Start", self.handle_non_pomodoro_start_stop)
        self.non_pomodoro_stop_button = PomodoroTimer.create_button("Stop", self.handle_non_pomodoro_start_stop, enabled=False)

        self.interruptions_label = QLabel()
        self.interruptions_label.setFont(QFont("PT Mono", 18))
        self.interruptions_label.setStyleSheet("border: 3px solid black;")

        self.num_pomodoros_before_long_break_lcdslider = LCDNumberSlider(
            minval=3, maxval=6, startval=LONG_BREAK_AFTER, numdigits=1, background=BUD_GREEN, color="black")
        self.num_pomodoros_before_long_break_lcdslider.current_value.connect(self.handle_config_changes)
        self.pomodoro_time_lcdslider = LCDNumberSlider(
            minval=15, maxval=30, startval=POMODORO_MINUTES, numdigits=2, background=BUD_GREEN, color="black")
        self.pomodoro_time_lcdslider.current_value.connect(self.handle_config_changes)
        self.short_break_time_lcdslider = LCDNumberSlider(
            minval=3, maxval=6, startval=SHORT_BREAK_MINUTES, numdigits=1, background=BUD_GREEN, color="black")
        self.short_break_time_lcdslider.current_value.connect(self.handle_config_changes)
        self.long_break_time_lcdslider = LCDNumberSlider(
            minval=15, maxval=60, startval=LONG_BREAK_MINUTES, numdigits=2, background=BUD_GREEN, color="black")
        self.long_break_time_lcdslider.current_value.connect(self.handle_config_changes)

        self.last_task_time = 0
        self.all_pomodoro_time = 0
        self.all_nonpomodoro_time = 0
        self.total_pomodoro_count = 0
        self.pomodoros_till_long_break = self.num_pomodoros_before_long_break_lcdslider.get_current_value()
        self.pomodoro_state = PomodoroState(self.pomodoro_time_lcdslider.get_current_value()*MINUTES)
        self.short_break_state = ShortBreakState(self.short_break_time_lcdslider.get_current_value()*MINUTES)
        self.long_break_state = LongBreakState(self.long_break_time_lcdslider.get_current_value()*MINUTES)
        self.state = self.pomodoro_state

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
        self.setWindowTitle("PyPomodoro")
        self.setWindowIcon(QIcon("tomato.png"))

        main_layout = QGridLayout()
        main_layout.addWidget(self.timer_lcd, 0, 0, 6, 8)
        self.timer_lcd.display(self.calculate_display_time())

        button_layout = QGridLayout()
        button_layout.addWidget(self.start_button, 0, 0, 1, 2)
        button_layout.addWidget(self.skip_button, 0, 3, 1, 2)
        button_layout.addWidget(self.pause_resume_button, 0, 6, 1, 2)
        button_layout.addWidget(self.stop_button, 0, 9, 1, 2)
        main_layout.addLayout(button_layout, 6, 0, 1, 8)

        counter_layout = QGridLayout()
        counter_layout.addWidget(self.pomodoros_till_long_break_lcd, 0, 0, 1, 1)
        self.pomodoros_till_long_break_lcd.display(self.calculate_pomodoros_till_long_break())
        counter_layout.addWidget(self.task_minutes_lcd, 0, 1, 1, 2)
        self.task_minutes_lcd.display(self.calculate_last_task_time())
        counter_layout.addWidget(self.total_minutes_lcd, 0, 3, 1, 3)
        self.total_minutes_lcd.display(self.calculate_all_tasks_time())
        counter_layout.addWidget(self.total_pomodoros_lcd, 0, 6, 1, 2)
        self.total_pomodoros_lcd.display(self.calculate_total_pomodoro_count())
        main_layout.addLayout(counter_layout, 7, 0, 3, 8)

        main_layout.addWidget(self.interruptions_label, 10, 0, 1, 8)

        non_pomodoro_layout = QGridLayout()
        non_pomodoro_layout.addWidget(self.non_pomodoro_start_button, 0, 0, 1, 1)
        non_pomodoro_layout.addWidget(self.non_pomodoro_start_hhmm_lcd, 0, 1, 1, 2)
        self.non_pomodoro_start_hhmm_lcd.display("------")
        non_pomodoro_layout.addWidget(self.non_pomodoro_minutes_lcd, 0, 3, 1, 2)
        self.non_pomodoro_minutes_lcd.display("---")
        non_pomodoro_layout.addWidget(self.non_pomodoro_stop_hhmm_lcd, 0, 5, 1, 2)
        non_pomodoro_layout.addWidget(self.non_pomodoro_stop_button, 0, 7, 1, 1)
        self.non_pomodoro_stop_hhmm_lcd.display("------")
        main_layout.addLayout(non_pomodoro_layout, 11, 0, 1, 8)

        config_layout = QGridLayout()
        config_layout.addWidget(self.num_pomodoros_before_long_break_lcdslider, 0, 0, 1, 2)
        config_layout.addWidget(self.pomodoro_time_lcdslider, 0, 2, 1, 2)
        config_layout.addWidget(self.short_break_time_lcdslider, 0, 6, 1, 2)
        config_layout.addWidget(self.long_break_time_lcdslider, 0, 8, 1, 2)
        main_layout.addLayout(config_layout, 12, 0, 1, 8)

        self.timer_lcd.setPalette(self.state.lcd_color)
        self.enable_lcd_sliders(True)

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

    def handle_non_pomodoro_start_stop(self):
        self.non_pomodoro_started = not self.non_pomodoro_started
        if self.non_pomodoro_started:
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
        else:
            self.ticking_sound.stop()
            self.non_pomodoro_start_button.setEnabled(True)
            self.non_pomodoro_stop_button.setEnabled(False)
            if self.state.paused:
                self.pause_resume_button.setEnabled(True)
                self.stop_button.setEnabled(True)
            else:
                self.start_button.setEnabled(True)
                self.skip_button.setEnabled(True)
            self.timer.stop()
            self.all_nonpomodoro_time = 60000 * round(self.all_nonpomodoro_time / 60000.0)
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

    def calculate_pomodoros_till_long_break(self):
        return "{:01d}".format(self.pomodoros_till_long_break)

    def calculate_total_pomodoro_count(self):
        return "{:02d}".format(self.total_pomodoro_count)

    def calculate_last_task_time(self):
        return "{:02d}".format(round(self.last_task_time / 60000.0))

    def calculate_all_tasks_time(self):
        return "{:03d}".format(round(self.all_pomodoro_time/60000.0) + round(self.all_nonpomodoro_time/60000.0))

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
        self.enable_lcd_sliders(False)
        self.start_countdown()

    def enable_lcd_sliders(self, enabled):
        self.num_pomodoros_before_long_break_lcdslider.setEnabled(enabled)
        self.pomodoro_time_lcdslider.setEnabled(enabled)
        self.short_break_time_lcdslider.setEnabled(enabled)
        self.long_break_time_lcdslider.setEnabled(enabled)

    def handle_stop(self):
        self.state.started = False
        self.pause_resume_button.setEnabled(False)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.skip_button.setEnabled(True)
        self.non_pomodoro_start_button.setEnabled(True)
        self.state.paused = False
        self.pause_resume_button.setText(self.calculate_pause_resume_btn_text())
        self.setWindowTitle("PyPomodoro")

        if self.state is self.pomodoro_state:
            # 1. Set all_tasks_time rounded to the nearest minute, in milliseconds
            self.all_pomodoro_time = 60000*round(self.all_pomodoro_time / 60000.0)
            # 2. decrement the pomodoros_till_long_break counter and update the lcd
            self.pomodoros_till_long_break -= 1
            self.pomodoros_till_long_break_lcd.display(self.calculate_pomodoros_till_long_break())
            # 3. increment the total_pomodoro_count counter and update the lcd
            self.total_pomodoro_count += 1
            self.total_pomodoros_lcd.display(self.calculate_total_pomodoro_count())
            # 4. transition to the appropriate break state
            if self.pomodoros_till_long_break == 0:
                self.state = self.long_break_state
            else:
                self.state = self.short_break_state
        elif self.state is self.long_break_state:
            # we are stopping the long break. So reset pomodoros_till_long_break to LONG_BREAK_AFTER and update the lcd
            self.pomodoros_till_long_break = self.num_pomodoros_before_long_break_lcdslider.get_current_value()
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

    def handle_config_changes(self):
        self.pomodoros_till_long_break = self.num_pomodoros_before_long_break_lcdslider.get_current_value()
        self.pomodoros_till_long_break_lcd.display(self.calculate_pomodoros_till_long_break())
        self.pomodoro_state.time_limit = self.pomodoro_time_lcdslider.get_current_value()*MINUTES
        self.short_break_state.time_limit = self.short_break_time_lcdslider.get_current_value()*MINUTES
        self.long_break_state.time_limit = self.long_break_time_lcdslider.get_current_value()*MINUTES

    def timer_fired(self):
        if self.non_pomodoro_started:
            self.last_non_pomodoro_time += TICK_INTERVAL
            self.all_nonpomodoro_time += TICK_INTERVAL
            self.non_pomodoro_minutes_lcd.display(self.calculate_non_pomodoro_minutes())
            self.total_minutes_lcd.display(self.calculate_all_tasks_time())
            self.non_pomodoro_stop_hhmm_lcd.display(PomodoroTimer.calculate_hhmmss())
            self.ticking_sound.stop()
            self.ticking_sound.play()
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
            self.all_pomodoro_time += TICK_INTERVAL

        self.timer_lcd.display(self.calculate_display_time())
        self.task_minutes_lcd.display(self.calculate_last_task_time())
        self.total_minutes_lcd.display(self.calculate_all_tasks_time())
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
