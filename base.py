import os
import sys
import json
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import OnscreenText

class ClockBase(ShowBase):

    def __init__(self, config_file=None, digit_color=(0,1,0,1)):
        super().__init__()
        self.config_file = config_file
        self.placed_numbers = []  # [{digit, x, y, scale, text_node},..]
        self.set_digit_color(digit_color)
        self.font = None
        if os.path.exists("Epoch-BF6881cf42e6637.otf"):
            self.font = loader.loadFont('Epoch-BF6881cf42e6637.otf')
        # Disable default mouse camera control
        self.disableMouse()        
        # Setup orthographic camera for 2D
        self.camera.setPos(0, -10, 0)
        self.camera.lookAt(0, 0, 0)

        self.setBackgroundColor(0, 0, 0, 1)

        if config_file is not None:
            self.load_configuration(self.config_file)

        self.accept("h", self.toggle_help)
        self.accept("escape", sys.exit)
        self.accept("i", self.print_stats)
        self.accept("f11", self.toggle_fullscreen)
        self.accept("f", self.toggle_fullscreen)

        print("=======================================================================")        
        self.add_help_text(f"Config: {self.config_file}")
        self.add_help_text("h = hide/show this help")
        self.add_help_text("escape = quit program")
        self.add_help_text("i = print statistics")
        self.add_help_text("F11 / f = toggle fullscreen")



    def set_digit_color(self, color):
        """Set the color for the digits"""
        self.digit_color = color
        for item in self.placed_numbers:
            item['text_node'].setFg(color)


    def load_configuration(self, config_file="beamer.json"):        
        """Load configuration from JSON file if it exists"""
        print(f"Loading configuration from {config_file}")
        self.config_file = config_file
        if hasattr(self, 'helpTexts'):
            self.helpTexts[0].setText(f"Config: {config_file}")
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            self.placed_numbers = config
            # Load each number from the config
            for item in config:
                # Create text node for the number (green, fixed)
                # 'xscale': self.current_text.getScale()[0],
                # 'yscale': self.current_text.getScale()[1],
                # 'roll': self.current_text.getTextR(),
                if item.get('scale', None) is not None:
                    legacy_scale = item.get('scale')
                    item['xscale'] = legacy_scale
                    item['yscale'] = legacy_scale
                    item['roll'] = 0
                text_node = OnscreenText(
                    text="O" if item['digit'] == 0 else str(item['digit']),
                    pos=(item['x'], item['y']),
                    scale=(item['xscale'], item['yscale']),
                    fg=self.digit_color,
                    align=TextNode.ACenter,
                    font=self.font,
                    roll=item['roll'],
                    mayChange=True
                )
                item['text_node'] = text_node
            print(f"Loaded {len(config)} numbers from {config_file}")
        except FileNotFoundError:
            print(f"{config_file} not found")
        except json.JSONDecodeError as e:
            print(f"{config_file} contains invalid JSON: {e.msg}")


    def save(self):
        """Save configuration to JSON and quit"""
        config = []
        for item in self.placed_numbers:
            data = item.copy()
            # Remove text_node before saving
            del data['text_node']
            config.append(data)
        # Save to JSON file
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Configuration saved to {self.config_file}")


    def add_help_text(self, text):
        print(text)
        if not hasattr(self, 'helpTexts'):
            self.helpTexts = []
        self.helpTexts.append(
            OnscreenText(
                text=text,
                pos=(-1.3, len(self.helpTexts) * -0.06 + 0.95),
                scale=0.05,
                fg=(0.7, 0.7, 0.7, 1),
                align=TextNode.ALeft,
                mayChange=True
            )
        )
        return self.helpTexts[-1]


    def toggle_help(self):
        """Toggle help text visibility"""
        if not hasattr(self, 'helpTexts'):
            return
        for text in self.helpTexts:
            if text.isHidden():
                text.show()
            else:
                text.hide()


    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        fullscreen = self.win.getProperties().getFullscreen()
        wp = WindowProperties()
        wp.fullscreen = not fullscreen
        base.win.request_properties(wp)


    def get_display_area(self):
        """Get the display area covered by placed numbers: (min_x, min_y, max_x, max_y)"""
        if not self.placed_numbers:
            return (0, 0, 0, 0)
        min_x = min(item['x'] for item in self.placed_numbers)
        max_x = max(item['x'] for item in self.placed_numbers)
        min_y = min(item['y'] for item in self.placed_numbers)
        max_y = max(item['y'] for item in self.placed_numbers)
        return (min_x, min_y, max_x, max_y)
    

    def print_stats(self):
        """Print statistics of placed numbers"""
        if not self.placed_numbers:
            print("No numbers placed yet")
            return
        if False:
            print("Available display sizes:")
            di = base.pipe.getDisplayInformation()
            for index in range(di.getTotalDisplayModes()):
                print(f"{di.getDisplayModeWidth(index)}x{di.getDisplayModeHeight(index)}")  
        self.placed_numbers.sort(key=lambda item: (item['x'], item['y']))
        digit_counters = [0 for _ in range(10)]
        for item in self.placed_numbers:
            digit_counters[item['digit']] += 1
        # we need 5 times the digit 0 (0:00:00)
        # wee need 6 times the digits 1 and 2 (11:11:11, 22:22:22)
        # we need 5 times the digits 3, 4, 5 (3:33:33, 4:44:44, 5:55:55)
        # we need 3 times the digits 6, 7, 8, 9 (e.g. 6:16:36, 9:19:59)
        amounts_needed = [5, 6, 6, 5, 5, 5, 3, 3, 3, 3]
        print("=======================================================================")
        print("Placed number statistics:")
        print(f"   Total placements: {len(self.placed_numbers)} (minimum number of numbers needed: {sum(amounts_needed)})")
        for i, count in enumerate(digit_counters):
            if (count < amounts_needed[i]):
                print(f"   digit {i}: {count:2d}, min={amounts_needed[i]} *** MISSING: {amounts_needed[i] - count} ***")
            else:
                print(f"   digit {i}: {count:2d}, min={amounts_needed[i]}")
        print("=======================================================================")
    

    def get_nearest_digit(self, x, y, tolerance=float('inf'), skip = None):
        """Get the nearest digit to the given (x, y) position"""
        if not self.placed_numbers:
            return None
        digit = None
        for item in self.placed_numbers:
            if skip and skip(item):
                continue
            dx = item['x'] - x
            dy = item['y'] - y
            dist = ((dx * dx) + (dy * dy)) ** 0.5
            if dist < tolerance:
                digit = item
                tolerance = dist
        return digit
