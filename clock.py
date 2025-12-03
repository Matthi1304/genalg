# Clock class for displaying the current time
# load beamer.json and place the digits accordingly
import os
import traceback
from base import ClockBase    
import animation
from datetime import datetime, timedelta
import random
import sys
from panda3d.core import *
from panda3d.core import loadPrcFile
from direct.showbase.ShowBase import ShowBase
from direct.task import Task

# this is fully transparent, rgb values are ignored
BLACK = (0, 0, 0, 0) 

class Clock(ClockBase):

    def __init__(self, config_file="beamer.json"):
        super().__init__(config_file=config_file, digit_color=BLACK)

        self.black = BLACK
        self.white = (1, 1, 1, 1)
        self.nearly_black = (0.1, 0.1, 0.1, 1)
        self.red = (1, 0, 0, 1)
        self.green = (0, 1, 0, 1)
        self.blue = (0, 0, 1, 1)
        self.yellow = (1, 1, 0, 1)
        self.cyan = (0, 1, 1, 1)
        self.default_color = self.black
        self.background_color = self.black

        self.color_sets = [
            # exhibition poster colors: , yellow, green, dark blue
            ((253/255, 235/255, 25/255, 1), (63/255, 165/255, 53/255, 1), (40/255, 53/255, 131/255, 1)), 
            (self.white, self.green, self.red),
            (self.green, self.blue, self.red),
            (self.yellow, self.red, self.blue),
            (self.red, self.green, self.yellow)
        ]

        self.time_delta = 0  # time offset in seconds

        self.accept("c", self.change_colors)
        self.accept("s", self.color_all_digits)
        self.accept("m", self.toggle_fast_clock_mode, [5])
        self.toggle_fast_clock_mode(5)  # start in fast mode

        self.accept("arrow_up", self.adjust_time, [60])
        self.accept("arrow_up-repeat", self.adjust_time, [60])
        self.accept("arrow_down", self.adjust_time, [-60])
        self.accept("arrow_down-repeat", self.adjust_time, [-60])
        self.accept("shift-arrow_up", self.adjust_time, [3600])
        self.accept("shift-arrow_down", self.adjust_time, [-3600])
        self.accept("r", self.reset_time)

        self.animation = None
        self.animations = [
            animation.Blob,
            animation.Countdown, 
            animation.WanderingDigit,
            animation.Random,
            animation.Sweeper,
            animation.FillPie,
            animation.Heartbeat
        ]
        self.accept("a", self.toggle_animation, [None])
        for i, animation_class in enumerate(self.animations, start=1):
            if i <= 10:
                self.accept(str(i % 10), self.toggle_animation, [animation_class])

        self.accept("q", sys.exit)


        self.add_help_text("Press 'c' to change highlight colors")
        self.add_help_text("Press 's' to show/hide of digits")
        self.add_help_text("Use (shift) up, down arrow to change time")
        self.add_help_text("Press 'r' to reset time to real time")
        self.add_help_text("Press 'a' to start or stop an animation")
        self.add_help_text("Press 'm' to toggle 'mode fast' for changing digits of clock")
        self.add_help_text("Press any number key to trigger a specific animation")
        for i, animation_class in enumerate(self.animations, start=1):
            if i <= 10:
                print(f"  Press '{i % 10}' to trigger {animation_class.__name__}")
        print("=======================================================================")

        self.toggle_help() # do not show help by default

        self.set_colors(self.color_sets[0])

        self.last_time = "245959"
        self.taskMgr.add(self.update_task, "MainLoop")

        self.tic_sound = self.loader.loadSfx(self.find_audio_file("tic.", "audio/tic.wav"))
        self.last_tic = -1
        gong_sound_file = self.find_audio_file("gong.", "audio/gong.wav")
        self.gong_sounds = [self.loader.loadSfx(gong_sound_file) for _ in range(12)] 


    def find_audio_file(self, prefix, default=None):
        for filename in os.listdir("audio"):
            if filename.startswith(prefix):
                return os.path.join("audio", filename)
        return default
    
    
    def set_colors(self, colors):
        self.highlight_colors = colors
        self.force_clock_update()


    def change_colors(self):
        index = self.color_sets.index(self.highlight_colors)
        index = (index + 1) % len(self.color_sets)
        self.set_colors(self.color_sets[index])
        self.color_all_digits(self.default_color)

    
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
        self.force_clock_update()


    def force_clock_update(self):
        self.last_time = "999999"
            

    def update_task(self, task):
        t = datetime.now() + timedelta(seconds=self.time_delta)
        self.play_clock_sounds(t)
        self.do_animation_at_random_time()
        if self.animation is not None:
            if self.animation.active:
                self.animation.animate()
                if self.animation.exclusive:
                    return Task.cont
            else:
                self.animation = None
        try:
            self.display_time(t.strftime("%H%M%S"))
        except Exception:
            print(traceback.format_exc())
        return Task.cont


    def do_animation_at_random_time(self):
        if self.animation is None:
            t = datetime.now()
            if not hasattr(self, 'next_animation_time'):
                self.next_animation_time = t + timedelta(seconds=random.randint(118, 300))
            if t >= self.next_animation_time:
                delta = t - self.next_animation_time
                self.next_animation_time = t + timedelta(seconds=random.randint(118, 300))
                if delta.total_seconds() < 1:
                    self.toggle_animation()

    
    def play_clock_sounds(self, t):
        if t.minute == 0:
            h = t.hour % 12
            if t.hour == 0:
                h = 12
            index = t.second // 2
            if index < h and self.gong_sounds[index].status() != self.gong_sounds[index].PLAYING:
                self.gong_sounds[index].play()
        if t.second != self.last_tic and t.microsecond < 100000:
            self.tic_sound.play()
            self.last_tic = t.second


    def toggle_animation(self, animation_class=None):
        if self.animation is not None and self.animation.active:
            self.animation.stop()
            self.animation = None
            self.force_clock_update()
        else:
            if animation_class is None:
                animation_class = self.animations.pop(0)
                self.animations.append(animation_class)
            self.animation = animation_class(self)
            self.animation.start()
            if self.animation.exclusive:
                self.color_all_digits(color=self.black)


    def toggle_fast_clock_mode(self, default=5):
        """
        Toggle fast clock mode: when enabled, the digits change more frequently for demonstration purposes.
        'default' specifies how often (in seconds) the digits should change in fast mode;
        should be less than 60 seconds.        
        """
        if not hasattr(self, 'change_digits_every_x_seconds'):
            self.change_digits_every_x_seconds = 0 # default value: fast mode off
        if self.change_digits_every_x_seconds == 0:
            self.change_digits_every_x_seconds = default
            print(f"Mode fast switched ON: digits change every {default} seconds")
        else:
            print("Mode fast switched OFF")
            self.change_digits_every_x_seconds = 0


    def display_time(self, t, iteration_count=40):

        def clear_digits_with_color(color):
            for digit in self.placed_numbers:
                if digit['text_node'].fg == color:
                    digit['text_node'].setFg(self.default_color)

        def get_digits(i, color):
            digits = []
            for digit in self.placed_numbers:
                if digit['digit'] == i and digit['text_node'].fg == color:
                    digits.append(digit)
            return digits

        if len(t) == 5:
            t = '0' + t
        if t == self.last_time:
            return

        # at least every hour
        change_hours = (t[:2] != self.last_time[:2]) 
        # check for fast clock change mode
        if hasattr(self, 'change_digits_every_x_seconds') and (self.change_digits_every_x_seconds > 0):
            seconds = int(t[4:6])
            if seconds % self.change_digits_every_x_seconds == 0:
                change_hours = True
        # every time we change the hours or at least every minute
        change_minutes = change_hours or (t[:3] != self.last_time[:3]) 
        # also every minute
        change_hours = change_minutes 

        h0, h1, m0, m1, s0, s1 = [int(c) for c in t]
        h_color, m_color, s_color = self.highlight_colors

        clear_digits_with_color(s_color)
        if change_minutes:
            clear_digits_with_color(m_color)
        if change_hours:
            clear_digits_with_color(h_color)        

        updates_needed = 3 if change_hours else (2 if change_minutes else 1)

        if change_hours and h0 == 0:
            clear_digits_with_color(h_color)        
            digit_h1 = random.choice(get_digits(h1, self.default_color))
            digit_h1['text_node'].setFg(h_color)
            updates_needed -= 1
        
        if change_hours and h0 != 0:
            for _ in range(iteration_count):
                digit_h0 = random.choice(get_digits(h0, self.default_color))
                digit_h1 = random.choice(get_digits(h1, self.default_color))
                if digit_h0 != digit_h1 and digit_h0['x'] < digit_h1['x']: # and digit_h0['y'] > digit_h1['y']:
                    digit_h0['text_node'].setFg(h_color)
                    digit_h1['text_node'].setFg(h_color)
                    updates_needed -= 1
                    break

        if change_minutes:
            for _ in range(iteration_count):
                digit_m0 = random.choice(get_digits(m0, self.default_color))
                digit_m1 = random.choice(get_digits(m1, self.default_color))
                if digit_m0 != digit_m1 and digit_m0['x'] < digit_m1['x'] and digit_m0['y'] > digit_m1['y']:
                    digit_m0['text_node'].setFg(m_color)
                    digit_m1['text_node'].setFg(m_color)
                    updates_needed -= 1
                    break

        for _ in range(iteration_count):
            digit_s0 = random.choice(get_digits(s0, self.default_color))
            digit_s1 = random.choice(get_digits(s1, self.default_color))
            if digit_s0 != digit_s1 and digit_s0['x'] < digit_s1['x']:
                digit_s0['text_node'].setFg(s_color)
                digit_s1['text_node'].setFg(s_color)
                updates_needed -= 1
                break

        if updates_needed > 0:
            self.failed_update = t
        else:  
            # successful 
            if hasattr(self, 'failed_update') and self.failed_update != t:
                f = self.failed_update
                print(f"{t[:2]}:{t[2:4]}:{t[4:6]}: Successful clock update after previous failures for time {f[:2]}:{f[2:4]}:{f[4:6]}")
                del self.failed_update
            self.last_time = t


    def print_stats(self):
        super().print_stats()
        print(f"Current displayed time: {self.last_time[:2]}:{self.last_time[2:4]}:{self.last_time[4:6]}")


if __name__ == "__main__":
    loadPrcFile("clock.prc")
    config_file = "beamer.json"
    if len(sys.argv) > 1:
        config_file = sys.argv.pop(1)
    app = Clock(config_file=config_file)
    app.run()
