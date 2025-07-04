import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"  # noqa: E402

import pygame
import moderngl
import sys
from OpenGL.GL import glGetString, GL_SHADING_LANGUAGE_VERSION


class Engine:
    # Settings
    target_fps = 999
    free_move = True
    vertical_sync = 0
    target_display = 0
    # Variables
    fps = 0
    time = 0
    delta_time = 0
    second_count = 0
    # State
    paused = True
    full_screen = False

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
        # Set OpenGL attributes (no version specification to use default)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, self.vertical_sync)
        # Create OpenGL context for 3D rendering
        self.game_screen = pygame.display.set_mode(
            self.win_size,
            flags=pygame.OPENGL | pygame.DOUBLEBUF,
            display=self.target_display,
            vsync=self.vertical_sync
        )
        # Mouse settings
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)
        # Detect and use existing OpenGL context
        try:
            self.ctx = moderngl.create_context()
        except Exception as e:
            print(f"error: failed to create opengl context: {e}")
            pygame.quit()
            sys.exit(1)
        self.ctx.enable(flags=moderngl.DEPTH_TEST | moderngl.CULL_FACE | moderngl.BLEND)
        self.ctx.gc_mode = 'auto'
        # Create an object to help track time
        self.clock = pygame.time.Clock()
        # Set fps max
        pygame.time.set_timer(pygame.USEREVENT, 1000 // self.target_fps)

    def run(self):
        # Query GPU and OpenGL information for debugging
        print("gpu")
        try:
            print(f"  vendor                            : {self.ctx.info.get('GL_VENDOR', 'Unknown')}")  # GPU vendor (e.g., NVIDIA, AMD, Intel)
            print(f"  renderer                          : {self.ctx.info.get('GL_RENDERER', 'Unknown')}")  # GPU model (e.g., GeForce RTX 3080)
            print(f"  opengl version                    : {self.ctx.info.get('GL_VERSION', 'Unknown')}")  # OpenGL version supported
            # Fallback for GL_SHADING_LANGUAGE_VERSION
            try:
                shading_version = self.ctx.info.get('GL_SHADING_LANGUAGE_VERSION', None)
                if shading_version is None:
                    shading_version = glGetString(GL_SHADING_LANGUAGE_VERSION).decode('utf-8') if glGetString(GL_SHADING_LANGUAGE_VERSION) else 'Unknown'
                print(f"  shading language version          : {shading_version}")  # GLSL version
            except Exception as e:
                print(f"error: failed to query shading language version: {e}")
        except Exception as e:
            print(f"error: failed to query gpu info: {e}")

        # Query texture-related limits
        print("texture-related limits")
        try:
            # Maximum number of texture units available across all shader stages
            # According to the OpenGL 4.6 Core Profile Specification (available from the Khronos Group), the minimum value for GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS is 80; and for 3.3 it was 48.
            # Modern GPUs often provide significantly more texture units (e.g., 192 or higher), but the minimum ensures portability across all compliant OpenGL 4.6 implementations.
            max_texture_units = self.ctx.info.get('GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS', 'Unknown')
            print(f"  max combined texture units        : {max_texture_units}")
            # Maximum width/height of a 2D texture
            max_texture_size = self.ctx.info.get('GL_MAX_TEXTURE_SIZE', 'Unknown')
            print(f"  max texture size                  : {max_texture_size}x{max_texture_size} pixels" if max_texture_size != 'Unknown' else "  max texture size                  : Unknown")
            # Maximum number of layers in a texture array
            max_array_layers = self.ctx.info.get('GL_MAX_ARRAY_TEXTURE_LAYERS', 'Unknown')
            print(f"  max texture array layers          : {max_array_layers}")
            # Maximum dimensions of a 3D texture
            max_3d_texture_size = self.ctx.info.get('GL_MAX_3D_TEXTURE_SIZE', 'Unknown')
            print(f"  max 3d texture size               : {max_3d_texture_size}x{max_3d_texture_size}x{max_3d_texture_size}" if max_3d_texture_size != 'Unknown' else "  max 3d texture size               : Unknown")
            # Maximum number of texture image units per shader stage (e.g., fragment shader)
            max_fragment_texture_units = self.ctx.info.get('GL_MAX_TEXTURE_IMAGE_UNITS', 'Unknown')
            print(f"  max fragment shader texture units : {max_fragment_texture_units}")
        except Exception as e:
            print(f"error: failed to query texture-related limits: {e}")

        # Query other useful limits for debugging
        print("other system limitations")
        try:
            # Maximum number of samples for multi-sampling (anti-aliasing)
            max_samples = self.ctx.info.get('GL_MAX_SAMPLES', 'Unknown')
            print(f"  max samples (multi-sampling)      : {max_samples}")
            # Maximum size of a viewport
            max_viewport_dims = self.ctx.info.get('GL_MAX_VIEWPORT_DIMS', ('Unknown', 'Unknown'))
            print(f"  max viewport dimensions           : {max_viewport_dims[0]}x{max_viewport_dims[1]}" if max_viewport_dims[0] != 'Unknown' else "  max viewport dimensions           : Unknown")
            # Maximum number of uniform buffer bindings
            max_uniform_buffer_bindings = self.ctx.info.get('GL_MAX_UNIFORM_BUFFER_BUFFER_BINDINGS', 'Unknown')
            print(f"  max uniform buffer bindings       : {max_uniform_buffer_bindings}")
            # Maximum size of a uniform buffer
            max_uniform_block_size = self.ctx.info.get('GL_MAX_UNIFORM_BLOCK_SIZE', 'Unknown')
            print(f"  max uniform block size            : {max_uniform_block_size} bytes" if max_uniform_block_size != 'Unknown' else "  max uniform block size            : Unknown")
            # Maximum number of vertex attributes
            max_vertex_attribs = self.ctx.info.get('GL_MAX_VERTEX_ATTRIBS', 'Unknown')
            print(f"  max vertex attributes             : {max_vertex_attribs}")
        except Exception as e:
            print(f"error: failed to query other system limits: {e}")

        # Create a sample texture for testing
        print("creating a sample texture")
        try:
            texture = self.ctx.texture(size=(512, 512), components=4, data=None)  # RGBA texture
            print(f"  created texture with ID {texture.glo}")
            # Bind the texture to a texture unit for testing
            texture.use(location=0)
            print(f"  texture bound to unit 0")
            # Release the texture
            texture.release()
            print(f"  texture released")
        except Exception as e:
            print(f"error: failed to create or use texture: {e}")

        # Clean up context and pygame
        self.ctx.release()
        print("moderngl context released")
        pygame.quit()


if __name__ == '__main__':
    app = Engine()
    app.run()
