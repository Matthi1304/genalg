# calibrate the beamer image:
# simple application showing a black image with a white circle in the center
# the circle can be moved with the mouse and the size can be changed while holding the left mouse button
# and dragging the mouse up and down or left and right
# when pressing any number key 0-9 this number is placed in the center of the circle in red color
# the number with the spot can then be moved around and scaled as well
# when pressing s the number is drawn in green color and the position of the number is then fixed
# the white spot can then be moved around again to place the next number
# pressing r removes the number at the current spot position
# pressing c lets the user change the current number and re-enables moving and scaling
# of the number at the spot position
# pressing space changes the background color from black to white and vice versa
# pressing q quits the application and saves the configuration to a json file
# this way the beamer can be calibrated to fit the hour plate

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
        self.spot_pos = Point2(0, 0)
        self.spot_size = 0.3
        self.dragging = False
        self.last_mouse_pos = None
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
        self.accept("mouse1", self.on_mouse_down)
        self.accept("mouse1-up", self.on_mouse_up)
        self.accept("s", self.fix_number)
        self.accept("r", self.remove_number)
        self.accept("c", self.change_number)
        self.accept("q", self.quit_and_save)
        self.accept("w", self.save)
        self.accept("f", self.toggle_fullscreen)
        self.accept("i", self.print_stats)
        self.accept("a", self.toggle_animation)
        self.accept("h", self.toggle_help)
        self.accept("escape", sys.exit)

        # Accept number keys 0-9
        for i in range(10):
            self.accept(str(i), self.place_number, [i])
        
        print("=======================================================================")        
        self.onScreenText(f"Config: {self.config_file}")
        self.onScreenText("Use mouse to move the spot, press and hold left mouse button to resize.")
        self.onScreenText("h = hide/show this help")
        self.onScreenText("0-9 = place digit")
        self.onScreenText("f = toggle fullscreen")
        self.onScreenText("s = fix digit")
        self.onScreenText("r = remove digit")
        self.onScreenText("c = change digit")
        self.onScreenText("i = print statistics")
        self.onScreenText("a = start/stop clock animation")
        self.onScreenText("w = save configuration")
        self.onScreenText("q = save and quit")
        self.onScreenText("escape = quit without saving")
        print("=======================================================================", 11)

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
        self.spot.setPos(self.spot_pos.x, 0, self.spot_pos.y)


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


    def on_mouse_down(self):
        """Handle mouse button down"""
        self.dragging = True
        self.last_mouse_pos = self.get_mouse_pos_2d()


    def on_mouse_up(self):
        """Handle mouse button up"""
        self.dragging = False
        self.last_mouse_pos = None


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
                'scale': self.current_text.getScale()[0],
                'text_node': self.current_text
            })
            
            # Clear current text reference
            self.current_text = None


    def getNumberPosition(self):
        return (self.spot_pos.x, self.spot_pos.y - self.spot_size/2)


    def numberAtMouse(self, tolerance=1):
        item = None        
        for data in self.placed_numbers:
            x = data['x']
            y = data['y']
            dist = ((x - self.spot_pos.x)**2 + 
                   (y - self.spot_pos.y)**2)**0.5
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

        # Find if there's a fixed number near the spot position
        item = self.numberAtMouse()
        
        if item is not None:
            # Remove from placed numbers and make it current
            item['text_node'].removeNode()
            self.placed_numbers.remove(item)
            
            # Recreate as current (red) number
            self.spot_pos = Point2(item['x'], item['y'])
            self.spot_size = item['scale'] / 2
            
            self.spot.setPos(self.spot_pos.x, 0, self.spot_pos.y)
            self.spot.setScale(self.spot_size)

            self.current_text = OnscreenText(
                text=str(item['digit']),
                pos=self.getNumberPosition(),
                scale=item['scale'],
                fg=(1, 0, 0, 1),  # Red color
                align=TextNode.ACenter,
                font=self.font,
                mayChange=True
            )


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
                text_node = OnscreenText(
                    text="O" if item['digit'] == 0 else str(item['digit']),
                    pos=(item['x'], item['y']),
                    scale=item['scale'],
                    fg=(0, 1, 0, 1),  # Green color (fixed)
                    align=TextNode.ACenter,
                    font=self.font,
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
        # wee need 6 times the digits 1 and 2 (11:11:11 to 22:22:22)
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
        warned = [False for _ in range(10)]
        for i in range(86400):
            self.check_time(
                i,
                warned,
                callbackMatch = lambda d: None,
                callbackMiss  = lambda d: None,
                callbackWarn  = lambda i, time: print(f"   Missing digit {i} for time {time}")
            )
        print("=======================================================================")
    

    def check_time(self, total_seconds, warned, callbackMatch=None, callbackMiss=None, callbackWarn=None):
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        current_time = f"{hours:02d}{minutes:02d}{seconds:02d}"
        i = 1 if current_time[0:2] == '00' else 0
        for item in self.placed_numbers:
            d = int(current_time[i]) if i < len(current_time) else -1
            if item['digit'] == d:
                callbackMatch(item)
                i += 1
            else:
                callbackMiss(item)                
        if i < len(current_time) and not warned[int(current_time[i])]:
            digit = int(current_time[i])
            warned[digit] = True
            callbackWarn(digit, current_time[0:2] + ':' + current_time[2:4] + ':' + current_time[4:6])


    def simulate_time(self, task):
        # format self.displaySeconds into HH:MM:SS
        self.check_time(
            int(task.time * 10) % 86400,
            self.warned,
            callbackMatch = lambda d: d['text_node'].setFg((1, 1, 1, 1)),  # white
            callbackMiss  = lambda d: d['text_node'].setFg((0, 1, 0, 1)),  # green
            callbackWarn  = lambda i, time: print(f"Warning: Not all digits could be displayed, missing configuration for digit {i} at {time}")
        )
        return Task.cont


    def toggle_animation(self):
        """Toggle animation of the clock"""
        if self.taskMgr.hasTaskNamed("DisplayTimeTask"):
            task = self.taskMgr.remove("DisplayTimeTask")
            for item in self.placed_numbers:
                item['text_node'].setFg((0, 1, 0, 1))  # green
        else:
            print("=======================================================================")
            print("Starting time simulation animation.")
            self.warned = [False for _ in range(10)]
            self.taskMgr.add(self.simulate_time, "DisplayTimeTask")


    def save(self):
        """Save configuration to JSON and quit"""
        config = []
        
        for item in self.placed_numbers:
            config.append({
                'digit': item['digit'],
                'x': item['x'],
                'y': item['y'],
                'scale': item['scale']
            })
        
        config.sort(key=SORT)

        # Save to JSON file
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Configuration saved to {self.config_file}")


    def mouse_move(self, task):
        """Update task for mouse movement"""
        mouse_pos = self.get_mouse_pos_2d()
        
        if mouse_pos is None:
            return Task.cont
        
        if self.dragging and self.last_mouse_pos:
            # Calculate mouse movement
            delta = mouse_pos - self.last_mouse_pos            
            # Scale based on vertical movement
            if abs(delta.y) > 0.001:
                self.spot_size = max(0.05, self.spot_size + delta.y * 0.5)
                self.spot.setScale(self.spot_size)                
            if self.current_text:
                self.current_text.setScale(self.spot_size * 2)
        elif not self.dragging:
            # Just follow mouse when not dragging
            self.spot_pos = mouse_pos
            self.spot.setPos(self.spot_pos.x, 0, self.spot_pos.y)            
            # If current text exists, move it too
            if self.current_text:
                x, y = self.getNumberPosition()
                self.current_text.setPos(x, y)
        
        self.last_mouse_pos = mouse_pos
        return Task.cont


if __name__ == "__main__":
    loadPrcFile("clock.prc")
    config_file = "beamer.json"
    if (len(sys.argv) > 1):
        config_file = sys.argv[1]
    app = CalibrationApp(config_file=config_file)
    app.run()

