# Clock class for displaying the current time
# load beamer.json and place the digits accordingly
from base import ClockBase    
from datetime import datetime
import random
import sys
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import OnscreenText  

class Clock(ClockBase):

    def __init__(self, config_file="beamer.json", time=None):
        super().__init__(config_file=config_file, digit_color=(0.1, 0.1, 0.1, 1))

        self.black = (0, 0, 0, 1)
        self.white = (1, 1, 1, 1)
        self.red = (1, 0, 0, 1 )
        self.green = (0, 1, 0, 1)
        self.blue = (0, 0, 1, 1)
        self.yellow = (1, 1, 0, 1)
        self.nearly_white = (0.8, 0.8, 0.8, 1)
        self.nearly_black = (0.1, 0.1, 0.1, 1)
        self.default_color = self.nearly_black
        self.background_color = self.black

        self.accept("c", self.change_colors)
        self.accept("s", self.show_all_digits)

        self.add_help_text("Press 'c' to change highlight colors")
        self.add_help_text("Press 's' to show/hide of digits")
        print("=======================================================================")

        self.set_colors(self.white, self.green, self.red)

        if time:
            print(f"Displaying static time: {time}")
            self.display_time(time.replace(':',''))
        else: 
            self.taskMgr.add(self.display_time_task, "DisplayTimeTask")

    
    def set_colors(self, *colors):
        if len(colors) == 1:
            self.highlight_color = [colors[0] for _ in range(6)]
        elif len(colors) == 3:
            self.highlight_color = [colors[0], colors[1], colors[2]]
        self.last_time = "hhmmss" # force clock update


    def change_colors(self):
        if self.highlight_color[0] == self.white:
            self.set_colors(self.green, self.blue, self.red)
        elif self.highlight_color[0] == self.green:
            self.set_colors(self.yellow, self.red, self.blue)
        elif self.highlight_color[0] == self.yellow:
            self.set_colors(self.red, self.green, self.yellow)
        else:
            self.set_colors(self.white, self.green, self.red)
        self.last_time = "hhmmss" # force clock update

    
    def show_all_digits(self):
        if self.default_color == self.white:
            self.default_color = self.nearly_black
        elif self.default_color == self.nearly_black:
            self.default_color = self.black
        else:
            self.default_color = self.white
        self.last_time = "hhmmss" # force clock update


    def display_time_task(self, task):
        self.display_time(datetime.now().strftime("%H%M%S"))
        return Task.cont


    def _set_color_to_random_digit(self, source, digit, color):
        candidates = list(filter(lambda item: item['digit'] == digit, source))
        if not candidates:
            print(f"Warning: no candidates found for digit {digit}, time {self.last_time}")
        else:
            digit = random.choice(candidates)
            if digit is not None:
                digit['text_node'].setFg(color)
        return digit


    def display_time(self, t):
        if not hasattr(self, 'quadrants'):
            self.last_time = "hhmmss"
            self.distribute_digits_in_quadrants()
            self.hours = []
            self.minutes = []
            self.seconds = []
        if len(t) == 5:
            t = '0' + t
        if t == self.last_time:
            return
        # clear seconds
        for digit in self.seconds:
            digit['text_node'].setFg(self.default_color)
        self.seconds = []
        change_hours = t[2] != self.last_time[2] # every ten minutes
        change_minutes = t[3] != self.last_time[3] # every minute
        self.last_time = t
        if change_hours:
            for digit in self.hours:
                digit['text_node'].setFg(self.default_color)
            if t[0] == 0:
                self.hours.append(self._set_color_to_random_digit(self.quadrants[0] + self.quadrants[1], int(t[1]), self.highlight_color[0]))
            else:
                self.hours.append(self._set_color_to_random_digit(self.quadrants[0], int(t[0]), self.highlight_color[0]))
                self.hours.append(self._set_color_to_random_digit(self.quadrants[1], int(t[1]), self.highlight_color[0]))
        if change_minutes:
            for digit in self.minutes:
                digit['text_node'].setFg(self.default_color)
            self.minutes.append(self._set_color_to_random_digit(self.quadrants[2], int(t[2]), self.highlight_color[1]))
            self.minutes.append(self._set_color_to_random_digit(self.quadrants[3], int(t[3]), self.highlight_color[1]))
        # set seconds randomly
        used_digits = self.hours + self.minutes
        while None in used_digits:
            used_digits.remove(None)
        unused_digits = self.placed_numbers.copy()
        for digit in used_digits:
            if (digit in unused_digits):
                unused_digits.remove(digit)
        second_1 = self._set_color_to_random_digit(unused_digits, int(t[4]), self.highlight_color[2])
        unused_digits.remove(second_1)
        second_2 = self._set_color_to_random_digit(unused_digits, int(t[5]), self.highlight_color[2])
        self.seconds.append(second_1)
        self.seconds.append(second_2)


if __name__ == "__main__":
    loadPrcFile("clock.prc")
    config_file = "beamer.json"
    if (len(sys.argv) > 1 and sys.argv[1] != "-t"):
        config_file = sys.argv.pop(1)
    time = sys.argv[2] if (len(sys.argv) > 2 and sys.argv[1] == "-t") else None
    app = Clock(config_file=config_file, time=time)
    app.run()

