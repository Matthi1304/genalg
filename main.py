#!/usr/bin/env python3

from direct.gui.DirectGui import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import *
import sys
from random import randint, choice, random


# Macro-like function used to reduce the amount to code needed to create the
# on screen instructions
def genLabelText(text, i):
    return OnscreenText(text=text, parent=base.a2dTopLeft, pos=(0.07, -.06 * i - 0.1),
                        fg=(0, 0, 0, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.05)


# This helps reduce the amount of code used by loading objects, since all of
# the objects are pretty much the same.
def load_digit(i):
    # todo: numbers should be white on the backside
    obj = base.loader.loadModel("models/plane")
    obj.name = f"{i}"
    tex = base.loader.loadTexture(f"textures/{i}.png")
    tex.setWrapU(SamplerState.WM_clamp)
    tex.setWrapV(SamplerState.WM_clamp)
    obj.setTexture(tex, 1)
    
    # Enable transparency blending.
    obj.setTransparency(TransparencyAttrib.MAlpha)

    return obj

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.digits = [load_digit(i) for i in range(10)]

        self.disableMouse()
        self.render.setShaderAuto()        

        self.setBackgroundColor(1, 1, 1, 1)
        
        self.camera_distance = -100
        self.camera.setPos(0, self.camera_distance, 0)
        self.camera.lookAt(0, 0, 0)
        
        self.setup_lighting()
        self.setup_scene()
        
        self.accept("escape", sys.exit)
        self.accept("space", self.toggle_rotation)
        self.accept("arrow_up", self.move_camera_forward)
        self.accept("arrow_down", self.move_camera_backward)
        self.accept("x", self.toggle_xray_mode)
        
        self.toggle_rotation(rotating=True)

        genLabelText("ESC: Quit", 0)
        genLabelText("SPACE: Start/Stop Rotation", 1)
        genLabelText("UP/DOWN: Move Camera In/Out", 2)


    def setup_lighting(self):
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((.1, .1, .1, 1))
        self.render.setLight(self.render.attachNewNode(ambientLight))
    

    def random_point_in_sphere(self, radius):
        while True:
            x = random() * 2 - 1
            y = random() * 2 - 1
            z = random() * 2 - 1
            if x*x + y*y + z*z <= 1:
                return Point3(x * radius, y * radius, z * radius)


    def setup_scene(self):
        self.config = []
        self.scene = self.render.attachNewNode("scene")
        self.scene.reparentTo(self.render)
        for i in range(150):
            digit = self.digits[randint(0, 9)].copyTo(self.render)
            digit.reparentTo(self.scene)
            digit.setPos(self.random_point_in_sphere(15))
            digit.setScale(random() * 10 + 0.1)
            digit.setH(randint(0, 360))
            self.config.append(digit)
        print("loaded scene")
        # todo: test code, remove later
        if True:
            digit = self.digits[8].copyTo(self.render)
            digit.reparentTo(self.render)
            digit.setPos(0, -100, 0)
            digit.setScale(10)
            digit.setH(180)
            self.config.append(digit)

    
    def rotate_scene(self, task):
        delta = task.time - self.rotationTime
        self.scene.setH(self.scene.getH() + delta * 30.0)
        self.rotationTime = task.time
        return Task.cont


    def toggle_rotation(self, rotating=None):
        self.rotationTime = 0.0
        self.rotating =  not self.rotating if rotating == None else rotating
        if self.rotating:
            self.taskMgr.add(self.rotate_scene, "RotateSceneTask")
        else:
            self.taskMgr.remove("RotateSceneTask")

    
    def move_camera_forward(self):
        self.camera_distance += 5
        self.camera.setPos(0, self.camera_distance, 0)
    

    def move_camera_backward(self):
        self.camera_distance -= 5
        self.camera.setPos(0, self.camera_distance, 0)


    def toggle_xray_mode(self):
        """Toggle X-ray mode on and off. This is useful for seeing the
        effectiveness of the occluder culling."""
        self.xray_mode = not self.xray_mode if hasattr(self, 'xray_mode') else True
        if self.xray_mode:
            self.scene.setColorScale((1, 1, 1, 0.5))
            self.scene.setTransparency(TransparencyAttrib.MDual)
        else:
            self.scene.setColorScaleOff()
            self.scene.setTransparency(TransparencyAttrib.MNone)


if __name__ == "__main__":
    from panda3d.core import loadPrcFile
    loadPrcFile("digits.prc")
    app = MyApp()
    app.run()
