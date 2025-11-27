# Clock class for displaying the current time
# load beamer.json and place the digits accordingly
    
import json
from datetime import datetime
import random
import sys
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import OnscreenText  

class Clock(ShowBase):

    def __init__(self, config_file="beamer.json", time=None):
        ShowBase.__init__(self)

        di = base.pipe.getDisplayInformation()
        print("Available display sizes:")
        for index in range(di.getTotalDisplayModes()):
            print(f"{di.getDisplayModeWidth(index)}x{di.getDisplayModeHeight(index)}")  

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
        # Storage for placed numbers
        self.placed_numbers = []  # [{digit, x, y, scale, text_node},..]
        self.placed_numbers = self.load_configuration(config_file)
        self.warned = [False for _ in range(10)]

        # Disable default mouse camera control
        self.disableMouse()
        
        # Setup orthographic camera for 2D
        self.camera.setPos(0, -10, 0)
        self.camera.lookAt(0, 0, 0)                
        
        # Setup background
        self.setBackgroundColor(0, 0, 0, 1)

        self.accept("f", self.toggle_fullscreen)
        self.accept("t", self.toggle_fullscreen)
        self.accept("space", self.toggle_fullscreen)
        self.accept("c", self.change_color)
        self.accept("i", self.show_all_digits)
        self.accept("q", sys.exit)
        self.accept("escape", sys.exit)

        print("=======================================================================")
        print("Clock initialized with configuration:", config_file)
        print("Press 'f', 't' or 'space' to toggle fullscreen.")
        print("Press 'c' to change highlight colors.")
        print("Press 'i' to toggle visibility of all digits.")
        print("Press 'q' or 'escape' to quit.")
        print("=======================================================================")

        self.set_color(self.white, self.green, self.red)

        if time:
            print(f"Displaying static time: {time}")
            self.display_time(time.replace(':',''))
        else: 
            self.taskMgr.add(self.display_time_task, "DisplayTimeTask")


    def load_configuration(self, config_file):
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            # todo: find a better sorting order for digits
            config.sort(key=lambda item: (item['x'], -item['y']))
            # Load each number from the config into an OnscreenText
            for item in config:
                # Create text node for the number (green, fixed)
                text_node = OnscreenText(
                    text="O" if item['digit'] == 0 else str(item['digit']),
                    pos=(item['x'], item['y']),
                    scale=item['scale'],
                    fg=(0.01, 0.01, 0.01, 1),  # black
                    align=TextNode.ACenter,
                    mayChange=True
                )
                item['text_node'] = text_node
            return config
        except FileNotFoundError:
            print(f"Configuration file '{config_file}' not found.")
        except json.JSONDecodeError:
            print("Error decoding JSON.")
        return []
    

    def set_color(self, *colors):
        if len(colors) == 1:
            self.highlight_color = [colors[0] for _ in range(6)]
        elif len(colors) == 3:
            self.highlight_color = [colors[0], colors[0], colors[1], colors[1], colors[2], colors[2]]


    def change_color(self):
        if self.highlight_color[0] == self.white:
            self.set_color(self.green, self.blue, self.red)
        elif self.highlight_color[0] == self.green:
            self.set_color(self.yellow, self.red, self.blue)
        elif self.highlight_color[0] == self.yellow:
            self.set_color(self.red, self.green, self.yellow)
        else:
            self.set_color(self.white, self.green, self.red)

    
    def show_all_digits(self):
        if self.default_color == self.white:
            self.default_color = self.nearly_black
        else:
            self.default_color = self.white


    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        fullscreen = self.win.getProperties().getFullscreen()
        wp = WindowProperties()
        wp.fullscreen = not fullscreen
        base.win.request_properties(wp)


    def display_time_task(self, task):
        self.display_time(datetime.now().strftime("%H%M%S"))
        return Task.cont


    def display_time(self, t):
        if not hasattr(self, 'last_time'):
            self.last_time = None
        if t == self.last_time:
            return
        self.last_time = t
        if len(t) == 5:
            t = '0' + t
        i = 1 if t[0:2] == '00' else 0
        lastDigits = []
        for item in self.placed_numbers:
            d = int(t[i]) if i < len(t) else -1
            item['text_node'].setFg(self.default_color)            
            if item['digit'] == d:
                if (i == len(t) - 1):
                    lastDigits.append(item)
                else:
                    item['text_node'].setFg(self.highlight_color[i])
                    i += 1
        if lastDigits:
            if len(lastDigits) > 1:
                random.shuffle(lastDigits)
            lastDigits[0]['text_node'].setFg(self.highlight_color[-1])
        elif i < len(t) and not self.warned[int(t[i])]:
            print(f"Warning: Not all digits could be displayed, missing configuration for digit {t[i]} at {t[:-4]}:{t[-4:-2]}:{t[-2:]}")
            self.warned[int(t[i])] = True


if __name__ == "__main__":
    loadPrcFile("clock.prc")
    config_file = "beamer.json"
    if (len(sys.argv) > 1 and sys.argv[1] != "-t"):
        config_file = sys.argv.pop(1)
    time = sys.argv[2] if (len(sys.argv) > 2 and sys.argv[1] == "-t") else None
    app = Clock(config_file=config_file, time=time)
    app.run()

