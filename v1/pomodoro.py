import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QLCDNumber, QPushButton,QTabWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from PyQt5 import QtMultimedia
from PomodoroStyleSheet import style_sheet

MINUTES = 60 * 1000             # milliseconds in a minute
POMODORO_TIME = 30 * MINUTES    # pomodoro duration in minutes
SHORT_BREAK_TIME = 6 * MINUTES  # short break time
LONG_BREAK_TIME = 60 * MINUTES  # long break time


class PomodoroTimer(QWidget):
    def __init__(self):
        super().__init__()
        self.pomodoro_sound = PomodoroTimer.initialize_sound_files('clock-ticking-2.wav')
        self.short_break_sound = PomodoroTimer.initialize_sound_files('clock-ticking-1.wav')
        self.long_break_sound = PomodoroTimer.initialize_sound_files('clock-ticking-5.wav')
        self.alarm_sound = PomodoroTimer.initialize_sound_files('alarm-clock-01.wav')
        self.initialize_ui()

    @staticmethod
    def initialize_sound_files(sound_file_name):
        sound = QtMultimedia.QSoundEffect()
        sound.setSource(QtCore.QUrl.fromLocalFile(sound_file_name))
        sound.setVolume(1.0)
        return sound

    def initialize_ui(self):
        self.setMinimumSize(500, 400)
        self.setWindowTitle("PyPomodoro - v1")
        self.setWindowIcon(QIcon("images/tomato.png"))

        self.pomodoro_limit = POMODORO_TIME
        self.short_break_limit = SHORT_BREAK_TIME
        self.long_break_limit = LONG_BREAK_TIME

        self.setup_tabs_and_widgets()

        self.current_tab_selected = 0
        self.current_start_button = self.pomodoro_start_button
        self.current_stop_button = self.pomodoro_stop_button
        self.current_reset_button = self.pomodoro_reset_button
        self.current_time_limit = self.pomodoro_limit
        self.current_lcd = self.pomodoro_lcd

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        self.show()

    def setup_tabs_and_widgets(self):
        self.tab_bar = QTabWidget(self)
        self.pomodoro_tab = QWidget()
        self.pomodoro_tab.setObjectName("Pomodoro")
        self.short_break_tab = QWidget()
        self.short_break_tab.setObjectName("ShortBreak")
        self.long_break_tab = QWidget()
        self.long_break_tab.setObjectName("LongBreak")

        self.tab_bar.addTab(self.pomodoro_tab, "Pomodoro")
        self.tab_bar.addTab(self.short_break_tab, "Short Break")
        self.tab_bar.addTab(self.long_break_tab, "Long Break")

        self.tab_bar.currentChanged.connect(self.tab_switched)

        self.setup_pomodoro_tab()
        self.setup_short_break_tab()
        self.setup_long_break_tab()

        main_v_box = QVBoxLayout()
        main_v_box.addWidget(self.tab_bar)
        self.setLayout(main_v_box)

    def setup_pomodoro_tab(self):
        start_time = self.calculate_display_time(self.pomodoro_limit)

        self.pomodoro_lcd = QLCDNumber()
        self.pomodoro_lcd.setObjectName("PomodoroLCD")
        self.pomodoro_lcd.setSegmentStyle(QLCDNumber.Filled)
        self.pomodoro_lcd.display(start_time)

        self.pomodoro_start_button = QPushButton("Start")
        self.pomodoro_start_button.clicked.connect(self.start_countdown)

        self.pomodoro_stop_button = QPushButton("Stop")
        self.pomodoro_stop_button.clicked.connect(self.stop_countdown)

        self.pomodoro_reset_button = QPushButton("Reset")
        self.pomodoro_reset_button.clicked.connect(self.reset_countdown)

        button_h_box = QHBoxLayout()
        button_h_box.addWidget(self.pomodoro_start_button)
        button_h_box.addWidget(self.pomodoro_stop_button)
        button_h_box.addWidget(self.pomodoro_reset_button)

        v_box = QVBoxLayout()
        v_box.addWidget(self.pomodoro_lcd)
        v_box.addLayout(button_h_box)
        self.pomodoro_tab.setLayout(v_box)

    def setup_short_break_tab(self):
        start_time = self.calculate_display_time(self.short_break_limit)

        self.short_break_lcd = QLCDNumber()
        self.short_break_lcd.setObjectName("ShortLCD")
        self.short_break_lcd.setSegmentStyle(QLCDNumber.Filled)
        self.short_break_lcd.display(start_time)

        self.short_start_button = QPushButton("Start")
        self.short_start_button.clicked.connect(self.start_countdown)

        self.short_stop_button = QPushButton("Stop")
        self.short_stop_button.clicked.connect(self.stop_countdown)

        self.short_reset_button = QPushButton("Reset")
        self.short_reset_button.clicked.connect(self.reset_countdown)

        button_h_box = QHBoxLayout()
        button_h_box.addWidget(self.short_start_button)
        button_h_box.addWidget(self.short_stop_button)
        button_h_box.addWidget(self.short_reset_button)

        v_box = QVBoxLayout()
        v_box.addWidget(self.short_break_lcd)
        v_box.addLayout(button_h_box)
        self.short_break_tab.setLayout(v_box)

    def setup_long_break_tab(self):
        start_time = self.calculate_display_time(self.long_break_limit)

        self.long_break_lcd = QLCDNumber()
        self.long_break_lcd.setObjectName("LongLCD")
        self.long_break_lcd.setSegmentStyle(QLCDNumber.Filled)
        self.long_break_lcd.display(start_time)

        self.long_start_button = QPushButton("Start")
        self.long_start_button.clicked.connect(self.start_countdown)

        self.long_stop_button = QPushButton("Stop")
        self.long_stop_button.clicked.connect(self.stop_countdown)

        self.long_reset_button = QPushButton("Reset")
        self.long_reset_button.clicked.connect(self.reset_countdown)

        button_h_box = QHBoxLayout()
        button_h_box.addWidget(self.long_start_button)
        button_h_box.addWidget(self.long_stop_button)
        button_h_box.addWidget(self.long_reset_button)

        v_box = QVBoxLayout()
        v_box.addWidget(self.long_break_lcd)
        v_box.addLayout(button_h_box)
        self.long_break_tab.setLayout(v_box)

    def start_countdown(self):
        self.current_start_button.setEnabled(False)

        remaining_time = self.calculate_display_time(self.current_time_limit)

        if remaining_time == "00:00":
            self.reset_countdown()
            self.timer.start(1000)
        else:
            self.timer.start(1000)

    def stop_countdown(self):
        if self.timer.isActive():
            self.timer.stop()
            self.current_start_button.setEnabled(True)
        self.stop_all_sounds()

    def reset_countdown(self):
        self.stop_countdown()

        if self.current_tab_selected == 0:
            self.pomodoro_limit = POMODORO_TIME
            self.current_time_limit = self.pomodoro_limit
            reset_time = self.calculate_display_time(self.current_time_limit)
        elif self.current_tab_selected == 1:
            self.short_break_limit = SHORT_BREAK_TIME
            self.current_time_limit = self.short_break_limit
            reset_time = self.calculate_display_time(self.current_time_limit)
        elif self.current_tab_selected == 2:
            self.long_break_limit = LONG_BREAK_TIME
            self.current_time_limit = self.long_break_limit
            reset_time = self.calculate_display_time(self.current_time_limit)
        self.current_lcd.display(reset_time)

    def update_timer(self):
        remaining_time = self.calculate_display_time(self.current_time_limit)
        if remaining_time == "00:00":
            self.stop_countdown()
            self.sound_alarm()
            self.current_lcd.display(remaining_time)

        else:
            self.current_time_limit -= 1000
            self.current_lcd.display(remaining_time)
            self.play_ticking_sound()

    def sound_alarm(self):
        self.alarm_sound.stop()
        self.alarm_sound.play()

    def play_ticking_sound(self):
        if self.current_tab_selected == 0:
            self.pomodoro_sound.stop()
            self.pomodoro_sound.play()
        elif self.current_tab_selected == 1:
            self.short_break_sound.stop()
            self.short_break_sound.play()
        elif self.current_tab_selected == 2:
            self.long_break_sound.stop()
            self.long_break_sound.play()

    def stop_all_sounds(self):
        self.pomodoro_sound.stop()
        self.short_break_sound.stop()
        self.long_break_sound.stop()
        self.alarm_sound.stop()
    
    def tab_switched(self, index):
        self.current_tab_selected = index
        self.stop_countdown()
        self.stop_all_sounds()

        if self.current_tab_selected == 0:
            self.current_start_button = self.pomodoro_start_button
            self.current_stop_button = self.pomodoro_stop_button
            self.current_reset_button = self.pomodoro_reset_button
            self.pomodoro_limit = POMODORO_TIME
            self.current_time_limit = self.pomodoro_limit
            reset_time = PomodoroTimer.calculate_display_time(self.current_time_limit)
            self.current_lcd = self.pomodoro_lcd
            self.current_lcd.display(reset_time)

        elif self.current_tab_selected == 1:
            self.current_start_button = self.short_start_button
            self.current_stop_button = self.short_stop_button
            self.current_reset_button = self.short_reset_button
            self.short_break_limit = SHORT_BREAK_TIME
            self.current_time_limit = self.short_break_limit
            reset_time = PomodoroTimer.calculate_display_time(self.current_time_limit)
            self.current_lcd = self.short_break_lcd
            self.current_lcd.display(reset_time)

        elif self.current_tab_selected == 2:
            self.current_start_button = self.long_start_button
            self.current_stop_button = self.long_stop_button
            self.current_reset_button = self.long_reset_button
            self.long_break_limit = LONG_BREAK_TIME
            self.current_time_limit = self.long_break_limit
            reset_time = PomodoroTimer.calculate_display_time(self.current_time_limit)
            self.current_lcd = self.long_break_lcd
            self.current_lcd.display(reset_time)

    @staticmethod
    def convert_total_time(time_in_milli):
        hours = (time_in_milli // (1000 * 60)) // 60
        minutes = (time_in_milli // (1000 * 60)) % 60
        seconds = (time_in_milli // 1000) % 60
        return hours, minutes, seconds

    @staticmethod
    def calculate_display_time(time):
        hours, minutes, seconds = PomodoroTimer.convert_total_time(time)
        minutes += hours*60
        amount_of_time = "{:02d}:{:02d}".format(minutes, seconds)
        return amount_of_time


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(style_sheet)
    window = PomodoroTimer()
    sys.exit(app.exec_())
