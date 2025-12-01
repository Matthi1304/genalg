from random import choice, randint


BLACK = (0, 0, 0, 1)

class Animation:

    def __init__(self, clock, exclusive=True):
        self.clock = clock
        self.active = False
        self.exclusive = exclusive
    
    def start(self):
        """
        Start the animation.
        Default implementation just sets self.active to True.
        """
        self.active = True


    def stop(self):
        """
        Stop the animation.
        Default implementation just sets self.active to False and calls cleanup().
        """
        self.cleanup()
        self.active = False


    def cleanup(self):
        """
        Cleanup after the animation is stopped.
        Default implementation does nothing.
        """
        pass


    def update(self):
        """
        Update the animation.
        Return True if the animation wants to continue, False to stop.
        Default implementation returns self.active.
        """
        return self.active
    


# Helper functions for fading colors

def fade_color_to(start_color, end_color, step):
    """Generate colors fading from start_color to end_color in given steps"""
    for i in range(step + 1):
        ratio = i / step
        r = start_color[0] + (end_color[0] - start_color[0]) * ratio
        g = start_color[1] + (end_color[1] - start_color[1]) * ratio
        b = start_color[2] + (end_color[2] - start_color[2]) * ratio
        yield (r, g, b, 1)


def fade_color_to_and_back_again(start_color, end_color, step):
    """Generate colors fading from start_color to end_color and back again in given steps"""
    for color in fade_color_to(start_color, end_color, step // 2):
        yield color
    for color in fade_color_to(end_color, start_color, step // 2):
        yield color


# Example animations


class WanderingDigit(Animation):
    """
    An example animation that makes digits wander around randomly.
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
        print(f"Starting WanderingDigits animation for digit {self.number} and color {self.target_color[0:3]}")
        self.counter = 0
        x1, y1, x2, y2 = self.clock.get_display_area()
        self.pos = (choice((x1, x2)), choice((y1, y2)))
        self.visited = []
        self.fading_counter = 0
    

    def cleanup(self):
        print(f"Stopped WanderingDigits animation for digit {self.number} and color {self.target_color[0:3]}")
        for digit in self.visited:
            digit['text_node'].setFg(self.clock.default_color)
            digit.pop('fader', None)
        self.visited = []
        super().cleanup()
    

    def fade(self):
        for digit in filter(lambda d: 'fader' in d, self.visited):
            try:
                next_color = next(digit['fader'])
                digit['text_node'].setFg(next_color)
            except StopIteration:
                digit.pop('fader', None)
                self.fading_counter -= 1


    def update(self):
        if not self.active:
            return False
        if (self.counter % self.update_interval) == 0:
            next = self.clock.get_nearest_digit(
                self.pos[0],
                self.pos[1],
                skip=lambda item: (self.number <= 9 and item['digit'] != self.number) or item in self.visited
            )
            if next is not None:
                next['fader'] = fade_color_to_and_back_again(BLACK, self.target_color, self.step * 2)
                self.visited.append(next)
                self.pos = (next['x'], next['y'])
                self.fading_counter += 1
        self.fade()
        self.counter += 1
        if self.fading_counter == 0:
            self.stop()
        return self.active


class Sweeper(Animation):
    """
    An example animation that sweeps across the display area, coloring digits. No fading.
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
    

    def cleanup(self):
        self.clock.color_all_digits(color=self.clock.default_color)
        super().cleanup()
        

    def update(self):
        if not self.active:
            return False
        sweep_x = self.x_start + (self.x_end - self.x_start) * ((self.position + 1.0) / 2.0)
        for digit in self.clock.placed_numbers:
            if digit['x'] <= sweep_x - self.width:
                digit['text_node'].setFg(self.clock.default_color)
            elif digit['x'] <= sweep_x:
                digit['text_node'].setFg(self.target_color)
        self.position += self.step
        if self.position > 1.0 + self.width:
            self.stop()
        return self.active


class Countdown(Animation):
    """
    An example animation that counts down from a 9 to 0
    """

    def __init__(self, clock, start_number=9, color=None):
        super().__init__(clock, exclusive=True)
        self.current_number = start_number
        if color is None:
            self.target_color = choice([clock.red, clock.green, clock.blue, clock.yellow, clock.cyan, clock.white])
        else:
            self.target_color = color
        self.hide_too = choice([True, True, False])
        if self.hide_too:
            self.step = 90
        else:
            self.step = randint(40,70)
    

    def start(self):
        super().start()
        self.counter = 0
    

    def cleanup(self):
        self.clock.color_all_digits(color=self.clock.default_color)
        super().cleanup()
    

    def update(self):
        if not self.active:
            return False
        if (self.counter % self.step) == 0:
            if self.current_number < 0:
                self.stop()
                return False
            for digit in self.clock.placed_numbers:
                if digit['digit'] == self.current_number:
                    digit['text_node'].setFg(self.target_color)
                elif self.hide_too and digit['digit'] > self.current_number:
                    digit['text_node'].setFg(self.clock.default_color)
            self.current_number -= 1
        self.counter += 1
        return self.active