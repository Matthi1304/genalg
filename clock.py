# Clock class for displaying the current time
# load beamer.json and place the digits accordingly
from base import ClockBase    
import animation
from datetime import datetime, timedelta
import random
import sys
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import OnscreenText  

class Clock(ClockBase):

    def __init__(self, config_file="beamer.json"):
        super().__init__(config_file=config_file, digit_color=(0.1, 0.1, 0.1, 1))

        self.black = (0, 0, 0, 1)
        self.white = (1, 1, 1, 1)
        self.red = (1, 0, 0, 1 )
        self.green = (0, 1, 0, 1)
        self.blue = (0, 0, 1, 1)
        self.yellow = (1, 1, 0, 1)
        self.cyan = (0, 1, 1, 1)
        self.nearly_white = (0.8, 0.8, 0.8, 1)
        self.nearly_black = (0.1, 0.1, 0.1, 1)
        self.default_color = self.black
        self.background_color = self.black

        self.time_delta = 0  # time offset in seconds

        self.accept("c", self.change_colors)
        self.accept("s", self.color_all_digits)

        self.accept("arrow_right", self.adjust_time, [60])
        self.accept("arrow_right-repeat", self.adjust_time, [60])
        self.accept("arrow_left", self.adjust_time, [-60])
        self.accept("arrow_left-repeat", self.adjust_time, [-60])
        self.accept("r", self.reset_time)

        self.animation = None
        self.animations = [
            animation.Countdown, 
            animation.WanderingDigit, 
            animation.Sweeper
        ]
        self.accept("a", self.toggle_animation)

        self.accept("q", sys.exit)


        self.add_help_text("Press 'c' to change highlight colors")
        self.add_help_text("Press 's' to show/hide of digits")
        self.add_help_text("Use left or right arrow to change time")
        self.add_help_text("Press 'r' to reset time")
        self.add_help_text("Press 'a' to start or stop an animation")
        print("=======================================================================")

        self.toggle_help() # do not show help by default

        self.set_colors(self.white, self.green, self.red)

        self.last_time = "245959"
        self.distribute_digits_in_quadrants()
        self.hours = []
        self.minutes = []
        self.seconds = []
        self.taskMgr.add(self.display_time_task, "DisplayTimeTask")

    
    def set_colors(self, *colors):
        if len(colors) == 1:
            self.highlight_colors = [colors[0] for _ in range(6)]
        elif len(colors) == 3:
            self.highlight_colors = [colors[0], colors[1], colors[2]]
        self.force_clock_update()


    def change_colors(self):
        if self.highlight_colors[0] == self.white:
            self.set_colors(self.green, self.blue, self.red)
        elif self.highlight_colors[0] == self.green:
            self.set_colors(self.yellow, self.red, self.blue)
        elif self.highlight_colors[0] == self.yellow:
            self.set_colors(self.red, self.green, self.yellow)
        else:
            self.set_colors(self.white, self.green, self.red)
        self._fix_highlight_colors()
        self.force_clock_update()

        self._fix_highlight_colors()
        self.force_clock_update()

    
    def color_all_digits(self, color=None):
        if color:
            self.default_color = color
        elif self.default_color == self.white:
            self.default_color = self.nearly_black
        elif self.default_color == self.nearly_black:
            self.default_color = self.black
        else:
            self.default_color = self.white

        for digit in self.placed_numbers:
            digit['text_node'].setFg(self.default_color)

        self._fix_highlight_colors()
        self.force_clock_update()


    def _fix_highlight_colors(self):
        unused_colors = list(
            {self.white, self.green, self.red, self.blue, self.yellow, self.cyan}
             - {self.default_color}
             - set(self.highlight_colors)
        )
        random.shuffle(unused_colors)
        for i, color in enumerate(self.highlight_colors):
            if (color == self.default_color):
                self.highlight_colors[i] = unused_colors.pop()


    def adjust_time(self, delta):
        self.time_delta += delta
    

    def reset_time(self):
        self.time_delta = 0


    def force_clock_update(self):
        self.last_time = "999999"
            

    def display_time_task(self, task):
        if self.animation is not None:
            if self.animation.active:
                self.animation.update()
                if self.animation.exclusive:
                    return Task.cont
            else:
                self.animation = None
        self.display_time((datetime.now() + timedelta(seconds=self.time_delta)).strftime("%H%M%S"))
        return Task.cont


    def toggle_animation(self):
        if self.animation is not None and self.animation.active:
            self.animation.stop()
            self.animation = None
            self.force_clock_update()
        else:
            clazz = self.animations.pop(0)
            self.animations.append(clazz)
            self.animation = clazz(self)
            self.animation.start()
            if self.animation.exclusive:
                self.color_all_digits(color=self.black)


    def _set_color_to_random_digit(self, source, digit, color, remove_from_source=False):
        candidates = list(filter(lambda item: item['digit'] == digit, source))
        if not candidates:
            print(f"Warning: no candidates found for digit {digit}, time {self.last_time}")
            return None
        else:
            digit = random.choice(candidates)
            if digit is not None:
                digit['text_node'].setFg(color)
                if remove_from_source:
                    source.remove(digit)
            return digit


    def _reset(self, digits):
        for digit in digits:
            digit['text_node'].setFg(self.default_color) if digit is not None else None
        digits.clear()


    def display_time(self, t):
        if len(t) == 5:
            t = '0' + t
        if t == self.last_time:
            return
        # clear seconds
        self._reset(self.seconds)
        change_hours = t[2] != self.last_time[2] # every ten minutes
        change_minutes = t[3] != self.last_time[3] # every minute
        self.last_time = t
        if change_hours:
            self._reset(self.hours)
            if t[0] == '0':
                self.hours.append(self._set_color_to_random_digit(self.quadrants[0] + self.quadrants[1], int(t[1]), self.highlight_colors[0]))
            else:
                self.hours.append(self._set_color_to_random_digit(self.quadrants[0], int(t[0]), self.highlight_colors[0]))
                self.hours.append(self._set_color_to_random_digit(self.quadrants[1], int(t[1]), self.highlight_colors[0]))
        if change_minutes:
            self._reset(self.minutes)
            self.minutes = []
            self.minutes.append(self._set_color_to_random_digit(self.quadrants[2], int(t[2]), self.highlight_colors[1]))
            self.minutes.append(self._set_color_to_random_digit(self.quadrants[3], int(t[3]), self.highlight_colors[1]))
        # set seconds randomly
        used_digits = self.hours + self.minutes
        while None in used_digits:
            used_digits.remove(None)
        unused_digits = self.placed_numbers.copy()
        for digit in used_digits:
            if (digit in unused_digits):
                unused_digits.remove(digit)
        self.seconds.append(self._set_color_to_random_digit(unused_digits, int(t[4]), self.highlight_colors[2], remove_from_source=True))
        self.seconds.append(self._set_color_to_random_digit(unused_digits, int(t[5]), self.highlight_colors[2]))


if __name__ == "__main__":
    loadPrcFile("clock.prc")
    config_file = "beamer.json"
    if len(sys.argv) > 1:
        config_file = sys.argv.pop(1)
    app = Clock(config_file=config_file)
    app.run()
