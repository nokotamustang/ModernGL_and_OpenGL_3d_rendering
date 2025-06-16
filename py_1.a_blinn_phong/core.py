import numpy
import moderngl
import glm
import pygame

mat_4 = glm.mat4(1)


def generate_vertex_data(vertices, indices):
    data = [vertices[ind] for triangle in indices for ind in triangle]
    return numpy.array(data, dtype='f4')


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

    def get_color_texture(self, size, name='color_texture', samples=None, disable_repeat=False):
        if name in self.texture_map:
            return self.texture_map[name]
        if samples == None:
            color_texture = self.ctx.texture(size=size, components=4)
        else:
            color_texture = self.ctx.texture(size=size, components=4, samples=samples)
        # Remove repetition
        if disable_repeat:
            color_texture.repeat_x = False
            color_texture.repeat_y = False
        # Add to list
        self.texture_count += 1
        self.texture_map[name] = self.texture_count
        self.textures.append(color_texture)
        print(f"loaded color texture: {name} at index: {self.texture_count}")

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


def generate_vertex_data(vertices, indices):
    data = [vertices[ind] for triangle in indices for ind in triangle]
    return numpy.array(data, dtype='f4')


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
                app=self.app,
                shader_name='default',
                shadow_name='shadow'
            )
        elif name == "light_source":
            base_object = PrototypeLightSource(
                app=self.app,
                light_name='light'
            )

        # Add to list
        self.object_count += 1
        self.object_map[name] = self.object_count
        self.objects.append(base_object)
        print(f"loaded proto-object: {name} at index: {self.object_count}")
        return base_object

    def common_render_update(self):
        shader_program = self.app.shader.get_shader('default')
        # Resolution
        # shader_program['u_resolution'].write(glm.vec2(self.app.win_size))

        # Position
        shader_program['num_lights'].value = len(self.app.lights)
        shader_program['cam_pos'].write(self.app.camera.position)
        shader_program['m_proj'].write(self.app.camera.m_proj)
        shader_program['m_view'].write(self.app.camera.m_view)

        # Send lights into uniform array of Light struct
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

        # Shadow
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


class Cube:
    def __init__(self, app, albedo=(1.0, 1.0, 1.0), diffuse=0.75, specular=0.25,
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

        self.albedo = glm.vec3(albedo)  # Ambient (Albedo)
        self.diffuse = diffuse  # Diffuse (Lambert)
        self.specular = specular  # Specular (Blinn-Phong)

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
        self.shader_program['material.d'].value = self.diffuse
        self.shader_program['material.s'].value = self.specular
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


class Scene():
    objects = []
    update_list = []
    moved = True

    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx

        # Global Light
        self.app.global_light = DirectionalLight(position=(20, 20, -20),
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
        # Point light 4
        self.app.light4 = PointLight(position=(-7, 2, 5),
                                     direction=(0, 0, 0),
                                     color=(1.0, 1.0, 0.0),
                                     strength=self.app.local_light_value)
        # Point Lights
        self.app.lights = [self.app.light1, self.app.light2, self.app.light3, self.app.light4]

        # Create a n*n grid for the floor
        _n = 10
        _h = -1
        _s = 1
        for i in range(-_n, _n):
            for j in range(-_n, _n):
                self.objects.append(Floor(app, position=(i*_s*2.0, _h, j*_s*2.0), scale=(_s, 0.1, _s)))

        # Add cubes
        _g = 1.5
        self.objects.append(Cube(app, position=(-_g*2, 0, 0), texture="crate_0"))
        self.objects.append(Cube(app, position=(-_g, 0, 0), texture="crate_1"))
        self.objects.append(Cube(app, position=(0, 0, 0), texture="crate_2"))
        self.objects.append(Cube(app, position=(_g, 0, 0), texture="metal_0", diffuse=0.4, specular=0.8))
        self.objects.append(Cube(app, position=(_g*2, 0, 0), texture="metal_1", diffuse=0.3, specular=1.0))
        self.objects.append(Cube(app, position=(_g*3, 0, 0), texture="metal_1", albedo=(1.00, 0.71, 0.29), diffuse=0.35, specular=0.95))

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
            angle_from_camera = glm.degrees(glm.acos(glm.dot(glm.normalize(obj.pos - camera_pos), self.app.camera.forward)))
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
                if obj.can_render:
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
