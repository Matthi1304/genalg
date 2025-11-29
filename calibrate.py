# calibrate the beamer image:
# simple application to place digits at certain positions
# load and save the configuration to a json file
from logging import config
import os
import sys
import json
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import OnscreenText  
from direct.interval.LerpInterval import LerpHprInterval

SORT = lambda item: (item['x'], -item['y'])

class CalibrationApp(ShowBase):

    def __init__(self, config_file="beamer.json"):
        ShowBase.__init__(self)

        self.font = None
        if os.path.exists("Epoch-BF6881cf42e6637.otf"):
            self.font = loader.loadFont('Epoch-BF6881cf42e6637.otf')
    
        self.config_file = config_file
        # State variables
        self.spot_size = 0.3
        self.shiftDown = False
        # Storage for placed numbers
        self.placed_numbers = []  # [{digit, x, y, scale, text_node},..]
        # Current number text
        self.current_text = None
                
        # Disable default mouse camera control
        self.disableMouse()
        
        # Setup orthographic camera for 2D
        self.camera.setPos(0, -10, 0)
        self.camera.lookAt(0, 0, 0)                
        
        # Create white circle spot
        self.create_spot()
        
        # Setup background
        self.setBackgroundColor(0, 0, 0, 1)
        
        # Load existing configuration if available
        self.load_configuration()

        
        # Setup mouse and keyboard events
        self.accept("mouse1", lambda: self.fix_number() if self.current_text else self.change_number())
        self.accept("mouse3", self.remove_number)
        self.accept("wheel_up", self.resize, [0.01])
        self.accept("wheel_down", self.resize, [-0.01])

        self.accept("space", lambda: self.fix_number() if self.current_text else self.change_number())

        self.accept("shift-wheel_up", self.increase_number, [1])
        self.accept("shift-wheel_down", self.increase_number, [-1])

        self.accept("arrow_up", self.move, [0, 0.001])
        self.accept("arrow_up-repeat", self.move, [0, 0.001])
        self.accept("arrow_down", self.move, [0, -0.001])
        self.accept("arrow_down-repeat", self.move, [0, -0.001])
        self.accept("arrow_right", self.move, [0.001, 0])
        self.accept("arrow_right-repeat", self.move, [0.001, 0])
        self.accept("arrow_left", self.move, [-0.001, 0])
        self.accept("arrow_left-repeat", self.move, [-0.001, 0])

        self.accept("shift-arrow_up", self.resize, [0.01])
        self.accept("shift-arrow_up-repeat", self.resize, [0.01])
        self.accept("shift-arrow_down", self.resize, [-0.01])
        self.accept("shift-arrow_down-repeat", self.resize, [-0.01])
        self.accept("shift-arrow_right", self.resize, [0.01])
        self.accept("shift-arrow_right-repeat", self.resize, [0.01])
        self.accept("shift-arrow_left", self.resize, [-0.01])
        self.accept("shift-arrow_left-repeat", self.resize, [-0.01])

        self.accept("control-arrow_left", self.roll_number, [-0.1])
        self.accept("control-arrow_left-repeat", self.roll_number, [-0.1])
        self.accept("control-arrow_right", self.roll_number, [0.1])
        self.accept("control-arrow_right-repeat", self.roll_number, [0.1])

        self.accept("shift-control-arrow_left", self.rotate_number, [-0.01])
        self.accept("shift-control-arrow_left-repeat", self.rotate_number, [-0.01])
        self.accept("shift-control-arrow_right", self.rotate_number, [0.01])
        self.accept("shift-control-arrow_right-repeat", self.rotate_number, [0.01])

        self.accept("q", self.quit_and_save)
        self.accept("s", self.save)
        self.accept("f", self.toggle_fullscreen)
        self.accept("i", self.print_stats)
        self.accept("h", self.toggle_help)
        self.accept("escape", sys.exit)

        # Accept number keys 0-9
        for i in range(10):
            self.accept(str(i), self.place_number, [i])
        
        print("=======================================================================")        
        self.onScreenText(f"Config: {self.config_file}")
        self.onScreenText("Use mouse to move the spot, use mouse wheel to resize.")
        self.onScreenText("Click to set digit, right click to remove digit.")
        self.onScreenText("Use arrow keys to nudge the digit position.")
        self.onScreenText("Use shift + mouse wheel to change between digits.")
        self.onScreenText("Use shift + arrow keys to resize digit.")
        self.onScreenText("Use ctrl + arrow left/right to rotate digit (ctrl + shift for vertical rotation).")
        self.onScreenText("Space to fix/unfix digit.")
        self.onScreenText("h = hide/show this help")
        self.onScreenText("f = toggle fullscreen")
        self.onScreenText("i = print statistics")
        self.onScreenText("s = save configuration")
        self.onScreenText("q = quit (and save configuration)")
        self.onScreenText("escape = quit without saving")
        print("=======================================================================")

        # Create on screen text for xy position
        self.xyText = self.onScreenText("0.00:0.00")

        # Task to update spot position based on mouse
        self.taskMgr.add(self.mouse_move, "UpdateTask")


    
    def onScreenText(self, text):
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
    

    def create_spot(self):
        """Create a white circle spot"""
        # Create a circular texture
        size = 128
        img = PNMImage(size, size, 4)
        center = size // 2
        radius = size // 2 - 2
        for y in range(size):
            for x in range(size):
                dx = x - center
                dy = y - center
                dist = (dx*dx + dy*dy) ** 0.5
                if dist <= radius:
                    img.setXel(x, y, 1, 1, 1)
                    img.setAlpha(x, y, 1)
                else:
                    img.setAlpha(x, y, 0)
        tex = Texture()
        tex.load(img)
        # Create card for the spot
        cm = CardMaker("spot")
        cm.setFrame(-1, 1, -1, 1)
        self.spot = self.aspect2d.attachNewNode(cm.generate())
        self.spot.setTexture(tex)
        self.spot.setTransparency(TransparencyAttrib.MAlpha)
        self.spot.setScale(self.spot_size)
        self.spot.setPos(0, 0, 0)


    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        fullscreen = self.win.getProperties().getFullscreen()
        wp = WindowProperties()
        wp.fullscreen = not fullscreen
        base.win.request_properties(wp)


    def get_mouse_pos_2d(self):
        """Get mouse position in 2D aspect2d coordinates"""
        if not self.mouseWatcherNode.hasMouse():
            return None
        mouse_pos = self.mouseWatcherNode.getMouse()
        # Convert to aspect2d coordinates
        aspect_ratio = self.getAspectRatio()
        x = mouse_pos.getX() * aspect_ratio
        y = mouse_pos.getY()
        self.xyText.text = f"{x:5.2f}:{y:5.2f}"
        return Point2(x, y)


    def increase_number(self, delta):
        """Increase or decrease the current number"""
        if self.current_text:
            digit = self.current_text.text
            digit = 0 if digit == 'O' else int(digit)
            digit = (digit + delta) % 10
            text = 'O' if digit == 0 else str(digit)
            self.current_text.text = text
        elif delta > 0:
            self.place_number(1)
        else:
            self.place_number(9)


    def place_number(self, digit):
        """Place a number at the current spot position"""
        text = 'O' if digit == 0 else str(digit)
        if self.current_text:
            self.current_text.text = text
        else:
            self.current_text = OnscreenText(
                text = text,
                pos=self.getNumberPosition(),
                scale=self.spot_size * 2,
                fg=(1, 0, 0, 1),  # Red color
                align=TextNode.ACenter,
                font=self.font,
                mayChange=True
            )


    def fix_number(self):
        """Fix the current number (turn it green)"""
        if self.current_text:
            # Change color to green
            self.current_text.setFg((0, 1, 0, 1))
            digit = self.current_text.text
            digit = 0 if digit == 'O' else int(digit)
            self.placed_numbers.append({
                'digit': int(digit),
                'x': self.current_text.getPos()[0],
                'y': self.current_text.getPos()[1],
                'xscale': self.current_text.getScale()[0],
                'yscale': self.current_text.getScale()[1],
                'roll': self.current_text.getRoll(),
                'text_node': self.current_text
            })
            self.current_text = None


    def getNumberPosition(self):
        return (self.spot.getX(), self.spot.getZ() - self.spot_size/2)


    def numberAtMouse(self, tolerance=1):
        item = None        
        for data in self.placed_numbers:
            x = data['x']
            y = data['y']
            dist = ((x - self.spot.getX())**2 + 
                   (y - self.spot.getZ())**2)**0.5
            if dist < tolerance:
                item = data
                tolerance = dist  # Update tolerance to closest
        return item


    def remove_number(self):
        """Remove number at current spot position"""
        # Find if there's a fixed number near the spot position
        if (self.current_text):
            self.current_text.removeNode()
        else:
            item = self.numberAtMouse()
            if item is not None:
                self.placed_numbers.remove(item)
                item['text_node'].removeNode()


    def change_number(self):
        """Change/edit the number at current spot position"""
        if self.current_text:
            return  # Already editing a number
        item = self.numberAtMouse()
        if item is not None:
            self.current_text = item['text_node']
            self.placed_numbers.remove(item)
            self.current_text.setFg((1, 0, 0, 1))
            # Recreate as current (red) number
            self.spot_size = item['xscale'] / 2            
            self.spot.setPos(item['x'], 0, item['y'])
            self.spot.setScale(self.spot_size)


    def quit_and_save(self):
        self.save()
        sys.exit()


    def load_configuration(self):
        """Load configuration from JSON file if it exists"""
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
                    fg=(0, 1, 0, 1),  # Green color (fixed)
                    align=TextNode.ACenter,
                    font=self.font,
                    roll=item['roll'],
                    mayChange=True
                )
                item['text_node'] = text_node
            print(f"Loaded {len(config)} numbers from calibration.json")
        except FileNotFoundError:
            print("No existing calibration.json found, starting fresh")
        except json.JSONDecodeError:
            print("Error reading calibration.json, starting fresh")


    def print_stats(self):
        """Print statistics of placed numbers"""
        print("Available display sizes:")
        di = base.pipe.getDisplayInformation()
        for index in range(di.getTotalDisplayModes()):
            print(f"{di.getDisplayModeWidth(index)}x{di.getDisplayModeHeight(index)}")  
        self.placed_numbers.sort(key=SORT)
        digit_counters = [0 for _ in range(10)]
        for item in self.placed_numbers:
            digit_counters[item['digit']] += 1
        # we need 5 times the digit 0 (0:00:00)
        # wee need 6 times the digits 1 and 2 (11:11:11, 22:22:22)
        # we need 5 times the digits 3, 4, 5 (3:33:33, 4:44:44, 5:55:55)
        # we need 4 times the digits 6, 7, 8, 9 (e.g. 6:16:36, 9:19:59)
        amounts_needed = [5, 6, 6, 5, 5, 5, 4, 4, 4, 4]
        print("=======================================================================")
        print("Placed number statistics:")
        print(f"   Total placements: {len(self.placed_numbers)} (minimum number of numbers needed: {sum(amounts_needed)})")
        for i, count in enumerate(digit_counters):
            if (count < amounts_needed[i]):
                print(f"   digit {i}: {count:2d}, min={amounts_needed[i]}) *** MISSING: {amounts_needed[i] - count} ***")
            else:
                print(f"   digit {i}: {count:2d}, min={amounts_needed[i]}")
        print("=======================================================================")
    

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


    def move(self, dx, dy):
        """Move spot position by delta"""
        if self.current_text:
            x, y = self.current_text.getPos()
            self.current_text.setPos(x + dx, y + dy)


    def mouse_move(self, task):
        """Update task for mouse movement"""
        mouse_pos = self.get_mouse_pos_2d()
        if mouse_pos is None:
            return Task.cont
        if (mouse_pos.x == self.spot.getX() and mouse_pos.y == self.spot.getZ()):
            # no mouse movement
            return Task.cont
        self.spot.setPos(mouse_pos.x, 0, mouse_pos.y)            
        # If current text exists, move it too
        if self.current_text:
            x, y = self.getNumberPosition()
            self.current_text.setPos(x, y)        
        return Task.cont
    

    def resize(self, delta):
        """Resize current number"""
        self.spot_size = max(0.05, self.spot_size + delta)
        self.spot.setScale(self.spot_size)
        if self.current_text:
            self.current_text.setScale(self.spot_size * 2)
    

    def roll_number(self, delta):
        """Rotate current number"""
        if self.current_text:
            self.current_text.setTextR(self.current_text.getTextR() + delta)


    def rotate_number(self, delta):
        """Tilt current number"""
        if self.current_text:
            scale = self.current_text.getTextScale()
            if delta < 0 and (scale[0] < 0.01):
                return
            if delta > 0 and (scale[0] > scale[1]):
                delta = -delta
            self.current_text.setTextScale((scale[0] + delta, scale[1]))


if __name__ == "__main__":
    loadPrcFile("clock.prc")
    config_file = "beamer.json"
    if (len(sys.argv) > 1):
        config_file = sys.argv[1]
    app = CalibrationApp(config_file=config_file)
    app.run()

