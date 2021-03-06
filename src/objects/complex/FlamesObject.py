#!/usr/bin/env python3
import numpy as np
from OpenGL.GL import *
import OpenGL.GL.shaders
import glfw
import math
import random

from src.shaders.Shader import Shader
from src.shaders.MagmaShader import vertex_code, fragment_code
from src.objects.GameObject import GameObject
from src.colliders.Hitbox import Hitbox
from src.helpers.vertex import generate_random_circle_vertexes

class FlamesObject(GameObject):
    """
    Implementa a poça de fogo incendiária que mata o robozinho.
    """

    shader_program  = Shader(vertex_code, fragment_code)
    shader_offset   = 0
    shader_vertices = []
    subscribe_keys  = []
    num_vertices    = 128

    def get_vertices():
        pi = 3.14
        counter = 0
        radius = 0.8

        # vertices = np.zeros(FlamesObject.num_vertices, [("position", np.float32, 2)])

        angle = 0.0
        for counter in range(FlamesObject.num_vertices):
            angle += 2*pi/FlamesObject.num_vertices 
            x = math.cos(angle)*radius
            y = math.sin(angle)*radius  
            xd = math.degrees(x)
            yd = math.degrees(y)
            aux = math.atan2(xd, yd)
            radius += math.sin(aux * 10.) * .04
            x = math.cos(angle)*radius
            y = math.sin(angle)*radius
            FlamesObject.shader_vertices += [(x,y,0.0)]

        return FlamesObject.shader_vertices


    def __init__(self, position=(0,0), size=(200,200), rotate=0, window_resolution=(600,600)) -> None:
        super().__init__(position=position, size=size, rotate=rotate, window_resolution=window_resolution)

        self.__u_time = 0.0


    def configure_hitbox(self) -> None:
        """Define a hitbox"""
        box_values = [ self.position[0]-0.2*self.size[0]/2, self.position[1]-0.2*self.size[1]/2, 
                        0.2*self.size[0], 0.2*self.size[1] ]

        if self.object_hitbox == None:
            self.object_hitbox = Hitbox("box", box_values)
        else: 
            self.object_hitbox.update_values(box_values)


    def draw(self):
        """Desenha o objeto na tela"""
        # Prepare the model transformation matrix
        model_matrix = np.array(self._generate_model_matrix(), np.float32)

        # Send final matrix to the GPU unit
        FlamesObject.shader_program.set4fMatrix('u_model_matrix', model_matrix)
        FlamesObject.shader_program.setFloat('u_time', self.__u_time)
        FlamesObject.shader_program.set2Float('u_resolution', [1200.0, 600.0])
        self.__u_time += 0.0005
        
        # Draw object steps
        FlamesObject.shader_program.set4Float('u_color',[1.0,0.0,0.3,1.0])
        glDrawArrays(GL_TRIANGLE_FAN, FlamesObject.shader_offset, FlamesObject.num_vertices)


    def logic(self, keys={}, buttons={}, objects=[]) -> None:
        """Nenhuma lógica necessária nesse componente"""
        return 
