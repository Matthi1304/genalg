#!/usr/bin/env python3

from direct.gui.DirectGui import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import *
import sys
from random import randint, choice, random

# This helps reduce the amount of code used by loading objects, since all of
# the objects are pretty much the same.
def loadObject(tex):
    # Every object uses the plane model
    obj = base.loader.loadModel("models/plane")
    obj.name = tex
    tex = base.loader.loadTexture("textures/" + tex)
    tex.setWrapU(SamplerState.WM_clamp)
    tex.setWrapV(SamplerState.WM_clamp)
    obj.setTexture(tex, 1)
    
    # Enable transparency blending.
    obj.setTransparency(TransparencyAttrib.MAlpha)

    return obj

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.disableMouse()
        self.render.setShaderAuto()
        
        self.digits = [loadObject(f"{i}.png") for i in range(10)]

        self.setBackgroundColor(1, 1, 1, 1)
        
        self.camera_distance = -100
        self.camera.setPos(0, self.camera_distance, 0)
        self.camera.lookAt(0, 0, 0)
        
        self.setup_lighting()
        self.setup_scene()
        
        self.taskMgr.add(self.rotate_scene, "RotateSceneTask")
        
        self.accept("escape", sys.exit)
        self.accept("space", self.toggle_rotation)
        self.accept("arrow_up", self.move_camera_forward)
        self.accept("arrow_down", self.move_camera_backward)
        
        self.rotating = True

    def setup_lighting(self):
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((.1, .1, .1, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(LVector3(0, 45, -45))
        directionalLight.setColor((0.2, 0.2, 0.2, 1))
        self.render.setLight(self.render.attachNewNode(directionalLight))
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
        print("loaded scene")
    
    def rotate_scene(self, task):
        """Rotiert die Szene kontinuierlich"""
        if self.rotating:
            angle_degrees = task.time * 30.0
            # rotate at Y axis
            self.scene.setH(angle_degrees)

        return Task.cont
    
    def toggle_rotation(self):
        self.rotating = not self.rotating
    
    def move_camera_forward(self):
        self.camera_distance += 5
        self.camera.setPos(0, self.camera_distance, 0)
    
    def move_camera_backward(self):
        self.camera_distance -= 5
        self.camera.setPos(0, self.camera_distance, 0)


if __name__ == "__main__":
    app = MyApp()
    app.run()
