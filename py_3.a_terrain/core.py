import numpy
import moderngl
import glm
import pygame
import math

mat_4 = glm.mat4(1)


def generate_vertex_data(vertices, indices):
    data = [vertices[ind] for triangle in indices for ind in triangle]
    return numpy.array(data, dtype='f4')


def delta_ab(a, b):
    return glm.vec3(b[0] - a[0], b[1] - a[1], b[2] - a[2])


def dot_product(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def angle_between_vectors(a, b):
    # unit_vector_of_ground = glm.vec3(0, 1, 0)
    return math.acos(dot_product(a, b))


def uniform_points_in_3d_triangle(p1, p2, p3, n):
    points = []
    for i in range(n):
        for j in range(n - i):
            k = n - i - j
            x = (i * p1[0] + j * p2[0] + k * p3[0]) / n
            y = (i * p1[1] + j * p2[1] + k * p3[1]) / n
            z = (i * p1[2] + j * p2[2] + k * p3[2]) / n
            points.append((x, y, z))
    return points


class Camera:
    yaw = -90
    pitch = 0
    fov = 50  # Degrees
    near = 0.1
    far = 100
    sensitivity = 0.1
    speed = 0.005

    position = None
    up = glm.vec3(0, 1, 0)
    right = glm.vec3(1, 0, 0)
    forward = glm.vec3(0, 0, -1)

    def __init__(self, app, position=(0, 0, 0), yaw=yaw, pitch=pitch,
                 fov=fov, near=near, far=far, sensitivity=sensitivity):
        self.app = app
        self.position = glm.vec3(position)
        self.yaw = yaw
        self.pitch = pitch
        self.fov = fov
        self.near = near
        self.far = far
        self.sensitivity = sensitivity
        # View matrix
        self.m_view = self.get_view_matrix()
        # Aspect ratio and Projection matrix
        self.set_aspect_and_projection()
        # Key bindings
        self.key_bindings = {
            "forward": pygame.K_w,
            "backward": pygame.K_s,
            "left": pygame.K_a,
            "right": pygame.K_d,
            "up": pygame.K_SPACE,
            "down": pygame.K_LCTRL,
        }

    def set_aspect_and_projection(self):
        self.aspect_ratio = self.app.win_size[0] / self.app.win_size[1]
        self.m_proj = self.get_projection_matrix()

    def rotate(self):
        old_yaw, old_pitch = self.yaw, self.pitch
        rel_x, rel_y = pygame.mouse.get_rel()
        self.yaw += rel_x * self.sensitivity
        self.pitch -= rel_y * self.sensitivity
        self.pitch = max(-89, min(89, self.pitch))
        if old_yaw != self.yaw or old_pitch != self.pitch:
            self.app.scene.moved = True

    def update_camera_vectors(self):
        yaw, pitch = glm.radians(self.yaw), glm.radians(self.pitch)
        self.forward.x = glm.cos(yaw) * glm.cos(pitch)
        self.forward.y = glm.sin(pitch)
        self.forward.z = glm.sin(yaw) * glm.cos(pitch)
        self.forward = glm.normalize(self.forward)
        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))

    def update(self):
        self.move()
        self.rotate()
        self.update_camera_vectors()
        self.m_view = self.get_view_matrix()

    def move(self):
        old_x, old_y, old_z = self.position.xyz
        self.velocity = self.speed * self.app.raw_delta_time
        keys = pygame.key.get_pressed()
        if keys[self.key_bindings["forward"]]:
            self.position += self.forward * self.velocity
        if keys[self.key_bindings["backward"]]:
            self.position -= self.forward * self.velocity
        if keys[self.key_bindings["left"]]:
            self.position -= self.right * self.velocity
        if keys[self.key_bindings["right"]]:
            self.position += self.right * self.velocity
        if keys[self.key_bindings["up"]]:
            self.position += self.up * self.velocity
        if keys[self.key_bindings["down"]]:
            self.position -= self.up * self.velocity
        if self.position.x != old_x or self.position.y != old_y or self.position.z != old_z:
            self.app.scene.moved = True

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.position + self.forward, self.up)

    def get_projection_matrix(self):
        return glm.perspective(glm.radians(self.fov), self.aspect_ratio, self.near, self.far)


class PointLight:
    def __init__(self, position=(10, 10, -10), direction=(0, 0, 0), color=(1, 1, 1), strength=1.0):
        self.position = glm.vec3(position)
        self.direction = glm.vec3(direction)
        self.color = glm.vec3(color)
        self.strength = strength

    def rotate(self, time):
        self.position = glm.rotateY(self.position, time)


class DirectionalLight:
    def __init__(self, position=(50, 50, 50), direction=(0, 0, 0),
                 color=(1, 1, 1), strength=1.0):
        self.position = glm.vec3(position)
        self.direction = glm.vec3(direction)
        self.color = glm.vec3(color)
        self.strength = strength
        self.m_view_light = self.get_view_matrix()

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.direction, glm.vec3(0, 1, 0))

    def rotate(self, time):
        self.position = glm.rotateY(self.position, time)
        self.m_view_light = self.get_view_matrix()


class SpotLight:
    def __init__(self, position=(10, 10, -10), direction=(0, 0, 0),
                 color=(1, 1, 1), strength=1.0,
                 cutoff: float = 12.5, softness: float = 25.5):
        self.position = glm.vec3(position)
        self.direction = glm.vec3(direction)
        self.color = glm.vec3(color)
        self.strength = strength
        self.cutoff = glm.cos(glm.radians(cutoff))
        self.softness = glm.cos(glm.radians(softness))

    def rotate(self, time):
        self.position = glm.rotateY(self.position, time)


class CameraSpotLight:
    camera = None

    def __init__(self, camera=None, color=(1, 1, 1), strength=1.0,
                 cutoff: float = 12.5, softness: float = 25.5):
        self.camera = camera
        self.position = glm.vec3(camera.position)
        self.direction = self.camera.forward
        self.color = glm.vec3(color)
        self.strength = strength
        self.cutoff = glm.cos(glm.radians(cutoff))
        self.softness = glm.cos(glm.radians(softness))

    def update(self):
        self.position = self.camera.position
        self.direction = self.camera.forward


class Shader():
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.programs = []
        self.programs_count = -1
        self.programs_map = {}

    def get_shader(self, shader_name, geometry=False):
        if shader_name in self.programs_map:
            # print(f"Reuse shader: {shader_name} at index: {self.programs_map[shader_name]}")
            return self.programs[self.programs_map[shader_name]]

        with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.vert', 'r') as f:
            vertex_shader_source = f.read()
        with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.frag', 'r') as f:
            fragment_shader_source = f.read()

        if geometry is True:
            with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.geom', 'r') as f:
                geometry_shader_source = f.read()
            shader_program = self.ctx.program(
                vertex_shader=vertex_shader_source,
                fragment_shader=fragment_shader_source,
                geometry_shader=geometry_shader_source,
            )
        else:
            shader_program = self.ctx.program(
                vertex_shader=vertex_shader_source,
                fragment_shader=fragment_shader_source,
            )
        self.programs_count += 1
        self.programs_map[shader_name] = self.programs_count
        self.programs.append(shader_program)
        print(f"loaded shader: {shader_name} at index: {self.programs_count}")
        return shader_program

    def destroy(self):
        for program in self.programs:
            program.release()


class Texture:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.textures = []
        self.texture_count = -1
        self.texture_map = {}

    def get_texture(self, path):
        if path in self.texture_map:
            return self.texture_map[path]

        texture = pygame.image.load(path).convert()
        texture = pygame.transform.flip(texture, flip_x=False, flip_y=True)  # Flip Pygame -> OpenGL
        texture = self.ctx.texture(size=texture.get_size(), components=3,
                                   data=pygame.image.tostring(texture, 'RGB'))
        # Mipmaps
        texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        texture.min_lod = -1000
        texture.max_lod = 1000
        # Set levels of mipmaps
        texture.build_mipmaps(base=0, max_level=1000)
        # AF
        texture.anisotropy = 32.0
        # Add to list
        self.texture_count += 1
        self.texture_map[path] = self.texture_count
        self.textures.append(texture)
        print(f"loaded texture: {path} at index: {self.texture_count}")
        return self.texture_count

    def get_depth_texture(self, size, name='depth_texture', disable_repeat=False):
        if name in self.texture_map:
            return self.texture_map[name]
        # Depth texture is slower than a depth buffer,
        # but you can sample it later on
        depth_texture = self.ctx.depth_texture(size=size)
        # Remove repetition
        if disable_repeat:
            depth_texture.repeat_x = False
            depth_texture.repeat_y = False
        # Add to list
        self.texture_count += 1
        self.texture_map[name] = self.texture_count
        self.textures.append(depth_texture)
        print(f"loaded depth texture: {name} at index: {self.texture_count}")
        return self.texture_count

    def get_alpha_texture(self, path):
        if path in self.texture_map:
            return self.texture_map[path]
        texture = pygame.image.load(path).convert_alpha()
        texture = pygame.transform.flip(texture, flip_x=False, flip_y=True)  # Flip Pygame -> OpenGL
        texture = self.ctx.texture(size=texture.get_size(), components=4,
                                   data=pygame.image.tostring(texture, 'RGBA'))
        # Mipmaps
        texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        texture.min_lod = -1000
        texture.max_lod = 1000
        # Set levels of mipmaps
        texture.build_mipmaps(base=0, max_level=1000)
        # AF
        texture.anisotropy = 32.0
        # Add to list
        self.texture_count += 1
        self.texture_map[path] = self.texture_count
        self.textures.append(texture)
        print(f"loaded texture: {path} at index: {self.texture_count}")
        return self.texture_count

    def get_basic_texture(self, path):
        'Get an RGB texture with no filtering'
        if path in self.texture_map:
            return self.texture_map[path]
        texture = pygame.image.load(path).convert()
        texture = pygame.transform.flip(texture, flip_x=False, flip_y=True)  # Flip Pygame -> OpenGL
        texture = self.ctx.texture(size=texture.get_size(), components=3,
                                   data=pygame.image.tostring(texture, 'RGB'))
        # Add to list
        self.texture_count += 1
        self.texture_map[path] = self.texture_count
        self.textures.append(texture)
        return self.texture_count

    def get_image_data(self, path):
        '''Return image data and size for in image file.'''
        image = pygame.image.load(path)
        image = pygame.transform.flip(image, flip_x=False, flip_y=True)
        width, height = image.get_rect().size
        image = pygame.surfarray.array3d(image)  # Convert image to numpy array
        return image, width, height

    def random_quad(self):
        '''Return random texture coordinates for a quad.'''
        rand_int = numpy.random.randint(4)
        texture_coords = []
        if rand_int == 0:
            texture_coords.append((0, 0))
            texture_coords.append((1, 0))
            texture_coords.append((1, 1))
            texture_coords.append((0, 1))
        elif rand_int == 1:
            texture_coords.append((1, 0))
            texture_coords.append((1, 1))
            texture_coords.append((0, 1))
            texture_coords.append((0, 0))
        elif rand_int == 2:
            texture_coords.append((1, 1))
            texture_coords.append((0, 1))
            texture_coords.append((0, 0))
            texture_coords.append((1, 0))
        elif rand_int == 3:
            texture_coords.append((0, 1))
            texture_coords.append((0, 0))
            texture_coords.append((1, 0))
            texture_coords.append((1, 1))
        return texture_coords

    def get_texture_cube(self, path, ext='png'):
        faces = ['right', 'left', 'top', 'bottom'] + ['front', 'back'][::-1]
        textures = []
        for face in faces:
            texture = pygame.image.load(f'{path}/{face}.{ext}').convert()
            if face in ['right', 'left', 'front', 'back']:
                texture = pygame.transform.flip(texture, flip_x=True, flip_y=False)
            else:
                texture = pygame.transform.flip(texture, flip_x=False, flip_y=True)
            textures.append(texture)
        size = textures[0].get_size()
        texture_cube = self.ctx.texture_cube(size=size, components=3, data=None)
        for i in range(6):
            texture_data = pygame.image.tostring(textures[i], 'RGB')
            texture_cube.write(face=i, data=texture_data)
        # return texture_cube
        # Add to list
        self.texture_count += 1
        self.texture_map[path] = self.texture_count
        self.textures.append(texture_cube)
        return self.texture_count

    def destroy(self):
        for texture in self.textures:
            texture.release()


class Shadow():
    def __init__(self, app, name="depth_texture", depth_size=[4096, 4096]):
        self.app = app
        self.ctx = app.ctx

        print(f"shadow depth texture: {depth_size}")
        # Assuming the depth buffer is a single float (4 bytes)
        # for 4096x it is 16,777,216 pixels × 4 bytes/pixel = 67,108,864 bytes
        # or 67,108,864 bytes ÷ (1024 × 1024) = 64 MB.

        # Using a texture here not a renderbuffer because we pass it to the shader
        self.depth_tex_id = self.app.texture.get_depth_texture(depth_size, name, disable_repeat=True)
        self.depth_texture = self.app.texture.textures[self.depth_tex_id]
        # self.depth_buffer = self.ctx.depth_renderbuffer(size=depth_size)

        self.depth_fbo = self.ctx.framebuffer(depth_attachment=self.depth_texture)
        # self.depth_fbo = self.ctx.framebuffer(depth_attachment=self.depth_buffer)

        # Shadow depth map
        self.shader_program = app.shader.get_shader("default")
        self.shader_program['shadow_map_tex'] = self.depth_tex_id
        self.app.texture.textures[self.depth_tex_id].use(location=self.depth_tex_id)

    def destroy(self):
        self.depth_fbo.release()
        self.depth_texture.release()


class Prototype:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.objects = []
        self.object_count = -1
        self.object_map = {}

    def get_object(self, name):
        if name in self.object_map:
            return self.objects[self.object_map[name]]

        if name == "cube" or name == "floor":
            base_object = PrototypeCube(
                app=self.app, shader_name='default', shadow_name='shadow'
            )
        elif name == "light_source":
            base_object = PrototypeLightSource(
                app=self.app, light_name='light'
            )
        elif name == "grass":
            base_object = PrototypeGrass(app=self.app)  # Not 100% settled on this design
        elif name == "ground":
            base_object = PrototypeGround(app=self.app)

        # Add to list
        self.object_count += 1
        self.object_map[name] = self.object_count
        self.objects.append(base_object)
        print(f"loaded proto-object: {name} at index: {self.object_count}")
        return base_object

    def common_render_update(self):
        # Default shader #
        shader_program = self.app.shader.get_shader('default')
        # Resolution
        # shader_program['u_resolution'].write(glm.vec2(self.app.win_size))

        # Position
        shader_program['cam_pos'].write(self.app.camera.position)
        shader_program['m_proj'].write(self.app.camera.m_proj)
        shader_program['m_view'].write(self.app.camera.m_view)

        # Send lights into uniform array of Light struct
        shader_program['num_lights'].value = len(self.app.lights)
        for i, light in enumerate(self.app.lights):
            shader_program[f'lights[{i}].position'].value = light.position
            shader_program[f'lights[{i}].color'].value = light.color
            shader_program[f'lights[{i}].strength'].value = light.strength

        # Send global_light from self.global_light
        shader_program['m_view_global_light'].write(self.app.global_light.m_view_light)
        shader_program['global_light.position'].value = self.app.global_light.position
        shader_program['global_light.direction'].value = self.app.global_light.direction
        shader_program['global_light.color'].value = self.app.global_light.color
        shader_program['global_light.strength'].value = self.app.global_light.strength

        # Send flash_light from self.flash_light
        shader_program['flash_light.position'].value = self.app.flash_light.position
        shader_program['flash_light.color'].value = self.app.flash_light.color
        shader_program['flash_light.strength'].value = self.app.flash_light.strength
        shader_program['flash_light.cutoff'].value = self.app.flash_light.cutoff
        shader_program['flash_light.direction'].value = self.app.flash_light.direction
        shader_program['flash_light.softness'].value = self.app.flash_light.softness

        # Shadow Shader #
        shadow_program = self.app.shader.get_shader('shadow')
        shadow_program['m_proj'].write(self.app.camera.m_proj)
        shadow_program['m_view_light'].write(self.app.global_light.m_view_light)

        # Debug
        shader_program["texture_blend"].value = self.app.texture_blend
        shader_program["local_light_blend"].value = self.app.local_light

        # Debug Light
        light_program = self.app.shader.get_shader('light')
        light_program['m_proj'].write(self.app.camera.m_proj)
        light_program['m_view'].write(self.app.camera.m_view)

        # Grass shader #
        grass_program = self.app.shader.get_shader('grass')
        # Position
        grass_program['m_proj'].write(self.app.camera.m_proj)
        grass_program['m_view'].write(self.app.camera.m_view)
        grass_program['cam_pos'].write(self.app.camera.position)

        # Send lights into uniform array of Light struct
        grass_program['num_lights'].value = len(self.app.lights)
        for i, light in enumerate(self.app.lights):
            grass_program[f'lights[{i}].position'].value = light.position
            grass_program[f'lights[{i}].color'].value = light.color
            grass_program[f'lights[{i}].strength'].value = light.strength

        # Send global_light from self.global_light
        grass_program['m_view_global_light'].write(self.app.global_light.m_view_light)
        grass_program['global_light.position'].value = self.app.global_light.position
        grass_program['global_light.direction'].value = self.app.global_light.direction
        grass_program['global_light.color'].value = self.app.global_light.color
        grass_program['global_light.strength'].value = self.app.global_light.strength

        # Send flash_light from self.flash_light
        grass_program['flash_light.position'].value = self.app.flash_light.position
        grass_program['flash_light.color'].value = self.app.flash_light.color
        grass_program['flash_light.strength'].value = self.app.flash_light.strength
        grass_program['flash_light.cutoff'].value = self.app.flash_light.cutoff
        grass_program['flash_light.direction'].value = self.app.flash_light.direction
        grass_program['flash_light.softness'].value = self.app.flash_light.softness

        # Debug
        grass_program["texture_blend"].value = self.app.texture_blend
        grass_program["local_light_blend"].value = self.app.local_light

        # Ground shader #
        ground_program = self.app.shader.get_shader('ground')
        # Position
        ground_program['cam_pos'].write(self.app.camera.position)
        ground_program['m_proj'].write(self.app.camera.m_proj)
        ground_program['m_view'].write(self.app.camera.m_view)

        # Send lights into uniform array of Light struct
        ground_program['num_lights'].value = len(self.app.lights)
        for i, light in enumerate(self.app.lights):
            ground_program[f'lights[{i}].position'].value = light.position
            ground_program[f'lights[{i}].color'].value = light.color
            ground_program[f'lights[{i}].strength'].value = light.strength

        # Send global_light from self.global_light
        ground_program['m_view_global_light'].write(self.app.global_light.m_view_light)
        ground_program['global_light.position'].value = self.app.global_light.position
        ground_program['global_light.direction'].value = self.app.global_light.direction
        ground_program['global_light.color'].value = self.app.global_light.color
        ground_program['global_light.strength'].value = self.app.global_light.strength

        # Send flash_light from self.flash_light
        ground_program['flash_light.position'].value = self.app.flash_light.position
        ground_program['flash_light.color'].value = self.app.flash_light.color
        ground_program['flash_light.strength'].value = self.app.flash_light.strength
        ground_program['flash_light.cutoff'].value = self.app.flash_light.cutoff
        ground_program['flash_light.direction'].value = self.app.flash_light.direction
        ground_program['flash_light.softness'].value = self.app.flash_light.softness

        # Debug
        ground_program["texture_blend"].value = self.app.texture_blend
        ground_program["local_light_blend"].value = self.app.local_light

    def destroy(self):
        for obj in self.objects:
            obj.destroy()


class PrototypeCube:
    def __init__(self, app,
                 shader_name: str = 'default',
                 shadow_name: str = 'shadow'):
        self.app = app
        self.ctx = app.ctx
        self.vbo = self.get_vbo()
        self.shader_program = self.app.shader.get_shader(shader_name)
        self.vao = self.get_vao(self.vbo, self.shader_program)
        self.shadow_program = self.app.shader.get_shader(shadow_name)
        self.shadow_vao = self.get_shadow_vao(self.vbo, self.shadow_program)

    def destroy(self):
        self.vao.release()
        self.shadow_vao.release()
        self.vbo.release()

    def get_vao(self, vbo, shader_program):
        vao = self.ctx.vertex_array(shader_program, [
            (vbo, '2f 3f 3f', 'in_texcoord_0', 'in_position', 'in_normal'),
        ])
        return vao

    def get_shadow_vao(self, vbo, shadow_program):
        vao = self.ctx.vertex_array(shadow_program, [
            (vbo, '2f 3f 3f', 'in_texcoord_0', 'in_position', 'in_normal'),
        ], skip_errors=True)
        # Temporary fix for the issue with the shadow program because we are not using texture coordinates
        # So we set skip_errors=True to ignore the missing in_texcoord_0 attribute
        return vao

    def get_vertex_data(self):
        # Vertices
        vertices = [
            (-1, -1, 1),
            (1, -1, 1),
            (1, 1, 1),
            (-1, 1, 1),
            (-1, 1, -1),
            (-1, -1, -1),
            (1, -1, -1),
            (1, 1, -1)
        ]
        indices = [
            (0, 2, 3), (0, 1, 2),
            (1, 7, 2), (1, 6, 7),
            (6, 5, 4), (4, 7, 6),
            (3, 4, 5), (3, 5, 0),
            (3, 7, 4), (3, 2, 7),
            (0, 6, 1), (0, 5, 6),
        ]
        vertex_data = generate_vertex_data(vertices, indices)

        # Texture coordinates
        texture_coords = [(0, 0), (1, 0), (1, 1), (0, 1)]
        texture_indices = [(0, 2, 3), (0, 1, 2),
                           (0, 2, 3), (0, 1, 2),
                           (0, 1, 2), (2, 3, 0),
                           (2, 3, 0), (2, 0, 1),
                           (0, 2, 3), (0, 1, 2),
                           (3, 1, 2), (3, 0, 1)]
        texture_coord_data = generate_vertex_data(texture_coords, texture_indices)
        vertex_data = numpy.hstack([texture_coord_data, vertex_data])

        # Normals
        normals = [
            (0, 0, 1) * 6,
            (1, 0, 0) * 6,
            (0, 0, -1) * 6,
            (-1, 0, 0) * 6,
            (0, 1, 0) * 6,
            (0, -1, 0) * 6,
        ]
        normals = numpy.array(normals, dtype='f4').reshape(int(len(normals * 6)), 3)
        vertex_data = numpy.hstack([vertex_data, normals])

        return numpy.array(vertex_data, dtype='f4')

    def get_vbo(self):
        return self.ctx.buffer(self.get_vertex_data())


class PrototypeLightSource():

    def __init__(self, app, light_name: str = 'light'):
        self.app = app
        self.ctx = app.ctx
        self.vbo = self.get_vbo()
        self.light_program = self.app.shader.get_shader(light_name)
        self.vao = self.get_vao(self.vbo, self.light_program)

    def destroy(self):
        self.vao.release()
        self.vbo.release()

    def get_vao(self, vbo, shader_program):
        vao = self.ctx.vertex_array(shader_program, [
            (vbo, '3f', 'in_position'),
        ])
        return vao

    def get_vertex_data(self):
        vertices = [
            (-1, -1, 1),
            (1, -1, 1),
            (1, 1, 1),
            (-1, 1, 1),
            (-1, 1, -1),
            (-1, -1, -1),
            (1, -1, -1),
            (1, 1, -1)
        ]
        indices = [
            (0, 2, 3), (0, 1, 2),
            (1, 7, 2), (1, 6, 7),
            (6, 5, 4), (4, 7, 6),
            (3, 4, 5), (3, 5, 0),
            (3, 7, 4), (3, 2, 7),
            (0, 6, 1), (0, 5, 6),
        ]
        vertex_data = generate_vertex_data(vertices, indices)
        return numpy.array(vertex_data, dtype='f4')

    def get_vbo(self):
        return self.ctx.buffer(self.get_vertex_data())


def generate_vertex_data(vertices, indices):
    data = [vertices[ind] for triangle in indices for ind in triangle]
    return numpy.array(data, dtype='f4')


class Cube:
    def __init__(self, app, albedo=(1.0, 1.0, 1.0), roughness=0.75, metallic=0.25,
                 position=(0, 0, 0), scale=(0.5, 0.5, 0.5),
                 texture: str = 'crate_0', name: str = "cube", can_update=True):
        self.app = app
        self.ctx = app.ctx
        self.scale = scale
        self.pos = glm.vec3(position)
        self.position = glm.mat4(glm.translate(mat_4, self.pos))
        self.position = glm.scale(self.position, glm.vec3(scale))
        self.can_update = can_update
        self.can_render = True
        self.has_shadow = True

        self.albedo = glm.vec3(albedo)
        self.roughness = roughness
        self.metallic = metallic

        this_object = self.app.prototype.get_object(name)
        self.vao = this_object.vao
        self.shadow_vao = this_object.shadow_vao
        self.shader_program = this_object.shader_program
        self.shadow_program = this_object.shadow_program

        self.tex_id = app.texture.get_texture(path=f'../textures/{texture}.png')
        self.m_model = self.position

    def update(self):
        self.m_model = glm.rotate(self.position, self.app.time, glm.vec3(0, 1, 0))

    def render(self):
        # Texture
        self.shader_program['u_tex_albedo'] = self.tex_id
        self.app.texture.textures[self.tex_id].use(location=self.tex_id)
        # Position
        self.shader_program['m_model'].write(self.m_model)
        # Material
        self.shader_program['material.a'].value = self.albedo
        self.shader_program['material.d'].value = self.roughness
        self.shader_program['material.s'].value = self.metallic
        # Render
        self.vao.render()

    def render_shadow(self):
        self.shadow_program['m_model'].write(self.m_model)
        self.shadow_vao.render()


class Floor(Cube):
    def __init__(self, app, albedo=(1.0, 1.0, 1.0), roughness=0.9, metallic=0.2,
                 position=(0, 0, 0), scale=(1, 0.1, 1), texture: str = 'ground',
                 can_update=False):
        super().__init__(app, albedo, roughness, metallic, position,
                         scale, texture, name="floor", can_update=can_update)

    def update(self):
        self.m_model = self.position


class LightSource:
    def __init__(self, app, light_source, name: str = "light_source"):
        self.app = app
        self.ctx = app.ctx

        self.light_source = light_source
        self.scale = light_source.strength * 0.05

        this_object = self.app.prototype.get_object(name)
        self.vao = this_object.vao
        self.light_program = this_object.light_program

    def render(self):
        self.m_model = glm.mat4(glm.translate(mat_4, self.light_source.position))
        self.m_model = glm.scale(self.m_model, glm.vec3(self.scale))
        # Position
        self.light_program['m_model'].write(self.m_model)
        self.light_program['light.color'].value = self.light_source.color
        # Render
        self.vao.render()


class TerrainChunk:

    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.chunks = []
        self.chunks_count = -1
        self.chunks_map = {}

    def add_chunk(self, app, name: int, position=(0, 0, 0), width=40, depth=40, max_height=100.0,
                  height_map_path="height_map", scale=1.0, rounding_factor=6):
        # Note this is still an old method where I'm loading a file and creating the terrain from it,
        # which isn't that useful for a chunked terrain system -- this needs to be moved to the scene builder
        # where we can chunk up the map area and create each chunk ready to go in the scene objects.
        if name in self.chunks_map:
            return self.chunks[self.chunks_map[name]]

        terrain_chunk = Terrain(app=app, position=position, width=width, depth=depth,
                                max_height=max_height, height_map_path=height_map_path,
                                scale=scale, rounding_factor=rounding_factor)

        self.chunks_count += 1
        self.chunks_map[name] = self.chunks_count
        self.chunks.append(terrain_chunk)
        print(f"loaded terrain chunk: {name} at index: {self.chunks_count}")
        return terrain_chunk


class Terrain:

    def __init__(self, app, position=(0, 0, 0), width=40, depth=40, max_height=100.0,
                 height_map_path="height_map", scale=1.0, rounding_factor=6):
        self.app = app
        self.ctx = app.ctx
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))
        self.rounding_factor = rounding_factor
        self.max_height = max_height

        self.scale = scale
        self.half_scale = self.scale * 0.5
        terrain_image_path = f'../textures/{height_map_path}.png'
        self.height_map, self.height_map_w, self.height_map_d = app.texture.get_image_data(terrain_image_path)

        # Temporary limit for terrain size
        if width != self.height_map_w and width <= self.height_map_w:
            self.height_map_w = width
        if depth != self. height_map_d and depth <= self.height_map_d:
            self.height_map_d = depth
        self.half_width = math.floor(self.height_map_w / 2 * self.scale)
        self.half_depth = math.floor(self.height_map_d / 2 * self.scale)

        # Get value at 0,0 i.e. half_width, half_depth; use this to place the terrain under the camera
        self.base_height = self.lookup_height(self.half_width, self.half_depth) + 1
        self.vertices = self.get_vertices(self.height_map_w, self.height_map_d, self.max_height,
                                          self.base_height, self.height_map,
                                          self.half_width, self.half_depth, self.rounding_factor)
        self.vertex_data = self.generate_vertex_data(self.vertices)

    def lookup_height(self, x, z):
        height = round(self.height_map[z][x][0] / 255 * self.max_height, self.rounding_factor)
        return height

    def get_vertices(self, height_map_w: int, height_map_d: int, max_h: float, offset_h: int,
                     height_map: list, half_width: int, half_depth: int, r_factor=5):
        vertices = []
        offset_w = half_width * self.scale
        offset_d = half_depth * self.scale
        for z in range(1, height_map_d):
            for x in range(1, height_map_w):
                y1 = round((height_map[z][x-1][0] / 255) * max_h - offset_h, r_factor)
                y2 = round((height_map[z][x][0] / 255) * max_h - offset_h, r_factor)
                y3 = round((height_map[z-1][x][0] / 255) * max_h - offset_h, r_factor)
                y4 = round((height_map[z-1][x-1][0] / 255) * max_h - offset_h, r_factor)
                x_pos = x * self.scale
                z_pos = z * self.scale
                vertices.append((x_pos-self.half_scale-offset_w, y1, z_pos+self.half_scale-offset_d))
                vertices.append((x_pos+self.half_scale-offset_w, y2, z_pos+self.half_scale-offset_d))
                vertices.append((x_pos+self.half_scale-offset_w, y3, z_pos-self.half_scale-offset_d))
                vertices.append((x_pos-self.half_scale-offset_w, y4, z_pos-self.half_scale-offset_d))
        return vertices

    def generate_vertex_data(self, vertices):
        grass_density = 10
        grass_vertices = []
        indices = []
        texture_coords = []
        texture_indices = []
        normals = []
        for i in range(0, len(vertices) - 1, 4):
            v1 = vertices[i]
            v2 = vertices[i + 1]
            v3 = vertices[i + 2]
            v4 = vertices[i + 3]
            indices.append((i, i + 2, i + 3))  # Triangle 1
            indices.append((i, i + 1, i + 2))  # Triangle 2
            texture_coords.extend(self.app.texture.random_quad())
            texture_indices.append((0, 2, 3))
            texture_indices.append((0, 1, 2))
            # Normals of the terrain triangles
            normal_1 = glm.normalize(glm.cross(delta_ab(v1, v3), delta_ab(v1, v4)))
            new_normals = [[normal_1] * 3]
            normal_2 = glm.normalize(glm.cross(delta_ab(v1, v2), delta_ab(v1, v3)))
            new_normals.extend([[normal_2] * 3])
            normals.append(new_normals)
            # Add grass blade points along each triangle of this piece
            grass_vertices.append(uniform_points_in_3d_triangle(v1, v2, v3, grass_density))
            grass_vertices.append(uniform_points_in_3d_triangle(v1, v3, v4, grass_density))
        self.vertices_mesh = numpy.array(grass_vertices, dtype='f4')

        # Pack vertex data
        texture_coord_data = generate_vertex_data(texture_coords, texture_indices)
        vertex_data = generate_vertex_data(vertices, indices)
        vertex_data = numpy.hstack([texture_coord_data, vertex_data])
        normals = numpy.array(normals, dtype='f4').reshape(int(len(normals * 6)), 3)
        vertex_data = numpy.hstack([vertex_data, normals])
        return numpy.array(vertex_data, dtype='f4')


class PrototypeGround():
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.shader_program = app.shader.get_shader('ground')
        self.shadow_program = app.shader.get_shader("shadow")

    def build(self, terrain_chunk: int = None):
        self.terrain_chunk = terrain_chunk
        self.vbo = self.get_vbo()
        self.vao = self.get_vao()
        self.shadow_vao = self.get_shadow_vao()

    def destroy(self):
        self.shader_program.release()
        self.vao.release()
        self.shadow_vao.release()
        self.vbo.release()

    def get_vao(self):
        vao = self.ctx.vertex_array(self.shader_program, [
            (self.vbo, '2f 3f 3f', 'in_texcoord_0', 'in_position', 'in_normal'),
        ])
        return vao

    def get_shadow_vao(self):
        vao = self.ctx.vertex_array(self.shadow_program, [
            (self.vbo, '2f 3f 3f', 'in_texcoord_0', 'in_position', 'in_normal'),
        ], skip_errors=True)
        # Temporary fix for the issue with the shadow program because we are not using texture coordinates
        # So we set skip_errors=True to ignore the missing in_texcoord_0 attribute
        return vao

    def get_vbo(self):
        return self.ctx.buffer(self.terrain_chunk.vertex_data)

    def render_shadow(self):
        self.shadow_program['m_model'].write(self.position)
        self.shadow_vao.render(moderngl.TRIANGLES)


class Ground():
    def __init__(self, app, position=(0, 0, 0), texture: str = 'dirt',
                 terrain_chunk: Terrain = None,
                 albedo=(1.0, 1.0, 1.0), roughness=0.75, metallic=0.25):
        self.app = app
        self.ctx = app.ctx
        self.terrain_chunk = terrain_chunk
        self.pos = glm.vec3(position)
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))
        self.m_model = self.position
        self.can_update = True
        self.can_render = True
        self.has_shadow = False  # Not sure if this is rendering completely correctly -- return to this.

        self.albedo = glm.vec3(albedo)
        self.roughness = roughness
        self.metallic = metallic

        this_object = self.app.prototype.get_object("ground")
        this_object.build(terrain_chunk)
        self.vao = this_object.vao
        self.shader_program = this_object.shader_program

        self.tex_id = app.texture.get_texture(path=f'../textures/{texture}.png')

    def update(self):
        self.shader_program['m_view'].write(self.app.camera.m_view)

    def render(self):
        # Texture
        self.shader_program['u_tex_albedo'] = self.tex_id
        self.app.texture.textures[self.tex_id].use(location=self.tex_id)

        # Position
        self.shader_program['m_model'].write(self.m_model)

        # Material
        self.shader_program['material.a'].value = self.albedo
        self.shader_program['material.d'].value = self.roughness
        self.shader_program['material.s'].value = self.metallic

        self.vao.render(moderngl.TRIANGLES)

    def render_shadow(self):
        self.shadow_program['m_model'].write(self.position)
        self.shadow_vao.render(moderngl.TRIANGLES)


class PrototypeGrass:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.shader_program = app.shader.get_shader('grass', geometry=True)
        self.shadow_program = app.shader.get_shader("shadow")

    def build(self, terrain_chunk: int = None):
        self.terrain_chunk = terrain_chunk
        self.vbo = self.get_vbo()
        self.vao = self.get_vao()
        self.shadow_vao = self.get_shadow_vao()

    def destroy(self):
        self.shader_program.release()
        self.vao.release()
        self.shadow_vao.release()
        self.vbo.release()

    def get_vao(self):
        vao = self.ctx.vertex_array(self.shader_program, [
            (self.vbo, '3f', 'in_position'),
        ])
        return vao

    def get_shadow_vao(self):
        vao = self.ctx.vertex_array(self.shadow_program, [
            (self.vbo, '3f', 'in_position'),
        ], skip_errors=True)
        # Temporary fix for the issue with the shadow program because we are not using texture coordinates
        # So we set skip_errors=True to ignore the missing in_texcoord_0 attribute
        return vao

    def get_vbo(self):
        return self.ctx.buffer(self.terrain_chunk.vertices_mesh)


class Grass:
    def __init__(self, app, position=(0, 0, 0), texture: str = 'grass_0',
                 terrain_chunk: Terrain = None, albedo=(1.0, 1.0, 1.0), roughness=0.6, metallic=0.1):
        self.app = app
        self.ctx = app.ctx
        self.pos = glm.vec3(position)
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))
        self.m_model = self.position
        self.can_update = True
        self.can_render = True
        self.has_shadow = False  # To correctly cast grass shadows from the billboards into the shadow map..
        # We need to create a new shadow shader just for billboards, which uses a geom shader.
        # I will add this soon.

        self.albedo = glm.vec3(albedo)
        self.roughness = roughness
        self.metallic = metallic

        this_object = self.app.prototype.get_object("grass")
        this_object.build(terrain_chunk)
        self.vao = this_object.vao
        self.shader_program = this_object.shader_program

        self.tex_id = app.texture.get_alpha_texture(path=f'../textures/{texture}.png')
        self.tex_id_wind = app.texture.get_basic_texture(path=f'../textures/flow_map.png')

        # Texture
        self.shader_program['u_tex_albedo'] = self.tex_id
        self.shader_program['u_wind'] = self.tex_id_wind
        self.app.texture.textures[self.tex_id].use(location=self.tex_id)
        self.app.texture.textures[self.tex_id_wind].use(location=self.tex_id_wind)

    def update(self):
        self.shader_program['u_time'].value = self.app.time

    def render(self):
        # Position
        # self.shader_program['m_model'].write(self.m_model)

        # Material
        self.shader_program['material.a'].value = self.albedo
        self.shader_program['material.d'].value = self.roughness
        self.shader_program['material.s'].value = self.metallic

        # Texture
        self.shader_program['u_tex_albedo'] = self.tex_id
        self.shader_program['u_wind'] = self.tex_id_wind
        self.app.texture.textures[self.tex_id].use(location=self.tex_id)
        self.app.texture.textures[self.tex_id_wind].use(location=self.tex_id_wind)

        # self.ctx.enable(moderngl.ONE_MINUS_DST_ALPHA) // Testing
        self.vao.render(moderngl.POINTS)
        # self.ctx.disable(moderngl.ONE_MINUS_DST_ALPHA)


class Scene():
    objects = []
    update_list = []
    moved = True

    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx

        # Global Light
        self.app.global_light = DirectionalLight(position=(10, 10, -10),
                                                 direction=(0, 0, 0),
                                                 color=(244/255, 233/255, 155/255),
                                                 strength=self.app.global_light_value)
        # Flash Light
        self.app.flash_light = CameraSpotLight(camera=self.app.camera,
                                               color=(1.0, 1.0, 1.0),
                                               strength=0.0)
        # Point light 1
        self.app.light1 = PointLight(position=(-7, 2, -5),
                                     direction=(0, 0, 0),
                                     color=(0.0, 0.0, 1.0),
                                     strength=self.app.local_light_value)
        # Point light 2
        self.app.light2 = PointLight(position=(7, 2, -5),
                                     direction=(0, 0, 0),
                                     color=(0.0, 1.0, 0.0),
                                     strength=self.app.local_light_value)
        # Point light 3
        self.app.light3 = PointLight(position=(7, 2, 5),
                                     direction=(0, 0, 0),
                                     color=(1.0, 0.0, 0.0),
                                     strength=self.app.local_light_value)
        # Point light 3
        self.app.light4 = PointLight(position=(-7, 2, 5),
                                     direction=(0, 0, 0),
                                     color=(1.0, 1.0, 0.0),
                                     strength=self.app.local_light_value)
        # Point Lights
        self.app.lights = [self.app.light1, self.app.light2, self.app.light3, self.app.light4]

        # Cubes (so we can cast shadows on the grass)
        _g = 1.5
        self.objects.append(Cube(app, position=(-_g*2, 0, 0), texture="crate_0"))
        self.objects.append(Cube(app, position=(-_g, 0, 0), texture="crate_1"))
        self.objects.append(Cube(app, position=(0, 0, 0), texture="crate_2"))
        self.objects.append(Cube(app, position=(_g, 0, 0), texture="metal_0",
                                 roughness=0.4, metallic=0.8))
        self.objects.append(Cube(app, position=(_g*2, 0, 0), texture="metal_1",
                                 roughness=0.3, metallic=1.0))
        self.objects.append(Cube(app, position=(_g*3, 0, 0), texture="metal_1",
                                 albedo=(1.00, 0.71, 0.29), roughness=0.35, metallic=0.95))

        # Terrain, Ground, and Grass
        terrain_chunk_0 = self.app.terrain.add_chunk(self.app, name=0)
        self.objects.append(Grass(self.app, terrain_chunk=terrain_chunk_0))
        self.objects.append(Ground(self.app, terrain_chunk=terrain_chunk_0))

        # Debug lights
        self.light_source_global = LightSource(app, light_source=self.app.global_light)
        self.light_source_local = []
        for light in self.app.lights:
            self.light_source_local.append(LightSource(app, light_source=light))

        # Cache the update list
        for obj in self.objects:
            if obj.can_update:
                self.update_list.append(obj)

    def update(self):
        if self.moved == False:
            for obj in self.update_list:
                obj.update()
            return
        camera_pos = self.app.camera.position
        for obj in self.objects:
            if obj.can_update:
                obj.update()
            angle_from_camera = glm.degrees(glm.acos(glm.dot(glm.normalize(obj.pos - camera_pos),
                                                             self.app.camera.forward)))
            if angle_from_camera <= 120.0:  # View frustum
                obj.can_render = True
                continue
            distance = glm.distance(camera_pos, obj.pos)
            if distance <= 10.0:
                obj.can_render = True
                continue
            obj.can_render = False
        self.moved = False

    def render(self):
        self.app.prototype.common_render_update()

        # Clear buffers
        self.app.shadow.depth_fbo.clear()
        self.app.ctx.clear(color=(0.08, 0.16, 0.18))

        # Pass 1 - Render the depth map for the global light shadows
        if self.app.show_global_light:
            # Enable front face culling in ctx to remove peter-panning flying shadows
            self.ctx.cull_face = "front"
            self.app.shadow.depth_fbo.use()
            for obj in self.objects:
                if obj.can_render and obj.has_shadow:
                    obj.render_shadow()
            self.ctx.cull_face = "back"

        # Pass 2 - Render the scene
        self.app.ctx.screen.use()  # Switch back to the screen
        for obj in self.objects:
            if obj.can_render:
                obj.render()

        # Render debug lights
        if self.app.show_light_sources:
            if self.app.show_global_light:
                self.light_source_global.render()
            if self.app.local_light == 1.0:
                for light_source in self.light_source_local:
                    light_source.render()

        # Swap buffers
        pygame.display.flip()

    def destroy(self):
        pass
