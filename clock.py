# Clock class for displaying the current time
# load beamer.json and place the digits accordingly
    
import json
from datetime import datetime
import sys
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import OnscreenText  

class Clock(ShowBase):

    def __init__(self, config_file="beamer.json"):
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
        self.nearly_black = (0.01, 0.01, 0.01, 1)
        self.highlight_color = self.white
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
        self.accept("r", self.set_color, [self.red])
        self.accept("g", self.set_color, [self.green])
        self.accept("b", self.set_color, [self.blue])
        self.accept("y", self.set_color, [self.yellow])
        self.accept("w", self.set_color, [self.white])
        self.accept("i", self.show_all_digits)
        self.accept("q", sys.exit)
        self.accept("escape", sys.exit)

        self.taskMgr.add(self.display_time, "DisplayTimeTask")


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
    

    def set_color(self, color):
        self.highlight_color = color

    
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


    def display_time(self, task):
        now = datetime.now()
        current_time = now.strftime("%H%M%S")
        if current_time[0] == '0':
            current_time = current_time[1:]  # Remove leading zero for hour
        i = 0
        for item in self.placed_numbers:
            d = int(current_time[i]) if i < len(current_time) else -1
            if item['digit'] == d:
                item['text_node'].setFg(self.highlight_color)
                i += 1
            else:
                item['text_node'].setFg(self.default_color)            
        if i < len(current_time) and not self.warned[int(current_time[i])]:
            print(f"Warning: Not all digits could be displayed, missing configuration for digit {current_time[i]} at {now.strftime('%H:%M:%S')}")
            self.warned[int(current_time[i])] = True
        return Task.cont


if __name__ == "__main__":
    loadPrcFile("clock.prc")
    config_file = "beamer.json"
    if (len(sys.argv) > 1):
        config_file = sys.argv[1]
    app = Clock(config_file=config_file)
    app.run()

