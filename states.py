from PySide2.QtGui import QColor, QPalette


class State:
    def __init__(self, time_limit):
        self.started = False
        self.paused = False
        self.non_pomodoro_started = False
        self.non_pomodoro_paused = False
        self.current_time = 0
        self.time_limit = time_limit
        self.show_blink = True
        self.lcd_color = QPalette()
        self.prefix = ""


class PomodoroState(State):
    def __init__(self, time_limit):
        super().__init__(time_limit)
        self.lcd_color.setColor(QPalette.Foreground, QColor("orangered"))
        self.prefix = "\u2b22"


class ShortBreakState(State):
    def __init__(self, time_limit):
        super().__init__(time_limit)
        self.lcd_color.setColor(QPalette.Foreground, QColor("yellow"))
        self.prefix = "\u25b2"


class LongBreakState(State):
    def __init__(self, time_limit):
        super().__init__(time_limit)
        self.lcd_color.setColor(QPalette.Foreground, QColor("green"))
        self.prefix = "\u25bc"
