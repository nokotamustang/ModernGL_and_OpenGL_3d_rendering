import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"  # noqa: E402

import pygame
import moderngl
import sys

from core import Camera, Prototype, Shadow, Texture, Shader, Scene


class Engine:
    # Settings
    target_fps = 999
    free_move = True
    vertical_sync = 0
    target_display = 0
    base_path = '.'
    shader_path = 'shaders'
    # Variables
    fps = 0
    time = 0
    delta_time = 0
    second_count = 0
    # State
    paused = True
    full_polygon = True
    full_screen = False
    show_flash_light = False
    show_global_light = True
    show_light_sources = True

    texture_blend = 1.0
    local_light = 1.0

    global_light_value = 5.0
    flash_light_value = 5.0
    local_light_value = 5.0

    def __init__(self, windowed_win_size=(1600, 900), full_screen_win_size=(1920, 1080)):
        # Initialize pygame modules
        pygame.mixer.pre_init(44100, 16, 2, 4096)
        pygame.init()
        # Window size
        self.full_screen_win_size = full_screen_win_size
        self.windowed_win_size = windowed_win_size
        if self.full_screen:
            self.win_size = self.full_screen_win_size
        else:
            self.win_size = self.windowed_win_size
        # Set OpenGL attributes
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 4)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 6)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, self.vertical_sync)
        # Create OpenGL context for 3D rendering
        self.game_screen = pygame.display.set_mode(self.win_size, flags=pygame.OPENGL | pygame.DOUBLEBUF,
                                                   display=self.target_display, vsync=self.vertical_sync)
        # Mouse settings
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)
        # Detect and use existing OpenGL context
        self.ctx = moderngl.create_context()
        self.ctx.enable(flags=moderngl.DEPTH_TEST | moderngl.CULL_FACE | moderngl.BLEND)
        self.ctx.cull_face = "back"
        self.ctx.gc_mode = 'auto'
        # Create an object to help track time
        self.clock = pygame.time.Clock()
        # Set fps max
        pygame.time.set_timer(pygame.USEREVENT, 1000 // self.target_fps)
        # Camera
        self.camera = Camera(self, position=(0, 0, 5))
        # Texture, Shader, Shadow, Prototype
        self.texture = Texture(self)
        self.shader = Shader(self)
        self.shadow = Shadow(self)
        self.prototype = Prototype(self)
        # Scene of objects (after lights)
        self.scene = Scene(self)
        # Font
        self.font = pygame.font.SysFont('arial', 64)

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.scene.destroy()
                self.skybox.destroy()
                self.prototype.destroy()
                self.shader.destroy()
                self.shadow.destroy()
                self.texture.destroy()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                self.paused = not self.paused
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                self.show_global_light = not self.show_global_light
                if self.show_global_light == True:
                    self.global_light.strength = self.global_light_value
                else:
                    self.global_light.strength = 0.0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                self.full_polygon = not self.full_polygon
                self.toggle_full_polygon()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                if self.local_light == 0.0:
                    self.local_light = 1.0
                else:
                    self.local_light = 0.0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
                if self.texture_blend == 0.0:
                    self.texture_blend = 1.0
                else:
                    self.texture_blend = 0.0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F6:
                self.show_light_sources = not self.show_light_sources
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.full_screen = not self.full_screen
                self.toggle_full_screen()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                self.show_flash_light = not self.show_flash_light
                if self.show_flash_light == True:
                    self.flash_light.strength = self.flash_light_value
                else:
                    self.flash_light.strength = 0.0

    def toggle_full_screen(self):
        if self.full_screen:
            self.win_size = self.full_screen_win_size
            pygame.display.set_mode(self.win_size,
                                    flags=pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN,
                                    display=self.target_display,
                                    vsync=self.vertical_sync)
            self.ctx.viewport = (0, 0, *self.win_size)
            self.camera.set_aspect_and_projection()
        else:
            self.win_size = self.windowed_win_size
            pygame.display.set_mode(self.win_size,
                                    flags=pygame.OPENGL | pygame.DOUBLEBUF,
                                    display=self.target_display,
                                    vsync=self.vertical_sync)
            self.ctx.viewport = (0, 0, *self.win_size)
            self.camera.set_aspect_and_projection()

    def toggle_full_polygon(self):
        if self.full_polygon:
            self.ctx.wireframe = False
        else:
            self.ctx.wireframe = True

    def update(self):
        self.camera.update()
        self.global_light.rotate(0.00027 * self.delta_time)
        self.flash_light.update()
        self.scene.update()

    def render(self):
        self.scene.render()

    def run(self):
        while True:
            self.delta_time = self.clock.tick(self.target_fps)
            self.raw_delta_time = self.delta_time
            if not self.paused:
                self.time = self.time + (self.delta_time * 0.001)
            else:
                self.delta_time = 0
            self.check_events()
            self.update()
            self.render()
            self.fps = self.clock.get_fps()
            self.second_count = self.second_count + self.raw_delta_time
            if self.second_count >= 1000:
                print(f'dt: {self.raw_delta_time:.2f}, fps: {self.fps:.2f}')
                self.second_count = self.second_count - 1000


if __name__ == '__main__':
    app = Engine()
    app.run()
