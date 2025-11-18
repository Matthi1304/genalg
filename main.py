#!/usr/bin/env python3

from direct.gui.DirectGui import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import *
import sys


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.disableMouse()
        self.render.setShaderAuto()
        
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
        
        self.rotating = False

    
    def setup_lighting(self):
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((.1, .1, .1, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(LVector3(0, 45, -45))
        directionalLight.setColor((0.2, 0.2, 0.2, 1))
        self.render.setLight(self.render.attachNewNode(directionalLight))
        self.render.setLight(self.render.attachNewNode(ambientLight))

    def setup_scene(self):
        self.scene = self.loader.loadModel("teapot")
        self.scene.reparentTo(self.render)
        self.scene.setPos(Point3(0, 0, -1))
        self.scene.setColor(.9, .9, .9, 1)
        print("loaded scene")
    
    def rotate_scene(self, task):
        """Rotiert die Szene kontinuierlich"""
        if self.rotating:
            angle_degrees = task.time * 10.0  # 10 degrees per second
            # rotate at Y axis
            self.scene.setH(angle_degrees)

        return Task.cont
    
    def toggle_rotation(self):
        self.rotating = not self.rotating
        status = "aktiviert" if self.rotating else "deaktiviert"
    
    def move_camera_forward(self):
        self.camera_distance += 5
        self.camera.setPos(0, self.camera_distance, 0)
    
    def move_camera_backward(self):
        self.camera_distance -= 5
        self.camera.setPos(0, self.camera_distance, 0)


if __name__ == "__main__":
    app = MyApp()
    app.run()
