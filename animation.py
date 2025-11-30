from random import choice

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
    

class WanderingDigits(Animation):
    """
    An example animation that makes digits wander around randomly.
    """

    def __init__(self, clock, number=None, color=None):
        super().__init__(clock, exclusive=True)
        self.number = number if number is not None else choice(range(10))
        if color is None:
            self.target_color = choice([clock.red, clock.green, clock.blue, clock.yellow])
        else:
            self.target_color = color
        self.step = 0.005
        self.update_interval = int(1 / (2 * self.step))
    

    def start(self):
        super().start()
        print(f"Starting WanderingDigits animation for digit {self.number} and color {self.target_color[0:3]}")
        self.counter = 0
        x1, y1, x2, y2 = self.clock.get_display_area()
        self.pos = (choice((x1, x2)), choice((y1, y2)))
        self.to_fade_in = []
        self.to_fade_out = []
        self.visited = []
    

    def cleanup(self):
        print(f"Stopped WanderingDigits animation for digit {self.number} and color {self.target_color[0:3]}")
        for digit in self.to_fade_in + self.to_fade_out:
            digit['text_node'].setFg(self.clock.default_color)
        self.to_fade_in = []
        self.to_fade_out = []
        self.visited = []
        super().cleanup()
    

    def fade_in(self):
        tr, tg, tb, _ = self.target_color
        for digit in self.to_fade_in.copy():
            r, g, b, _ = digit['text_node'].fg
            if (r < tr):
                r = min(r + self.step, tr)
            if (g < tg):
                g = min(g + self.step, tg)
            if (b < tb):
                b = min(b + self.step, tb)
            digit['text_node'].setFg((r, g, b, 1))
            if (r == tr) and (g == tg) and (b == tb):
                self.to_fade_in.remove(digit)
                self.to_fade_out.append(digit)


    def fade_out(self):
        for digit in self.to_fade_out.copy():
            r, g, b, _ = digit['text_node'].fg
            if (r > 0):
                r = max(r - self.step, 0)
            if (g > 0):
                g = max(g - self.step, 0)
            if (b > 0):
                b = max(b - self.step, 0)
            if (r == 0) and (g == 0) and (b == 0):
                self.to_fade_out.remove(digit)
            digit['text_node'].setFg((r, g, b, 1))


    def update(self):
        if not self.active:
            return False
        if (self.counter % self.update_interval) == 0:
            next = self.clock.get_nearest_digit(
                self.pos[0],
                self.pos[1],
                skip=lambda item:  item['digit'] != self.number or item in self.visited
            )
            if next is not None:
                next['text_node'].setFg((0, 0, 0, 1))  # start with black
                self.to_fade_in.append(next)
                self.visited.append(next)
                self.pos = (next['x'], next['y'])
        self.fade_in()
        self.fade_out()
        self.counter += 1
        if (not self.to_fade_in) and (not self.to_fade_out):
            self.stop()
        return self.active