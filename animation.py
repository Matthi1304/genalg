from math import atan2, pi
import os
from random import choice, randint


FADER = 'fader'
BLACK = (0, 0, 0, 1)


class Animation:

    def __init__(self, clock, exclusive=True, sound_file=None):
        self.clock = clock
        self.active = False
        self.exclusive = exclusive
        self.sound_file = sound_file
        if sound_file is not None:
            if os.path.exists(self.sound_file):
                self.sound_file = sound_file
            else:
                self.sound_file = None
        else:
            prefix = self.__class__.__name__.lower() + "."
            for filename in os.listdir("audio"):
                if filename.startswith(prefix):
                    self.sound_file = os.path.join("audio", filename)
                    break
            if not self.sound_file:
                print(f"No sound file for animation found, should match 'audio/{self.__class__.__name__.lower()}.*'.")

    
    def start(self):
        """
        Start the animation.
        Default implementation just sets self.active to True.
        """
        self.active = True
        self.counter = 0
        self.sound_fader = None
        self.sound = None
        if self.sound_file:
            self.sound = self.clock.loader.loadSfx(self.sound_file)
            self.sound.setVolume(1.0)
            self.sound.play()
            self.sound_fader = sound_fader(self.sound)
            


    def stop(self):
        """
        Call this to stop the animation gracefully.
        Sets self.active to False and calls cleanup().
        """
        self.cleanup()
        self.active = False


    def cleanup(self):
        """
        Cleanup after the animation is stopped.
        Default implementation cleans any fader attributes and resets colors of all digits.
        """
        for digit in filter(lambda d: FADER in d, self.clock.placed_numbers):
            digit.pop(FADER, None)
        self.clock.color_all_digits(color=BLACK)
        if self.sound:
            self.sound.stop()
            self.sound = None
            self.sound_fader = None


    def animate(self):
        """
        Animate one step.
        Calls update() and increments the counter if the animation is active.
        Returns True if the animation wants to continue, False to stop.
        """
        if not self.active:
            return False
        continue_animation = self.update()
        self.counter += 1
        if continue_animation == False:
            self.stop()
            return False
        return True
    

    def update(self):
        """
        Update the animation.
        Return False if the animation is finished.
        Default implementation just returns False.
        """
        return False


    def fade(self):
        """
        Takes care of fading for all active fading digits.
        If a sound is associated with the animation, it also fades out the sound when no other qfaders are left.
        Returns True if there are still faders active, False otherwise.
        """
        has_faders = False
        for digit in filter(lambda d: FADER in d, self.clock.placed_numbers):
            try:
                next_color = next(digit[FADER])
                digit['text_node'].setFg(next_color)
                has_faders = True
            except StopIteration:
                digit.pop(FADER, None)
        if not has_faders and self.sound_fader:
            try:
                return next(self.sound_fader)
            except StopIteration:
                self.sound.stop()
                self.sound = None
                self.sound_fader = None
        return has_faders
    

    def has_faders(self):
        return self.sound_fader or any(FADER in d for d in self.clock.placed_numbers)
    

# Helper functions


def distance_from_center(digit):
    return (digit['x'] ** 2 + digit['y'] ** 2) ** 0.5


def register_color_fader(digit, start_color, end_color, step, both_ways=True):

    def fade_to(start_color, end_color, step):
        for i in range(step + 1):
            ratio = i / step
            r = start_color[0] + (end_color[0] - start_color[0]) * ratio
            g = start_color[1] + (end_color[1] - start_color[1]) * ratio
            b = start_color[2] + (end_color[2] - start_color[2]) * ratio
            yield (r, g, b, 1)

    def fade_to_and_back(start_color, end_color, step):
        """Generate colors fading from start_color to end_color and back again in given steps"""
        for color in fade_to(start_color, end_color, step // 2 - 1):
            yield color
        yield end_color
        yield end_color
        for color in fade_to(end_color, start_color, step // 2 - 1):
            yield color

    def update_and_get_next_color(digit, fader):
        for color in fader:
            digit['text_node'].setFg(color)
            yield color

    generator = fade_to_and_back(start_color, end_color, step) if both_ways else fade_to(start_color, end_color, step)
    digit[FADER] = generator
    


def sound_fader(sound):
    """Generator that fades out the sound volume"""
    current_volume = sound.getVolume()
    while current_volume > 0.0 and sound.status() == sound.PLAYING:
        current_volume -= 0.002 
        sound.setVolume(max(0.0, current_volume))
        yield True
    sound.stop()
    yield False


# Animations


class FillPie(Animation):
    """
    An animation that fills the display area like a pie chart, coloring digits as it goes.
    """

    def __init__(self, clock, color=None):
        super().__init__(clock, exclusive=True)
        if color is None:
            self.target_color = choice([clock.red, clock.green, clock.blue, clock.yellow, clock.cyan])
        else:
            self.target_color = color
        self.step = 0.02 # fraction of full circle per update
        self.current_angle = 0.0
    

    def start(self):
        super().start()
    

    def update(self):
        angle_limit = self.current_angle + self.step * 360.0
        for digit in filter(lambda d: not FADER in d, self.clock.placed_numbers):
            angle = (180.0 / pi) * -1.0 * atan2(digit['y'], digit['x']) + 180.0
            if self.current_angle <= angle < angle_limit:
                register_color_fader(digit, BLACK, self.target_color, 100)
        self.current_angle += self.step * 360.0
        if self.current_angle >= 360.0:
            return self.fade()
        return True


class Blob(Animation):
    """
    An animation that makes a blob of digits light up and fade out, 
    Either starting at the center of the screen or from outside in.
    """

    def __init__(self, clock, number=None, color=None):
        super().__init__(clock, exclusive=True)
        if color is None:
            self.target_color = choice([clock.red, clock.green, clock.blue, clock.yellow, clock.cyan])
        else:
            self.target_color = color
        self.step = 15 # number of steps for each radius increment
        self.fade_cycle = self.step * 20 # number of update steps for a full fade in or fadeout
    

    def start(self):
        super().start()
        x1, y1, x2, y2 = self.clock.get_display_area()
        if choice((True, False)):
            self.max_radius = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 # diagonal distance
            self.radius_step = self.max_radius / 20
            self.current_radius = min(map(lambda d: distance_from_center(d), self.clock.placed_numbers)) + self.radius_step / 2

        else:
            self.max_radius = max(map(lambda d: distance_from_center(d), self.clock.placed_numbers))
            self.radius_step = -self.max_radius / 20
            self.current_radius = self.max_radius - self.radius_step / 2


    def update(self):
        if self.counter % self.step == 0:
            for digit in filter(lambda d: not FADER in d, self.clock.placed_numbers):
                distance = distance_from_center(digit)
                interval = (self.current_radius, self.current_radius + self.radius_step)
                if (min(interval) <= distance < max(interval)):
                    register_color_fader(digit, BLACK, self.target_color, self.fade_cycle)
            self.current_radius += self.radius_step
        return self.fade()
    

class WanderingDigit(Animation):
    """
    An animation that makes digits wander around randomly, but adjacent.
    """

    def __init__(self, clock, number=None, color=None):
        super().__init__(clock, exclusive=True)
        self.number = number if number is not None else randint(0, 15)
        if color is None:
            self.target_color = choice([clock.red, clock.green, clock.blue, clock.yellow, clock.cyan])
        else:
            self.target_color = color
        self.step = 200 # number of update steps for a full fade in or fadeout
        if self.number > 9:
            self.update_interval = self.step // 20
        else:
            self.update_interval = self.step // 4
    

    def start(self):
        super().start()
        x1, y1, x2, y2 = self.clock.get_display_area()
        self.pos = (choice((x1, x2)), choice((y1, y2)))
        self.visited = []
    

    def cleanup(self):
        super().cleanup()
        self.visited = []
    

    def update(self):
        if (self.counter % self.update_interval) == 0:
            next = self.clock.get_nearest_digit(
                self.pos[0],
                self.pos[1],
                skip=lambda item: (self.number <= 9 and item['digit'] != self.number) or item in self.visited
            )
            if next is not None:
                register_color_fader(next, BLACK, self.target_color, self.step * 2)
                self.visited.append(next)
                self.pos = (next['x'], next['y'])
        return self.fade()


class Sweeper(Animation):
    """
    An animation that sweeps across the display area, coloring digits. No fading.
    """

    def __init__(self, clock, color=None):
        super().__init__(clock, exclusive=True)
        if color is None:
            self.target_color = choice([clock.red, clock.green, clock.blue, clock.yellow, clock.cyan, clock.white])
        else:
            self.target_color = color
        self.step = 0.01
        self.width = 0.4  # width of the sweeper as fraction of display area
        self.position = -1.0  # Start from the left outside the display area
        self.mode = 'left-to-right'
    

    def start(self):
        super().start()
        self.x_start, _, self.x_end, _ = self.clock.get_display_area()
        self.width = (self.x_end - self.x_start) * self.width
         

    def update(self):
        sweep_x = self.x_start + (self.x_end - self.x_start) * ((self.position + 1.0) / 2.0)
        for digit in self.clock.placed_numbers:
            if digit['x'] <= sweep_x - self.width:
                digit['text_node'].setFg(BLACK)
            elif digit['x'] <= sweep_x:
                digit['text_node'].setFg(self.target_color)
        self.position += self.step
        if self.position > 1.0 + self.width:
            return False
        return True


class Countdown(Animation):
    """
    An animation that counts down from a 9 to 0
    """

    def __init__(self, clock, start_number=9, color=None):
        super().__init__(clock, exclusive=True)
        self.current_number = start_number
        if color is None:
            self.target_color = choice([clock.red, clock.green, clock.blue, clock.yellow, clock.cyan, clock.white])
        else:
            self.target_color = color
        self.hide_counted_digits = choice([True, False, False, False])  # mostly do not hide
        if self.hide_counted_digits:
            self.step = 90
        else:
            self.step = randint(40,70)
        self.fade_animation = choice([True, False, False])  # mostly no fading
        if self.fade_animation:
            self.step += 100
    

    def start(self):
        super().start()
        self.current_number = 9


    def update(self):
        if (self.counter % self.step) == 0 and self.current_number >= 0:
            for digit in self.clock.placed_numbers:
                if digit['digit'] == self.current_number:
                    if self.fade_animation:
                        register_color_fader(digit, BLACK, self.target_color, int(self.step * 1.4))
                    else:
                        digit['text_node'].setFg(self.target_color)
                elif not self.fade_animation and self.hide_counted_digits and digit['digit'] > self.current_number:
                    digit['text_node'].setFg(BLACK)
            self.current_number -= 1
        if self.current_number == -1 and not self.hide_counted_digits and not self.fade_animation:
            # if all colors are shown, then fade them out at the end
            for digit in self.clock.placed_numbers:
                if digit['digit'] >= 0:
                    register_color_fader(digit, digit['text_node'].fg, BLACK, int(self.step * 1.4), both_ways=False)
            self.fade_animation = True
        if self.fade_animation:
            return self.fade()                    
        return self.current_number >= 0