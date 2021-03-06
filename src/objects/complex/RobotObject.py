#!/usr/bin/env python3
import math 
import numpy as np
from OpenGL.GL import *
import OpenGL.GL.shaders
import glfw

from src.shaders.Shader import Shader
from src.shaders.BaseShader import vertex_code, fragment_code
from src.objects.GameObject import GameObject
from src.helpers.collisions import hitbox_window_collider
from src.colliders.Hitbox import Hitbox

# Types used in Game Collision Logic
from src.objects.complex.BoxObject import BoxObject
from src.objects.complex.ContainerObject import ContainerObject
from src.objects.complex.ParedeSageObject import ParedeSageObject
from src.objects.complex.GateObject import GateObject

# Types used to trigger events on collide
from src.objects.complex.RotatorObject import RotatorObject
from src.objects.complex.FlamesObject import FlamesObject
from src.objects.complex.FinishObject import FinishObject


class RobotObject(GameObject):
    """
    Implementa o Robô que se move constantemente em busca de alcançar
    o objetivo da fase. 
    """

    shader_program  = Shader(vertex_code, fragment_code)
    shader_offset   = 0
    shader_vertices = []
    subscribe_keys  = []

    num_vertices = 10
    
    def get_vertices():
        """Geração dos vértices do Robo"""
        RobotObject.shader_vertices = [
            ( 0.428 , 0.857 , 0.0), # laranja
            ( 1.0 , 0.428 , 0.0),
            ( 0.857 , -0.286 , 0.0),
            ( 0.0 , -0.857 , 0.0),
            ( -0.857 , -0.286 , 0.0),
            ( -1.0 , 0.428 , 0.0),
            ( -0.428 , 0.857 , 0.0),    

            ( 0.428 , 0.857 , 0.0), # preto
            ( 0.642 , 0.714 , 0.0),
            ( 0.286 , 0.214 , 0.0),
            ( -0.286 , 0.214 , 0.0),
            ( -0.642 , 0.714 , 0.0),
            ( -0.428 , 0.857 , 0.0),

            ( 0.643 , 0.714 , 0.0), # azul direita
            ( 1.0 , 0.428 , 0.0),
            ( 0.928 , 0.0 , 0.0),
            ( 0.5 , 0.0 , 0.0),
            ( 0.285 , 0.214 , 0.0),

            ( -0.642 , 0.714 , 0.0), # azul esquerda
            ( -1.0 , 0.428 , 0.0),
            ( -0.928 , 0.0 , 0.0),
            ( -0.5 , 0.0 , 0.0),
            ( -0.285 , 0.214 , 0.0),

            ( 0.285 , 0.214 , 0.0), # contorno smile
            ( 0.5 , 0.0 , 0.0),
            ( 0.214 , -0.571 , 0.0),
            ( -0.214 , -0.571 , 0.0),
            ( -0.5 , 0.0 , 0.0),
            ( -0.285 , 0.214 , 0.0),
        ]

        counter = 29
        radius = 0.0714
        posx = 0.286
        posy = -0.071
        angle = 0.0
        for counter in range(29, 29 + RobotObject.num_vertices):
            angle += 2*math.pi/RobotObject.num_vertices
            x = math.cos(angle)*radius + posx   
            y = math.sin(angle)*radius + posy
            RobotObject.shader_vertices += [(x,y,0.0)]

        counter = 39
        radius = 0.0714
        posx = -0.285
        posy = -0.071
        angle = 0.0
        for counter in range(39, 39 + RobotObject.num_vertices):
            angle += 2*math.pi/RobotObject.num_vertices
            x = math.cos(angle)*radius + posx   
            y = math.sin(angle)*radius + posy
            RobotObject.shader_vertices += [(x,y,0.0)]

        RobotObject.shader_vertices += [
            ( -0.142 , -0.157 , 0.0), # Smiles *W*
            ( -0.128 , -0.142 , 0.0),
            ( -0.043 , -0.257 , 0.0),
            ( -0.036 , -0.236 , 0.0),

            ( -0.043 , -0.257 , 0.0),
            ( -0.057 , -0.242 , 0.0),
            ( 0.0 , -0.2 , 0.0),
            ( 0.0 , -0.185 , 0.0),

            ( 0.043 , -0.257 , 0.0),
            ( 0.057 , -0.242 , 0.0),
            ( 0.0 , -0.2 , 0.0),
            ( 0.0 , -0.185 , 0.0),

            ( 0.143 , -0.157 , 0.0),
            ( 0.128 , -0.142 , 0.0),
            ( 0.043 , -0.257 , 0.0),
            ( 0.036 , -0.236 , 0.0),
        ]

        counter = 65
        radius = 0.857
        posx = -0.786
        posy = 0.0
        angle = math.pi/2
        for counter in range(65, 65 + RobotObject.num_vertices):
            angle += math.pi/RobotObject.num_vertices
            x = math.cos(angle)*radius*0.4 + posx   
            y = math.sin(angle)*radius + posy
            RobotObject.shader_vertices += [(x,y,0.0)]

        counter = 75
        radius = 0.857
        posx = +0.785
        posy = 0.0
        angle = math.pi/2
        for counter in range(75, 75 + RobotObject.num_vertices):
            angle += math.pi/RobotObject.num_vertices
            x = -1*math.cos(angle)*radius*0.4 + posx
            y = math.sin(angle)*radius + posy
            RobotObject.shader_vertices += [(x,y,0.0)]

        return RobotObject.shader_vertices


    def __init__(self, position=(0,0), size=(200,200), rotate=0, window_resolution=(600,600)) -> None:
        super().__init__(position=position, size=size, rotate=rotate, window_resolution=window_resolution)

        self.__delta_translate = 6 * 0.1  # Moves 0.1 px each translation iteration
        self.__delta_direction = np.array([0.0, 1.0], dtype=np.float) # Initial direction up
        self.__dead = False
    

    def configure_hitbox(self) -> None:
        """Define a box type Hitbox"""
        box_values = [ self.position[0]-(0.857)*self.size[0]/2, self.position[1]-(0.857)*self.size[1]/2, 
                        0.857*self.size[0], 0.857*self.size[1] ]

        if self.object_hitbox == None:
            self.object_hitbox = Hitbox("box", box_values)
        else: 
            self.object_hitbox.update_values(box_values)


    def draw(self):
        """
        Desenha o triângulo na tela
        """
        # Prepare the model transformation matrix
        model_matrix = np.array(self._generate_model_matrix(), np.float32)

        # Send final matrix to the GPU unit
        RobotObject.shader_program.set4fMatrix('u_model_matrix', model_matrix)
        
        # Draw steps
        RobotObject.shader_program.set4Float('u_color',[0.678, 0.333, 0.118, 1.0])
        glDrawArrays(GL_TRIANGLE_FAN, RobotObject.shader_offset+0, 7) # perfil

        RobotObject.shader_program.set4Float('u_color',[ 0.153, 0.188, 0.188, 1.0])
        glDrawArrays(GL_TRIANGLE_FAN, RobotObject.shader_offset+7, 6) # cima

        RobotObject.shader_program.set4Float('u_color',[ 0.290, 0.498, 0.447, 1.0])
        glDrawArrays(GL_TRIANGLE_FAN, RobotObject.shader_offset+13, 5) # azul direita
        glDrawArrays(GL_TRIANGLE_FAN, RobotObject.shader_offset+18, 5) # azul esquerda

        RobotObject.shader_program.set4Float('u_color',[ 0.972, 0.898, 0.294, 1.0])
        glDrawArrays(GL_TRIANGLE_FAN, RobotObject.shader_offset+23, 6) # contorno smile preto

        RobotObject.shader_program.set4Float('u_color',[ 0.647, 0.247, 0.117, 1.0])
        glDrawArrays(GL_TRIANGLE_FAN, RobotObject.shader_offset+29, RobotObject.num_vertices) #carinha
        glDrawArrays(GL_TRIANGLE_FAN, RobotObject.shader_offset+29 + RobotObject.num_vertices, RobotObject.num_vertices)
        glDrawArrays(GL_TRIANGLE_STRIP, RobotObject.shader_offset+29 + 2 * RobotObject.num_vertices, 4)
        glDrawArrays(GL_TRIANGLE_STRIP, RobotObject.shader_offset+33 + 2 * RobotObject.num_vertices, 4)
        glDrawArrays(GL_TRIANGLE_STRIP, RobotObject.shader_offset+37 + 2 * RobotObject.num_vertices, 4)
        glDrawArrays(GL_TRIANGLE_STRIP, RobotObject.shader_offset+41 + 2 * RobotObject.num_vertices, 4)

        RobotObject.shader_program.set4Float('u_color',[ 0.212, 0.231, 0.227, 1.0])
        glDrawArrays(GL_TRIANGLE_FAN, RobotObject.shader_offset+45 + 2 * RobotObject.num_vertices, RobotObject.num_vertices)
        glDrawArrays(GL_TRIANGLE_FAN, RobotObject.shader_offset+45 + 3 * RobotObject.num_vertices, RobotObject.num_vertices)


    def __collision_logic(self, move,  objects=[]) -> None:
        """Wrapper collision Logic"""
        collision = False
        last_position = self.position[move]

        self.position[move] += self.__delta_translate * self.__delta_direction[move]
        self.configure_hitbox()

        collision |= hitbox_window_collider(self.position, self.size, self.window_resolution)        
        for item in objects: 
            if item != self and type(item) in [BoxObject, ContainerObject, ParedeSageObject, GateObject]:
                collision |= self.object_hitbox.check_collision(item.object_hitbox)
            if collision:
                self.position[move] = last_position
                self.__delta_direction[move] *= -1.0
                break


    def __event_trigger_logic(self, objects=[]) -> None:
        """Wrapper event triggers logic"""
        for item in objects:
            if item == self:
                continue
            if type(item) == RotatorObject and self.object_hitbox.check_collision(item.object_hitbox):
                rad = item.rotate*(np.pi/180.0)
                self.__delta_direction[0] = np.cos(rad)
                self.__delta_direction[1] = np.sin(rad)
            elif type(item) == FlamesObject and self.object_hitbox.check_collision(item.object_hitbox):
                self.__dead = True
                break
            elif type(item) == FinishObject and self.object_hitbox.check_collision(item.object_hitbox):
                self.__delta_translate = 0.0
                break

    def logic(self, keys={}, buttons={}, objects=[]) -> None:
        """
        Implementa a lógica de colisões do robo
        """ 
        
        if self.__dead:
            self.rotate  += 0.2
            self.size[0] -= 0.03 if self.size[0] > 0 else 0.0
            self.size[1] -= 0.03 if self.size[1] > 0 else 0.0
            self._configure_gl_variables()
            return

        # Event trigger logic
        self.__event_trigger_logic(objects)

        # Horizontal movement
        self.__collision_logic(0, objects)
            
        # Vertical movement
        self.__collision_logic(1, objects)

        # Update rotation from current direction vector
        degX =  np.degrees(np.arccos(self.__delta_direction[0]))
        degY =  np.degrees(np.arcsin(self.__delta_direction[1]))
        self.rotate = (degX-90.0) if degY >= 0 else (-degX-90.0)

        self._configure_gl_variables()