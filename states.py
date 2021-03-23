from PySide2.QtGui import QColor, QPalette

MINUTES = 60*1000
POMODORO_TIME = 30*MINUTES
SHORT_BREAK_TIME = 6*MINUTES
LONG_BREAK_TIME = 60*MINUTES


class State:
    def __init__(self):
        self.started = False
        self.paused = False
        self.current_time = 0
        self.show_blink = True
        self.lcd_color = QPalette()
        self.prefix = ""


class PomodoroState(State):
    def __init__(self):
        super().__init__()
        self.time_limit = POMODORO_TIME
        self.lcd_color.setColor(QPalette.Foreground, QColor("red"))
        self.prefix = "P"


class ShortBreakState(State):
    def __init__(self):
        super().__init__()
        self.time_limit = SHORT_BREAK_TIME
        self.lcd_color.setColor(QPalette.Foreground, QColor("yellow"))
        self.prefix = "S"


class LongBreakState(State):
    def __init__(self):
        super().__init__()
        self.time_limit = LONG_BREAK_TIME
        self.lcd_color.setColor(QPalette.Foreground, QColor("green"))
        self.prefix = "L"
