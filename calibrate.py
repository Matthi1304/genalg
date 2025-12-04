# calibrate the beamer image:
# simple application to place digits at certain positions
# load and save the configuration to a json file
from base import ClockBase
import sys
from panda3d.core import *
from direct.task import Task


RED = (1, 0, 0, 1)
HIGHLIGHT_COLOR = (0.8, 1, 0, 1)

class CalibrationApp(ClockBase):

    def __init__(self, config_file="beamer.json"):
        super().__init__(digit_color=(0, 0, 1, 1))

        self.spot_size = 1.0
        self.create_spot()
        self.current_text = None

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

        self.accept("x", self.roll, ['x', -1])
        self.accept("x-repeat", self.roll, ['x', -1])
        self.accept("shift-x", self.roll, ['x', 1])
        self.accept("shift-x-repeat", self.roll, ['x', 1])
        self.accept("y", self.roll, ['y', -1])
        self.accept("y-repeat", self.roll, ['y', -1])
        self.accept("shift-y", self.roll, ['y', 1])
        self.accept("shift-y-repeat", self.roll, ['y', 1])
        self.accept("z", self.roll, ['z', -1])
        self.accept("z-repeat", self.roll, ['z', -1])
        self.accept("shift-z", self.roll, ['z', 1])
        self.accept("shift-z-repeat", self.roll, ['z', 1])
        self.accept("r", self.reset_roll)
        self.accept("v", self.toggle_spot_visibility)

        self.accept("c", self.change_digit_color)

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
        self.add_help_text("Use (shift) x/y/z to roll digit around respective axis")
        self.add_help_text("r = reset roll")
        self.add_help_text("Space = same as left mouse button")
        self.add_help_text("v = toggle spot visibility")
        self.add_help_text("c = change highlight colors")
        self.add_help_text("s = save configuration")
        self.add_help_text("q = quit (and save configuration)")
        print("=======================================================================")

        self.load_configuration(config_file=config_file)

    
    def create_spot(self):
        """Create a white circle spot"""
        # create a circular texture
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
        # place spot in scene
        cm = CardMaker("spot")
        cm.setHas3dUvs(True)
        cm.setFrame(-self.spot_size, self.spot_size, -self.spot_size, self.spot_size)
        self.spot = self.scene.attachNewNode(cm.generate())
        self.spot.setTexture(tex)
        self.spot.setTransparency(TransparencyAttrib.MAlpha)
        self.spot.hide()
        self.spot_visible = False


    def change_digit_color(self):
        colors = [
            (0, 0, 1, 1),
            (0, 1, 0, 1),
            (1, 1, 0, 1),
            (0, 0, 0, 0)
        ]
        next_index = (colors.index(self.digit_color) + 1) % len(colors)
        self.set_digit_color(colors[next_index])
        self.mouse_move(None, force=True)  # Update highlight


    def get_mouse_pos_2d(self):
        """Get mouse position in 2D aspect2d coordinates"""
        if not self.mouseWatcherNode.hasMouse():
            return None
        mouse_pos = self.mouseWatcherNode.getMouse()
        # Convert to aspect2d coordinates
        aspect_ratio = self.getAspectRatio()
        x = mouse_pos.getX() # * aspect_ratio
        y = mouse_pos.getY()
        x, y = self.screen_to_world(x, y)
        return Point2(x, y)


    def increase_number(self, delta):
        """Increase or decrease the current number"""
        if self.current_text:
            digit = self.current_text.text
            digit = int(digit)
            digit = (digit + delta) % 10
            text = str(digit)
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
            self.current_text = self.create_text_node({
                'digit': int(text),
                'x': self.spot.getX(),
                'y': self.spot.getZ() - self.spot_size/2,
                'scale': self.spot_size * 2,
            })
            self.placed_numbers.append(self.current_text.data)
            self.current_text.setFg(RED)


    def fix_number(self):
        """Fix the current number (turn it green)"""
        if self.current_text:
            # Change color to green
            self.current_text.setFg(self.digit_color)
            self.current_text = None


    def getNumberPosition(self):
        return (self.spot.getX(), self.spot.getZ() - self.spot_size/2)


    def numberAtMouse(self):
        tolerance = self.spot.getScale().getX() / 2
        x_center = self.spot.getX()
        y_center = self.spot.getZ() - tolerance
        return self.get_nearest_digit(x_center, y_center, tolerance=tolerance)


    def grab_text_node(self):
        if not self.current_text:
            d = self.numberAtMouse()
            if d:
                self.current_text = d['text_node']
                self.current_text.setFg(RED)
        if self.current_text:
            return self.current_text


    def remove_number(self):
        """Remove number at current spot position"""
        item = self.grab_text_node()
        if item:
            item.removeNode()
            self.placed_numbers.remove(item.data)
            self.current_text = None


    def change_number(self):
        """Change/edit the number at current spot position"""
        if self.current_text:
            return  # Already editing a number
        item = self.grab_text_node()
        if item is None:
            self.place_number(1)
        else:
            self.spot_size = item.scale / 2
            self.spot.setScale(self.spot_size)


    def quit_and_save(self):
        self.save()
        sys.exit()


    def keyboard_move(self, dx, dy):
        """Move spot position by delta"""
        text = self.grab_text_node()
        if text:
            self.spot.hide()  # Hide spot while working with keyboard
            x, y = self.current_text.getPos()
            text.setPos(x + dx, y + dy)


    def toggle_spot_visibility(self):
        """Toggle the visibility of the spot"""
        self.spot_visible = not self.spot_visible
        if self.spot_visible:
            self.spot.show()
        else:
            self.spot.hide()


    def mouse_move(self, task, force=False):
        """Update task for mouse movement"""
        mouse_pos = self.get_mouse_pos_2d()
        if mouse_pos is None:
            return Task.cont
        if not force and (mouse_pos.x == self.spot.getX() and mouse_pos.y == self.spot.getZ()):
            # no mouse movement
            return Task.cont
        if self.spot_visible:
            self.spot.show() # show during mouse move
        self.spot.setPos(mouse_pos.x, 0.01, mouse_pos.y)            
        # If current text exists, move it too
        if self.current_text:
            self.current_text.setPos(mouse_pos.x, mouse_pos.y)
        else:
            if hasattr(self, 'highlight') and self.highlight:
                self.highlight['text_node'].setFg(self.digit_color)
            self.highlight = self.numberAtMouse()
            if self.highlight is not None:
                self.highlight['text_node'].setFg(HIGHLIGHT_COLOR)
        return Task.cont
    

    def resize(self, delta):
        """Resize current number"""
        self.spot_size = max(0.04, self.spot_size + delta)
        self.spot.setScale(self.spot_size)
        item = self.current_text
        if item:
            self.spot.hide()  # Hide spot while working with keyboard
            item.setScale(self.spot_size * 2)
    

    def roll(self, axis, delta):
        """Roll the given text node around the given axis by delta"""
        text = self.grab_text_node()
        if text is None:
            return
        self.spot.hide()  # Hide spot while working with keyboard
        hpr = list(text.getHpr())
        "__z"
        axis_index = "yxz".index(axis)
        value = hpr[axis_index] + delta
        if -80 < value < 80:
            hpr[axis_index] = value
            text.setHpr(hpr[0], hpr[1], hpr[2])
    

    def reset_roll(self):
        """Reset roll of the current text node"""
        text = self.current_text
        if text:
            text.setHpr(0, 0, 0)


if __name__ == "__main__":
    loadPrcFile("clock.prc")
    config_file = "beamer.json"
    if (len(sys.argv) > 1):
        config_file = sys.argv[1]
    app = CalibrationApp(config_file=config_file)
    app.run()

