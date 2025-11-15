#!/usr/bin/env python3
"""
Panda3D Starter-Projekt
Ein einfaches 3D-Projekt mit einer rotierenden Szene
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight
from direct.task import Task
import sys


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Hintergrundfarbe setzen
        self.setBackgroundColor(1.0, 1.0, 1.0, 1)
        
        # Kamera Position anpassen
        self.camera.setPos(0, -30, 0)
        self.camera.lookAt(0, 0, 0)
        
        # Beleuchtung hinzufügen
        self.setup_lighting()
        
        # 3D-Objekte zur Szene hinzufügen
        self.setup_scene()
        
        # Rotations-Task hinzufügen
        self.taskMgr.add(self.rotate_scene, "RotateSceneTask")
        
        # Tastatur-Steuerung
        self.accept("escape", sys.exit)
        self.accept("space", self.toggle_rotation)
        
        self.rotating = True
        
        print("\n=== Panda3D Projekt gestartet ===")
        print("Steuerung:")
        print("  ESC   - Beenden")
        print("  SPACE - Rotation an/aus")
        print("================================\n")
    
    def setup_lighting(self):
        """Beleuchtung für die Szene einrichten"""
        # Helles ambientes Licht
        ambient_light = AmbientLight("ambient_light")
        ambient_light.setColor((1.0, 1.0, 1.0, 1))
        self.ambient_light_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(self.ambient_light_np)
    
    def setup_scene(self):
        """3D-Objekte zur Szene hinzufügen - Form der Ziffer 1"""
        # Erstelle einen Container-Node für die gesamte Ziffer 1
        self.digit_one = self.render.attachNewNode("digit_one")

        # Hauptstamm der 1 (vertikal)
        stem = self.loader.loadModel("models/box")
        stem.setScale(1, 0.5, 8)  # Dünn und hoch
        stem.setPos(0, 0, 0)
        stem.setColor(0.0, 0.0, 0.0, 1.0)
        stem.reparentTo(self.digit_one)

        # Oberer schräger Teil (Dach)
        top = self.loader.loadModel("models/box")
        top.setScale(1.5, 0.5, 1)
        top.setPos(-1.2, 0, 6)
        top.setHpr(0, 0, -30)  # Schräg nach links
        top.setColor(0.0, 0.0, 0.0, 1.0)
        top.reparentTo(self.digit_one)

        # Basis der 1 (horizontal)
        base = self.loader.loadModel("models/box")
        base.setScale(4, 0.5, 1)
        base.setPos(0, 0, -8)
        base.setColor(0.0, 0.0, 0.0, 1.0)
        base.reparentTo(self.digit_one)
    
    def rotate_scene(self, task):
        """Rotiert die Szene kontinuierlich"""
        if self.rotating:
            angle_degrees = task.time * 10.0  # 10 Grad pro Sekunde (langsam)

            # Die gesamte Ziffer 1 als Einheit um die Y-Achse rotieren
            self.digit_one.setH(angle_degrees)

        return Task.cont
    
    def toggle_rotation(self):
        """Rotation an/aus schalten"""
        self.rotating = not self.rotating
        status = "aktiviert" if self.rotating else "deaktiviert"
        print(f"Rotation {status}")


if __name__ == "__main__":
    app = MyApp()
    app.run()
