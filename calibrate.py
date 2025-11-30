# calibrate the beamer image:
# simple application to place digits at certain positions
# load and save the configuration to a json file
from base import ClockBase
import sys
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import OnscreenText  

SORT = lambda item: (item['x'], -item['y'])

class CalibrationApp(ClockBase):

    def __init__(self, config_file="beamer.json"):
        super().__init__(digit_color=(0, 1, 0, 1))

        self.spot_size = 0.3
        self.create_spot()
        self.current_text = None
        self.red = (1, 0, 0, 1)

        # Setup mouse and keyboard events
        # Task to update spot position based on mouse
        self.taskMgr.add(self.mouse_move, "mouse-move-task")

        self.accept("mouse1", lambda: self.fix_number() if self.current_text else self.change_number())
        self.accept("mouse3", self.remove_number)
        self.accept("wheel_up", self.resize, [0.01])
        self.accept("wheel_down", self.resize, [-0.01])

        self.accept("space", lambda: self.fix_number() if self.current_text else self.change_number())

        self.accept("shift-wheel_up", self.increase_number, [1])
        self.accept("shift-wheel_down", self.increase_number, [-1])
        self.accept("mouse2", lambda: self.increase_number(1))

        self.accept("arrow_up", self.keyboard_move, [0, 0.001])
        self.accept("arrow_up-repeat", self.keyboard_move, [0, 0.001])
        self.accept("arrow_down", self.keyboard_move, [0, -0.001])
        self.accept("arrow_down-repeat", self.keyboard_move, [0, -0.001])
        self.accept("arrow_right", self.keyboard_move, [0.001, 0])
        self.accept("arrow_right-repeat", self.keyboard_move, [0.001, 0])
        self.accept("arrow_left", self.keyboard_move, [-0.001, 0])
        self.accept("arrow_left-repeat", self.keyboard_move, [-0.001, 0])

        self.accept("shift-arrow_up", self.resize, [0.01])
        self.accept("shift-arrow_up-repeat", self.resize, [0.01])
        self.accept("shift-arrow_down", self.resize, [-0.01])
        self.accept("shift-arrow_down-repeat", self.resize, [-0.01])
        self.accept("shift-arrow_right", self.resize, [0.01])
        self.accept("shift-arrow_right-repeat", self.resize, [0.01])
        self.accept("shift-arrow_left", self.resize, [-0.01])
        self.accept("shift-arrow_left-repeat", self.resize, [-0.01])

        self.accept("v", self.roll_number, [-0.3])
        self.accept("v-repeat", self.roll_number, [-0.3])
        self.accept("shift-v", self.roll_number, [0.3])
        self.accept("shift-v-repeat", self.roll_number, [0.3])

        self.accept("h", self.rotate_number, [-0.01])
        self.accept("h-repeat", self.rotate_number, [-0.01])
        self.accept("shift-h", self.rotate_number, [0.01])
        self.accept("shift-h-repeat", self.rotate_number, [0.01])

        self.accept("q", self.quit_and_save)
        self.accept("s", self.save)
    
        # Accept number keys 0-9
        for i in range(10):
            self.accept(str(i), self.place_number, [i])
        
        self.add_help_text("Use mouse to move the spot, use mouse wheel to resize")
        self.add_help_text("Click to set digit, right click to remove digit")
        self.add_help_text("Use arrow keys to nudge the digit position")
        self.add_help_text("Use shift + mouse wheel to change between digits")
        self.add_help_text("Use shift + arrow keys to resize digit")
        self.add_help_text("Use (shift) h to rotate digit horizontaly")
        self.add_help_text("Use (shift) v to rotate digit vertically")
        self.add_help_text("Space = same as left mouse button")
        self.add_help_text("s = save configuration")
        self.add_help_text("q = quit (and save configuration)")
        print("=======================================================================")

        self.load_configuration(config_file=config_file)

    
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
                    distance = ((dx / radius) ** 2 + (dy / radius) ** 2) ** 0.5
                    alpha = max(0.0, min(1.0, .9 - distance)) ** 0.5
                    img.setAlpha(x, y, alpha)
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


    def get_mouse_pos_2d(self):
        """Get mouse position in 2D aspect2d coordinates"""
        if not self.mouseWatcherNode.hasMouse():
            return None
        mouse_pos = self.mouseWatcherNode.getMouse()
        # Convert to aspect2d coordinates
        aspect_ratio = self.getAspectRatio()
        x = mouse_pos.getX() * aspect_ratio
        y = mouse_pos.getY()
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
                fg=self.red,
                align=TextNode.ACenter,
                font=self.font,
                mayChange=True
            )


    def fix_number(self):
        """Fix the current number (turn it green)"""
        if self.current_text:
            # Change color to green
            self.current_text.setFg(self.digit_color)
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


    def numberAtMouse(self):
        tolerance = self.spot.getScale().getX() / 2
        x_center = self.spot.getX()
        y_center = self.spot.getZ() - tolerance
        return self.get_nearest_digit(x_center, y_center, tolerance=tolerance)


    def remove_number(self):
        """Remove number at current spot position"""
        if (self.current_text):
            self.current_text.removeNode()
        else:
            # Find if there's a fixed number near the spot position
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
            self.current_text.setFg(self.red)
            self.spot_size = item['xscale'] / 2            
            self.spot.setPos(item['x'], 0, item['y'])
            self.spot.setScale(self.spot_size)
        else:
            self.place_number(1)


    def quit_and_save(self):
        self.save()
        sys.exit()


    def keyboard_move(self, dx, dy):
        """Move spot position by delta"""
        if self.current_text:
            self.spot.hide()  # Hide spot while moving with keyboard
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
        self.spot.show()  # Ensure spot is visible when mouse is moved
        self.spot.setPos(mouse_pos.x, 0, mouse_pos.y)            
        # If current text exists, move it too
        if self.current_text:
            x, y = self.getNumberPosition()
            self.current_text.setPos(x, y)
        else:
            if hasattr(self, 'text_node_at_mouse') and self.text_node_at_mouse:
                self.text_node_at_mouse.setFg(self.digit_color)
            item = self.numberAtMouse()
            if item is not None:
                item['text_node'].setFg(self.red)
                self.text_node_at_mouse = item['text_node']
        return Task.cont
    

    def resize(self, delta):
        """Resize current number"""
        self.spot_size = max(0.04, self.spot_size + delta)
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

