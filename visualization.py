#!/usr/bin/env python3

import sys
import json
from panda3d.core import *
from direct.gui.DirectGui import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.task import Task

SIZE_SCALE = 1000.0

# Macro-like function used to reduce the amount to code needed to create the
# on screen instructions
def genLabelText(text, i):
    return OnscreenText(text=text, parent=base.a2dTopLeft, pos=(0.07, -.06 * i - 0.1),
                        fg=(0, 0, 0, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.05)


# This helpers reduce the amount of code used by loading objects, since all of
# the objects are pretty much the same.
def load_digit(i):
    image = PNMImage(f"img/{i}.png")
    front = _load_digit(f"digit {i}", image)
    # front.setPos(-1, 0, 0)
    image = PNMImage(f"img/{i}.png")
    flip_image_and_exchange_black_with_white(image)
    image.write(f"tmp/{i}_b.png")
    back = _load_digit(f"digit {i} back", image)
    back.reparentTo(front)
    back.setH(180)
    # back.setPos(1, 0, 0)
    return front


def flip_image_and_exchange_black_with_white(image):
    image.flip(True, False, False)
    white = PNMImage(image.getXSize(), image.getYSize(), 1)
    white.fill(1.0)
    image.threshold(image, 0, 0.9, white, image)


def _load_digit(name, image):
    obj = base.loader.loadModel("models/plane")
    obj.name = f"{name}"
    obj.setTransparency(TransparencyAttrib.MAlpha)       
    tex = Texture()
    tex.load(image)
    tex.setWrapU(SamplerState.WM_clamp)
    tex.setWrapV(SamplerState.WM_clamp)
    ts = TextureStage('ts')
    ts.setMode(TextureStage.MReplace)
    obj.setTexture(ts, tex)
    return obj


class Visualizer(ShowBase):

    def __init__(self, callback=None):
        ShowBase.__init__(self)
        self.digits = [load_digit(i) for i in range(10)]
        self.disableMouse()
        self.render.setShaderAuto()        
        self.setBackgroundColor(1, 1, 1, 1)
        self.camera_distance = -60
        self.camera.setPos(0, self.camera_distance, 0)
        self.camera.lookAt(0, 0, 0)
        self.setup_lighting()
        self.scene = None
        if callback:
            self.config = []
            self.hourText = None
            callback(self)
        else:
            self.accept("escape", sys.exit)
            self.accept("q", sys.exit)
            self.accept("space", self.toggle_rotation)
            self.accept("arrow_up", self.move_camera, [+5])
            self.accept("arrow_down", self.move_camera, [-5])
            self.accept("arrow_up-repeat", self.move_camera, [+5])
            self.accept("arrow_down-repeat", self.move_camera, [-5])
            self.accept("arrow_left", self.turn_scene, [-1])
            self.accept("arrow_right", self.turn_scene, [+1])
            self.accept("arrow_left-repeat", self.turn_scene, [-1])
            self.accept("arrow_right-repeat", self.turn_scene, [+1])
            self.accept("shift-arrow_left", self.turn_hour, [-1])
            self.accept("shift-arrow_right", self.turn_hour, [+1])
            self.toggle_rotation(rotating=True)
            genLabelText("ESC/Q: Quit", 0)
            genLabelText("SPACE: Start/Stop Rotation", 1)
            genLabelText("UP/DOWN: Move Camera In/Out", 2)
            genLabelText("(SHIFT) LEFT/RIGHT: Rotate Scene", 3)
            self.hourText = genLabelText("12:00", 4)
            self.degreeText= genLabelText("000°", 5)


    def setup_lighting(self):
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((.1, .1, .1, 1))
        self.render.setLight(self.render.attachNewNode(ambientLight))


    def set_configuration(self, data):
        """
        Set the configuration, for expected format see get_configuration().
        """
        if (self.scene):
            self.scene.detachNode()
        self.config = []
        self.scene = self.render.attachNewNode("scene")
        self.scene.reparentTo(self.render)
        for item in data:
            digit = self.digits[item[0]].copyTo(self.scene)
            digit.reparentTo(self.scene)
            digit.setPos(item[1]/SIZE_SCALE, item[2]/SIZE_SCALE, item[3]/SIZE_SCALE)
            digit.setScale(item[4]/SIZE_SCALE)
            digit.setH(item[5])
            self.config.append(digit)


    def rotate_scene(self, task):
        delta = task.time - self.rotationTime
        self.rotate_to(degrees=self.scene.getH() + delta * 30.0)
        self.rotationTime = task.time
        return Task.cont
    

    def rotate_to(self, degrees=None, hour=0):       
        if degrees is None:
            degrees = (hour % 12) * 30.0
        self.scene.setH(degrees)
        if self.hourText:
            t = (degrees / 30) % 12
            if (t < 1.0):
                t += 12.0
            self.hourText.setText(f" {int(t):2d}:{int((t - int(t)) * 60):02d}")
            self.degreeText.setText(f" {int(degrees)%360:03d}°")
    

    def turn_scene(self, direction):
        if self.rotating:
            self.toggle_rotation()
        self.rotate_to(degrees=self.scene.getH() + direction)


    def turn_hour(self, direction):
        if self.rotating:
            self.toggle_rotation()
        h = self.scene.getH() / 30
        if h == int(h):
            self.rotate_to(hour=int(h) + direction)
        elif direction > 0:
            self.rotate_to(hour=int(h) + 1)
        else:
            self.rotate_to(hour=int(h))


    def make_screenshot(self, degrees):
        self.rotate_to(degrees=degrees)
        base.graphicsEngine.renderFrame()
        shot = self.win.getScreenshot()
        return shot


    def toggle_rotation(self, rotating=None):
        self.rotationTime = 0.0
        self.rotating =  not self.rotating if rotating == None else rotating
        if self.rotating:
            self.taskMgr.add(self.rotate_scene, "RotateSceneTask")
        else:
            self.taskMgr.remove("RotateSceneTask")

    
    def move_camera(self, delta):
        self.camera_distance += delta
        self.camera.setPos(0, self.camera_distance, 0)


def headless_app(callback, prc_file="headless.prc"):
    loadPrcFile(prc_file)
    app = Visualizer(callback=callback)
    return app


def start(config="config.json"):
    loadPrcFile("digits.prc")
    with open(config, "r") as f:
        config = json.load(f)
    app = Visualizer()
    app.set_configuration(config)
    app.run()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        start(config=sys.argv[1])
    else:
        start()