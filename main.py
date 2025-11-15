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
        self.camera.setPos(0, -20, 5)
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
        """3D-Objekte zur Szene hinzufügen"""
        # Würfel in der Mitte - verwende Panda3D's eingebaute Modelle
        try:
            # Versuche zuerst das eingebaute Box-Modell zu laden
            self.cube = self.loader.loadModel("models/misc/box")
        except:
            # Falls nicht verfügbar, verwende eine Kugel als Alternative
            self.cube = self.loader.loadModel("models/misc/sphere")

        self.cube.setScale(2, 2, 2)
        self.cube.setPos(0, 0, 0)
        self.cube.setColor(0.0, 0.0, 0.0, 1.0)  # Schwarz
        self.cube.reparentTo(self.render)

        # Kleinere Würfel drumherum
        colors = [
            (0.0, 0.0, 0.0, 1.0),  # Schwarz
            (0.0, 0.0, 0.0, 1.0),  # Schwarz
            (0.0, 0.0, 0.0, 1.0),  # Schwarz
            (0.0, 0.0, 0.0, 1.0),  # Schwarz
        ]

        positions = [
            (5, 0, 0),
            (-5, 0, 0),
            (0, 5, 0),
            (0, -5, 0),
        ]

        self.small_cubes = []
        for pos, color in zip(positions, colors):
            try:
                cube = self.loader.loadModel("models/misc/box")
            except:
                cube = self.loader.loadModel("models/misc/sphere")

            cube.setScale(1, 1, 1)
            cube.setPos(*pos)
            cube.setColor(*color)
            cube.reparentTo(self.render)
            self.small_cubes.append(cube)
    
    def rotate_scene(self, task):
        """Rotiert die Szene kontinuierlich"""
        if self.rotating:
            angle_degrees = task.time * 20.0  # 20 Grad pro Sekunde
            
            # Hauptwürfel rotieren
            self.cube.setHpr(angle_degrees, angle_degrees * 0.5, 0)
            
            # Kleine Würfel einzeln rotieren
            for i, cube in enumerate(self.small_cubes):
                cube.setHpr(angle_degrees * (1 + i * 0.2), 
                           angle_degrees * 0.3, 
                           angle_degrees * 0.7)
        
        return Task.cont
    
    def toggle_rotation(self):
        """Rotation an/aus schalten"""
        self.rotating = not self.rotating
        status = "aktiviert" if self.rotating else "deaktiviert"
        print(f"Rotation {status}")


if __name__ == "__main__":
    app = MyApp()
    app.run()
