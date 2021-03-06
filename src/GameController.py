#!/usr/bin/env python3
import glfw
import numpy as np
from OpenGL.GL import *
from PIL import Image

from src.objects.GameObject import GameObject
from src.objects.geometrics.TriangleObject import TriangleObject
from src.objects.geometrics.RectangleObject import RectangleObject


class GameController:
    """
    Classe principal que engloba todos os estados, objetos, controle de janela,
    inputs de usuário e loop principal da lógica do jogo.
    """


    def __init__(self, title="Computer Graphics 101", width=600, height=600, enable3D=False, scheme = []) -> None:
        """
        Set the program window configurations and other important variables
        """
        self.__glfw_window = False
        self.__glfw_title  = title
        self.__glfw_resolution  = (width, height)
        self.__glfw_enable3D = enable3D
        self.scheme = scheme
        self.__configure_window()
        
        self.__objects = []
        self.__vertices = []
        self.__buffer = None
        self.__solid_objects = []

        self.__glfw_keys = {}
        self.__glfw_observe_keys = [glfw.KEY_R]
        self.__glfw_buttons = {}

        self.__configure_vertexes_and_keys()
        self.__configure_objects()
        self.__configure_buffer()
        self.__configure_textures()


    def __configure_window(self) -> None:
        """
        Internal function with the GLFW window and context configurations
        """
        glfw.init()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
        self.__glfw_window = glfw.create_window(self.__glfw_resolution[0], self.__glfw_resolution[1], self.__glfw_title, None, None)
        glfw.make_context_current(self.__glfw_window)

        # Register handlers
        glfw.set_key_callback(self.__glfw_window, self.__key_event_handler)
        glfw.set_mouse_button_callback(self.__glfw_window, self.__mouse_event_handler)

        # Compile shaders of objects used in scene scheme
        for object in self.scheme:
            object["type"].shader_program.compile()


    def __configure_vertexes_and_keys(self) -> None:
        """
        Configure vertex configurations and subscribed keys
        """
        for object in self.scheme:
            # Update Object offset and save vertices in program buffer
            object["type"].shader_offset = len(self.__vertices)
            self.__vertices += object["type"].get_vertices()

            # Configure observed keys
            if hasattr(object["type"], "subscribe_keys"):
                self.__glfw_observe_keys += object["type"].subscribe_keys


    def __configure_objects(self) -> None:
        """
        Start/Restart all objects used in the game
        """
        self.__objects = []
        self.__solid_objects = []

        for object in self.scheme:
            # Create all desired object items
            items = []
            for item in object["items"]:
                items.append(object["type"](position=item["position"], size=item["size"], rotate=item["rotate"], window_resolution=self.__glfw_resolution))
                
                # If is solid create a reference in the solid objects array
                if item.get("props", {"hitbox": False})["hitbox"]:
                    items[-1].configure_hitbox()
                    if items[-1].object_hitbox != None:
                        self.__solid_objects.append(items[-1])

            # Append created items to objects
            self.__objects.append({"type": object["type"], "items": items })


    def __configure_buffer(self) -> None:
        """
        Instantiate a buffer in GPU and send the vertex data.
        """
        self.__vertices = np.array(self.__vertices, dtype=np.float32)
        self.__buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.__buffer)
        glBufferData(GL_ARRAY_BUFFER, self.__vertices.nbytes, self.__vertices, GL_STATIC_DRAW)


    def __configure_textures(self) -> None:
        """
        Instantiate and initialize all textures used by te objects
        """

        # Calc. the sum number of textures needed and generate them
        qtd_textures = 0
        for object in self.scheme:
            qtd_textures += len(object["type"].shader_textures)

        # If no textures to create then exits
        if qtd_textures == 0:
            return 

        # Init all the textures
        texture_id = 1
        glGenTextures(qtd_textures)
        for object in self.scheme:
            for texture in object["type"].shader_textures:
                # Texture Settings
                glBindTexture(GL_TEXTURE_2D, texture_id)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);	
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                # Load image and generate midmap
                image = Image.open(texture)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image.size[0], image.size[1], 0, GL_RGB, GL_UNSIGNED_BYTE, image.tobytes("raw", "RGB", 0, -1))
                glGenerateMipmap(GL_TEXTURE_2D)
                # Set id and increment
                object["type"].shader_textures_ids.append(texture_id)
                texture_id += 1


    def __key_event_handler(self, window, key, scancode, action, mods):
        """
        Manipula os eventos de teclados lidos pelo GLFW e salva as mudanças de estado 
        apenas das teclas de interesse para economizar memória não necessária
        """
        if key in self.__glfw_observe_keys:
            self.__glfw_keys[key] = { "action": action, "code": scancode, "mods": mods }


    def __mouse_event_handler(self, window, button, action, mods):
        """
        Manipula os eventos de mouse que, como são menores, não necessita de uma
        seleção tão aguçada de quais estados salvar
        """
        self.__glfw_buttons[button] = { "action": action, "mods": mods }


    def start(self) -> None:
        """
        Start the game logic and graphic loop. Runs until the player close the window.
        """
        glfw.show_window(self.__glfw_window)

        if self.__glfw_enable3D:
            glEnable(GL_DEPTH_TEST)

        # Enable color transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        while not glfw.window_should_close(self.__glfw_window):
            glfw.poll_events() 
            
            # Reset the screen with the white color
            if self.__glfw_enable3D:
                glClear(GL_COLOR_BUFFER_BIT) 
            else:
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) 
            glClearColor(0.709, 0.486, 0.443, 1.0)

            # If key R pressed restart the game
            if self.__glfw_keys.get(glfw.KEY_R, {"action": 0})["action"]:
                self.__configure_objects()

            # Execute objects logics, if object is solid pass all solid objects to 
            # be used in the collision logics calculation
            for object_group in reversed(self.__objects):
                for item in object_group["items"]:
                    if item.object_hitbox == None:
                        item.logic(keys=self.__glfw_keys, buttons=self.__glfw_buttons)
                    else:
                        item.logic(keys=self.__glfw_keys, buttons=self.__glfw_buttons, objects=self.__solid_objects)


            # Foreach object group active the shader and draw items
            # Obs: Reversed because first groups have priority.
            for object_group in reversed(self.__objects):
                object_group["type"].shader_program.use()
                for item in object_group["items"]:
                    item.draw()

            glfw.swap_buffers(self.__glfw_window)
        glfw.terminate()


if __name__ == '__main__':
    game = GameController(title="Testing Game Controller", width=1200, height=600, enable3D=False)
    game.start()