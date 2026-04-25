import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr
import math
import random
from Geometry import Geometry
from PIL import Image
from Planet import Planet

class OpenGLWindow:
    def __init__(self):
        """
        Initialize the OpenGL window.
        """
        self.clock = pg.time.Clock()
        self.animation_running = True
        self.animation_time = 0.0
        self.cloud_animation_time = 0.0
        self.earth_angle = 0.0
        self.moon_angle = 0.0
        self.earth_speed = 10
        self.moon_speed = 30
        self.camera_rotation_x = 0.0
        self.camera_rotation_y = 0.0
        self.camera_rotation_z = 0.0
        self.camera_distance = 40.0
        self.camera_speed = 0.05
        self.sun_rotation_angle = 0.0
        self.earth_rotation_angle = 0.0
        self.moon_rotation_angle = 0.0
        self.sun_rotation_speed = 5.0
        self.earth_rotation_speed = 20.0
        self.moon_rotation_speed = 10.0
        self.first_planet_distance = 9.0
        self.earth_cloud_texture = None
        self.starry_background_texture = None
        self.camera_distance = 150.0
        self.diffuse_textures = {}
        self.normal_textures = {}
        self.cloud_textures = {}
        self.target_planet_index = -1
    
    def init_planets(self):
        """
        Initialize the planets in the solar system.
        """
        self.planets = [
            Planet("Mercury", self.first_planet_distance, 0.2, 20.0, 10.0, "./resources/mercury/diffuse.png", "./resources/mercury/normal.png"),
            Planet("Venus", self.first_planet_distance + 4, 0.4, 15.0, 8.0, "./resources/venus/diffuse.png", "./resources/venus/normal.png", 0.2, [0.8, 0.6, 0.2]),
            Planet("Earth", self.first_planet_distance + 8, 0.5, 10.0, 20.0, "./resources/earth/diffuse.png", "./resources/earth/normal.png", 0.1, [0.0, 0.5, 1.0]),
            Planet("Mars", self.first_planet_distance + 12, 0.3, 8.0, 12.0, "./resources/mars/diffuse.png", "./resources/mars/normal.png", 0.05, [0.8, 0.4, 0.1]),
            Planet("Jupiter", self.first_planet_distance + 20, 1.5, 5.0, 5.0, "./resources/jupiter/diffuse.png", "./resources/jupiter/normal.png", 0.3, [0.8, 0.6, 0.4], [1.0, 0.6, 0.2]),
            Planet("Saturn", self.first_planet_distance + 40, 1.2, 4.0, 4.0, "./resources/saturn/diffuse.png", "./resources/saturn/normal.png", 0.2, [0.8, 0.7, 0.5]),
            Planet("Uranus", self.first_planet_distance + 60, 0.8, 3.0, 3.0, "./resources/uranus/diffuse.png", "./resources/uranus/normal.png", 0.15, [0.6, 0.8, 0.9], [0.2, 0.6, 1.0]),
            Planet("Neptune", self.first_planet_distance + 70, 0.7, 2.0, 2.0, "./resources/neptune/diffuse.png", "./resources/neptune/normal.png", 0.1, [0.2, 0.4, 0.8])
        ]
        self.saturn_ring = Planet("Saturn Ring", self.first_planet_distance + 60, 2.0, 4.0, 0.0, "./resources/saturn/rings_diffuse.png", "./resources/saturn/rings_normal.png")
        self.moon = Planet("Moon", 2, 0.1, 30.0, 10.0, "./resources/moon/diffuse.png", "./resources/moon/normal.png")

    def load_textures(self):
        """
        Load the textures for the planets, sun, and background.
        """
        for planet in self.planets:
            diffuse_texture, normal_texture, cloud_texture = self.load_texture(planet.diffuse_path, planet.normal_path)
            self.diffuse_textures[planet.name] = diffuse_texture
            self.normal_textures[planet.name] = normal_texture

            if planet.name == "Earth":
                self.earth_cloud_texture = cloud_texture

        self.diffuse_textures["Saturn Ring"], self.normal_textures["Saturn Ring"], _ = self.load_texture(self.saturn_ring.diffuse_path, self.saturn_ring.normal_path)
        self.diffuse_textures["Moon"], self.normal_textures["Moon"], _ = self.load_texture(self.moon.diffuse_path, self.moon.normal_path)

        self.sun_diffuse_texture, self.sun_normal_texture, _ = self.load_texture("./resources/sun/diffuse.png", "./resources/sun/normal.png")
        self.starry_background_texture, _, _ = self.load_texture("./resources/starry_background.png")


    def load_shader_program(self, vertex_shader_path, fragment_shader_path):
        """
        Load and compile the shader program.

        Args:
            vertex_shader_path (str): The path to the vertex shader file.
            fragment_shader_path (str): The path to the fragment shader file.

        Returns:
            int: The shader program ID.
        """
        with open(vertex_shader_path, 'r') as f:
            vertex_src = f.readlines()

        with open(fragment_shader_path, 'r') as f:
            fragment_src = f.readlines()

        shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                                compileShader(fragment_src, GL_FRAGMENT_SHADER))

        return shader

    def initGL(self, screen_width=800, screen_height=600):
        """
        Initialize OpenGL and set up the rendering context.

        Args:
            screen_width (int, optional): The width of the screen. Defaults to 800.
            screen_height (int, optional): The height of the screen. Defaults to 600.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 2)
        pg.display.set_mode((screen_width, screen_height), pg.OPENGL | pg.DOUBLEBUF)

        glEnable(GL_DEPTH_TEST)
        glClearColor(0, 0, 0, 1)

        self.init_planets()
        self.load_textures()

        # Set up the light sources
        self.light_colors = np.array([[2, 2, 2]], dtype=np.float32)  # Sun color

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.shader = self.load_shader_program("./shaders/simple.vert", "./shaders/simple.frag")
        glUseProgram(self.shader)

        self.sphere = Geometry('./resources/sphere.obj')

        # Load the textures for each planet
        for planet in self.planets:
            diffuse_texture, normal_texture, cloud_texture = self.load_texture(planet.diffuse_path, planet.normal_path)
            self.diffuse_textures[planet.name] = diffuse_texture
            self.normal_textures[planet.name] = normal_texture
            
            if planet.name == "Earth":
                self.earth_cloud_texture = cloud_texture

        # Load the textures for Saturn's ring and the Moon
        self.diffuse_textures["Saturn Ring"], self.normal_textures["Saturn Ring"], _ = self.load_texture(self.saturn_ring.diffuse_path, self.saturn_ring.normal_path)
        self.diffuse_textures["Moon"], self.normal_textures["Moon"], _ = self.load_texture(self.moon.diffuse_path, self.moon.normal_path)

        # Load the Sun's textures
        self.sun_diffuse_texture, self.sun_normal_texture, _ = self.load_texture("./resources/sun/diffuse.png", "./resources/sun/normal.png")

        self.starry_background_texture, _, _ = self.load_texture("./resources/starry_background.png")

        # Set up the light sources
        self.light_positions = []
        self.light_colors = []

        for planet in self.planets:
            if np.any(planet.light_color > 0.0):
                self.light_positions.append(planet.distance * np.array([math.cos(planet.angle), 0.0, math.sin(planet.angle)], dtype=np.float32))
                self.light_colors.append(planet.light_color)

        self.light_colors = np.array(self.light_colors, dtype=np.float32)

        self.init_orbit_geometry()
        self.init_asteroids()

        pg.font.init()
        self.font = pg.font.SysFont('Arial', 20)
        self.hud_shader = self.load_shader_program("./shaders/hud.vert", "./shaders/hud.frag")
        self.init_hud_geometry()
        self.init_fbo()

        print("Setup complete!")
    
    def load_texture(self, diffuse_path, normal_path=None):
        """
        Load a texture from file.

        Args:
            diffuse_path (str): The path to the diffuse texture file.
            normal_path (str, optional): The path to the normal texture file. Defaults to None.

        Returns:
            tuple: A tuple containing the diffuse texture ID, normal texture ID (if provided), and cloud texture ID (if applicable).
        """
        try:
            # Load the diffuse texture
            diffuse_texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, diffuse_texture)

            # Set the texture wrapping and filtering parameters for the diffuse texture
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            # Load the diffuse image using PIL
            diffuse_image = Image.open(diffuse_path)
            diffuse_data = np.array(list(diffuse_image.getdata()), np.uint8)

            # Determine the color format based on the number of channels
            if diffuse_image.mode == 'RGB':
                diffuse_format = GL_RGB
            elif diffuse_image.mode == 'RGBA':
                diffuse_format = GL_RGBA
            else:
                raise Exception(f"Unsupported image mode: {diffuse_image.mode}")

            # Bind the diffuse texture data to the texture object
            glTexImage2D(GL_TEXTURE_2D, 0, diffuse_format, diffuse_image.width, diffuse_image.height, 0, diffuse_format, GL_UNSIGNED_BYTE, diffuse_data)
            glGenerateMipmap(GL_TEXTURE_2D)

            normal_texture = None
            if normal_path is not None:
                # Load the normal texture
                normal_texture = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, normal_texture)

                # Set the texture wrapping and filtering parameters for the normal texture
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

                # Load the normal image using PIL
                normal_image = Image.open(normal_path)
                normal_data = np.array(list(normal_image.getdata()), np.uint8)

                # Determine the color format based on the number of channels
                if normal_image.mode == 'RGB':
                    normal_format = GL_RGB
                elif normal_image.mode == 'RGBA':
                    normal_format = GL_RGBA
                else:
                    raise Exception(f"Unsupported image mode: {normal_image.mode}")

                # Bind the normal texture data to the texture object
                glTexImage2D(GL_TEXTURE_2D, 0, normal_format, normal_image.width, normal_image.height, 0, normal_format, GL_UNSIGNED_BYTE, normal_data)
                glGenerateMipmap(GL_TEXTURE_2D)

            cloud_texture = None
            if diffuse_path == "./resources/earth/diffuse.png":
                # Load the cloud texture only for Earth
                cloud_texture = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, cloud_texture)
                
                # Set the texture wrapping and filtering parameters for the cloud texture
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                
                # Load the cloud image using PIL
                cloud_image = Image.open("./resources/earth/clouds.png")
                cloud_data = np.array(list(cloud_image.getdata()), np.uint8)
                
                # Determine the color format based on the number of channels
                if cloud_image.mode == 'RGB':
                    cloud_format = GL_RGB
                elif cloud_image.mode == 'RGBA':
                    cloud_format = GL_RGBA
                else:
                    raise Exception(f"Unsupported image mode: {cloud_image.mode}")
                
                # Bind the cloud texture data to the texture object
                glTexImage2D(GL_TEXTURE_2D, 0, cloud_format, cloud_image.width, cloud_image.height, 0, cloud_format, GL_UNSIGNED_BYTE, cloud_data)
                glGenerateMipmap(GL_TEXTURE_2D)

            return diffuse_texture, normal_texture, cloud_texture

        except Exception as e:
            print(f"Error loading texture: {str(e)}")
            return None, None, None

    def handle_mouse_movement(self, dx, dy):
        """
        Update the camera rotation based on mouse movement.
        """
        sensitivity = 0.005
        self.camera_rotation_y -= dx * sensitivity
        self.camera_rotation_x -= dy * sensitivity
        
        # Clamp pitch to avoid flipping
        max_pitch = math.pi / 2.0 - 0.01
        self.camera_rotation_x = max(min(self.camera_rotation_x, max_pitch), -max_pitch)

    def handle_mouse_scroll(self, dy):
        """
        Update the camera zoom based on mouse scroll.
        """
        zoom_speed = 5.0
        self.camera_distance -= dy * zoom_speed
        
        # Keep distance within reasonable bounds
        self.camera_distance = max(10.0, min(self.camera_distance, 500.0))

    def init_orbit_geometry(self):
        """
        Initializes a generic circle VBO for drawing orbits.
        """
        self.orbit_vao = glGenVertexArrays(1)
        glBindVertexArray(self.orbit_vao)

        # Generate points for a circle (radius 1)
        segments = 100
        vertices = []
        for i in range(segments):
            theta = 2.0 * math.pi * float(i) / float(segments)
            x = math.cos(theta)
            z = math.sin(theta)
            # Position: x, y, z
            vertices.extend([x, 0.0, z])
            # Fake UV
            vertices.extend([0.0, 0.0])
            # Fake Normal: up
            vertices.extend([0.0, 1.0, 0.0])
        
        self.orbit_vertex_count = segments
        self.orbit_vertices = np.array(vertices, dtype=np.float32)
        
        self.orbit_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.orbit_vbo)
        glBufferData(GL_ARRAY_BUFFER, self.orbit_vertices.nbytes, self.orbit_vertices, GL_STATIC_DRAW)
        
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(20))

    def init_asteroids(self):
        """
        Initializes an asteroid belt between Mars and Jupiter.
        Mars distance: 21, Jupiter distance: 29. Belt range: 23 to 27.
        """
        self.asteroids = []
        for _ in range(500):
            angle_offset = random.uniform(0, 2 * math.pi)
            dist = random.uniform(self.first_planet_distance + 15, self.first_planet_distance + 18.5)
            height = random.uniform(-0.8, 0.8)
            speed = random.uniform(6.0, 9.0)
            scale = random.uniform(0.015, 0.1)
            rot_speed = random.uniform(-20.0, 20.0)
            self.asteroids.append({
                'base_dist': dist,
                'height': height,
                'speed': speed,
                'scale': scale,
                'angle_offset': angle_offset,
                'rot_speed': rot_speed
            })

    def init_hud_geometry(self):
        """
        Initializes the VBO for a full-screen HUD quad.
        """
        self.hud_vao = glGenVertexArrays(1)
        glBindVertexArray(self.hud_vao)
        hud_vertices = np.array([
            # x, y, u, v  (V is flipped because Pygame surface coordinate 0,0 is top-left)
            -1.0,  1.0, 0.0, 0.0,
            -1.0, -1.0, 0.0, 1.0,
             1.0, -1.0, 1.0, 1.0,
            -1.0,  1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 1.0,
             1.0,  1.0, 1.0, 0.0
        ], dtype=np.float32)

        self.hud_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.hud_vbo)
        glBufferData(GL_ARRAY_BUFFER, hud_vertices.nbytes, hud_vertices, GL_STATIC_DRAW)
        
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))
        
        self.hud_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.hud_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    def init_fbo(self):
        """
        Initializes the Framebuffer for post-processing Bloom effect.
        """
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        self.fbo_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.fbo_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.screen_width, self.screen_height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.fbo_texture, 0)

        self.rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.screen_width, self.screen_height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.rbo)

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print("ERROR::FRAMEBUFFER:: Framebuffer is not complete!")
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
        self.post_shader = self.load_shader_program("./shaders/post.vert", "./shaders/post.frag")

    def toggle_animation(self):
        """
        Toggle the animation on/off.
        """
        self.animation_running = not self.animation_running

    def render(self):
        """
        Render the scene.
        """
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glEnable(GL_DEPTH_TEST)
        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader)

        # Update the animation time if the animation is running
        if self.animation_running:
            self.animation_time += 0.001
            self.cloud_animation_time += 0.01

        # Update planet angles early so the camera can track them
        for planet in self.planets:
            planet.angle = planet.speed * self.animation_time
            planet.rotation_angle = planet.rotation_speed * self.animation_time

        # Set up the projection matrix
        aspect_ratio = 640.0 / 480.0
        near_plane = 0.1
        far_plane = 1000.0
        fov = 45.0

        projection = pyrr.matrix44.create_perspective_projection(fov, aspect_ratio, near_plane, far_plane)
        projection_loc = glGetUniformLocation(self.shader, "projection")
        glUniformMatrix4fv(projection_loc, 1, GL_FALSE, projection)

        # Set up the view matrix based on camera rotation angles
        if self.target_planet_index != -1 and self.target_planet_index < len(self.planets):
            target = self.planets[self.target_planet_index]
            target_pos = pyrr.Vector3([target.distance * math.cos(target.angle), 0.0, target.distance * math.sin(target.angle)])
            
            # The zooming range is closer since we're viewing a planet
            zoom = max(2.5 * target.radius, self.camera_distance * 0.15)
            
            camera_offset = pyrr.Vector3([
                zoom * math.cos(self.camera_rotation_y) * math.cos(self.camera_rotation_x),
                zoom * math.sin(self.camera_rotation_x),
                zoom * math.cos(self.camera_rotation_x) * math.sin(self.camera_rotation_y)
            ])
            camera_position = target_pos + camera_offset
            
            view_matrix = pyrr.matrix44.create_look_at(camera_position, target_pos, pyrr.Vector3([0.0, 1.0, 0.0]))
        else:
            view_matrix = pyrr.matrix44.create_identity()
            view_matrix = pyrr.matrix44.multiply(view_matrix, pyrr.matrix44.create_from_y_rotation(self.camera_rotation_y))
            view_matrix = pyrr.matrix44.multiply(view_matrix, pyrr.matrix44.create_from_x_rotation(self.camera_rotation_x))
            view_matrix = pyrr.matrix44.multiply(view_matrix, pyrr.matrix44.create_from_z_rotation(self.camera_rotation_z))
            view_matrix = pyrr.matrix44.multiply(view_matrix, pyrr.matrix44.create_from_translation(pyrr.Vector3([0.0, 0.0, -self.camera_distance])))

            # Calculate the camera position based on the rotation angles
            camera_position = pyrr.Vector3([
                self.camera_distance * math.cos(self.camera_rotation_y) * math.cos(self.camera_rotation_x),
                self.camera_distance * math.sin(self.camera_rotation_x),
                self.camera_distance * math.cos(self.camera_rotation_x) * math.sin(self.camera_rotation_y)
            ])

        view_loc = glGetUniformLocation(self.shader, "view")
        glUniformMatrix4fv(view_loc, 1, GL_FALSE, view_matrix)

        # Set the camera position as the viewPos uniform
        glUniform3fv(glGetUniformLocation(self.shader, "viewPos"), 1, camera_position)




        glUniform1f(glGetUniformLocation(self.shader, "cloudAnimationTime"), self.cloud_animation_time)

        # Calculate the Earth and Moon angles based on the animation time
        self.earth_angle = self.earth_speed * self.animation_time
        self.moon_angle = self.moon_speed * self.animation_time

        # Update the rotation angles based on the animation time
        self.sun_rotation_angle = self.sun_rotation_speed * self.animation_time
        self.earth_rotation_angle = self.earth_rotation_speed * self.animation_time
        self.moon_rotation_angle = self.moon_rotation_speed * self.animation_time

        # Bind the Sun textures
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.sun_diffuse_texture)
        glUniform1i(glGetUniformLocation(self.shader, "diffuseTexture"), 0)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.sun_normal_texture)
        glUniform1i(glGetUniformLocation(self.shader, "normalTexture"), 1)

        sun_ka = np.array([0.2, 0.2, 0.2], dtype=np.float32)
        sun_kd = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        sun_ks = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        sun_shininess = 80.0

        sun_position = pyrr.Vector3([0.0, 0.0, 0.0])
        sun_radius = 2.0
        sun_color = np.array([2, 2, 2], dtype=np.float32)
        
        glUniform3fv(glGetUniformLocation(self.shader, "sunPosition"), 1, sun_position)
        glUniform1f(glGetUniformLocation(self.shader, "sunRadius"), sun_radius)
        glUniform3fv(glGetUniformLocation(self.shader, "sunColor"), 1, sun_color)

        # Draw the Sun
        sun_model = pyrr.matrix44.create_identity()
        sun_model = pyrr.matrix44.multiply(sun_model, pyrr.matrix44.create_from_y_rotation(self.sun_rotation_angle))
        sun_model = pyrr.matrix44.multiply(sun_model, pyrr.matrix44.create_from_translation(sun_position))
        sun_model = pyrr.matrix44.multiply(sun_model, pyrr.matrix44.create_from_scale(pyrr.Vector3([sun_radius, sun_radius, sun_radius])))
        self.draw_object(self.sphere, sun_model, sun_ka, sun_kd, sun_ks, sun_shininess, is_sun=True)

        # Draw the Planets
        for planet in self.planets:

            # Bind the planet textures
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.diffuse_textures[planet.name])
            glUniform1i(glGetUniformLocation(self.shader, "diffuseTexture"), 0)

            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, self.normal_textures[planet.name])
            glUniform1i(glGetUniformLocation(self.shader, "normalTexture"), 1)

            if planet.name == "Mercury":
                planet_ka = np.array([0.1, 0.1, 0.1], dtype=np.float32)
                planet_kd = np.array([0.4, 0.4, 0.4], dtype=np.float32)
                planet_ks = np.array([0.2, 0.2, 0.2], dtype=np.float32)
                planet_shininess = 16.0
            elif planet.name == "Venus":
                planet_ka = np.array([0.2, 0.2, 0.2], dtype=np.float32)
                planet_kd = np.array([0.8, 0.6, 0.4], dtype=np.float32)
                planet_ks = np.array([0.4, 0.3, 0.2], dtype=np.float32)
                planet_shininess = 32.0
            elif planet.name == "Earth":
                planet_ka = np.array([0.1, 0.1, 0.1], dtype=np.float32)
                planet_kd = np.array([0.0, 0.5, 1.0], dtype=np.float32)
                planet_ks = np.array([0.3, 0.3, 0.3], dtype=np.float32)
                planet_shininess = 64.0
            elif planet.name == "Mars":
                planet_ka = np.array([0.2, 0.1, 0.1], dtype=np.float32)
                planet_kd = np.array([0.8, 0.4, 0.1], dtype=np.float32)
                planet_ks = np.array([0.2, 0.2, 0.2], dtype=np.float32)
                planet_shininess = 32.0
            elif planet.name == "Jupiter":
                planet_ka = np.array([0.2, 0.2, 0.2], dtype=np.float32)
                planet_kd = np.array([0.8, 0.6, 0.4], dtype=np.float32)
                planet_ks = np.array([0.4, 0.4, 0.4], dtype=np.float32)
                planet_shininess = 128.0
            elif planet.name == "Saturn":
                planet_ka = np.array([0.2, 0.2, 0.2], dtype=np.float32)
                planet_kd = np.array([0.8, 0.7, 0.5], dtype=np.float32)
                planet_ks = np.array([0.5, 0.5, 0.5], dtype=np.float32)
                planet_shininess = 128.0
            elif planet.name == "Uranus":
                planet_ka = np.array([0.1, 0.1, 0.1], dtype=np.float32)
                planet_kd = np.array([0.6, 0.8, 0.9], dtype=np.float32)
                planet_ks = np.array([0.4, 0.4, 0.4], dtype=np.float32)
                planet_shininess = 64.0
            elif planet.name == "Neptune":
                planet_ka = np.array([0.1, 0.1, 0.1], dtype=np.float32)
                planet_kd = np.array([0.6, 0.6, 0.6], dtype=np.float32)
                planet_ks = np.array([0.1, 0.1, 0.1], dtype=np.float32)
                planet_shininess = 16.0

            planet_model = pyrr.matrix44.create_from_y_rotation(planet.angle)
            planet_model = pyrr.matrix44.multiply(planet_model, pyrr.matrix44.create_from_y_rotation(planet.rotation_angle))
            planet_model = pyrr.matrix44.multiply(planet_model, pyrr.matrix44.create_from_scale(pyrr.Vector3([planet.radius, planet.radius, planet.radius])))
            planet_model = pyrr.matrix44.multiply(planet_model, pyrr.matrix44.create_from_translation(pyrr.Vector3([planet.distance * math.cos(planet.angle), 0.0, planet.distance * math.sin(planet.angle)])))

            if planet.name == "Earth":
                self.draw_object(self.sphere, planet_model, planet_ka, planet_kd, planet_ks, planet_shininess, planet=planet)
            else:
                self.draw_object(self.sphere, planet_model, planet_ka, planet_kd, planet_ks, planet_shininess)

            # Draw the planet's orbit
            orbit_model = pyrr.matrix44.create_identity()
            orbit_model = pyrr.matrix44.multiply(orbit_model, pyrr.matrix44.create_from_scale(pyrr.Vector3([planet.distance, 1.0, planet.distance])))
            self.draw_orbit_ring(orbit_model)

        # Draw the Asteroid Belt
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.diffuse_textures["Moon"]) # Use moon texture for rocks
        glUniform1i(glGetUniformLocation(self.shader, "diffuseTexture"), 0)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.normal_textures["Moon"])
        glUniform1i(glGetUniformLocation(self.shader, "normalTexture"), 1)

        ast_ka = np.array([0.1, 0.1, 0.1], dtype=np.float32)
        ast_kd = np.array([0.4, 0.4, 0.4], dtype=np.float32)
        ast_ks = np.array([0.05, 0.05, 0.05], dtype=np.float32)
        ast_shininess = 8.0

        for ast in self.asteroids:
            ast_angle = ast['angle_offset'] + ast['speed'] * self.animation_time
            ast_rot = ast['rot_speed'] * self.animation_time
            ast_model = pyrr.matrix44.create_from_y_rotation(ast_rot)
            ast_model = pyrr.matrix44.multiply(ast_model, pyrr.matrix44.create_from_scale(pyrr.Vector3([ast['scale'], ast['scale'], ast['scale']])))
            ast_position = pyrr.Vector3([
                ast['base_dist'] * math.cos(ast_angle),
                ast['height'],
                ast['base_dist'] * math.sin(ast_angle)
            ])
            ast_model = pyrr.matrix44.multiply(ast_model, pyrr.matrix44.create_from_translation(ast_position))
            self.draw_object(self.sphere, ast_model, ast_ka, ast_kd, ast_ks, ast_shininess)
    

        # Draw Saturn's Ring
        saturn = next((planet for planet in self.planets if planet.name == "Saturn"), None)
        if saturn:
            # Bind Saturn's Ring textures
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.diffuse_textures["Saturn Ring"])
            glUniform1i(glGetUniformLocation(self.shader, "diffuseTexture"), 0)

            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, self.normal_textures["Saturn Ring"])
            glUniform1i(glGetUniformLocation(self.shader, "normalTexture"), 1)

            ring_ka = np.array([1, 1, 1], dtype=np.float32)
            ring_kd = np.array([0.8, 0.8, 0.8], dtype=np.float32)
            ring_ks = np.array([0.2, 0.2, 0.2], dtype=np.float32)
            ring_shininess = 100.0

            ring_model = pyrr.matrix44.create_from_y_rotation(saturn.angle)
            ring_model = pyrr.matrix44.multiply(ring_model, pyrr.matrix44.create_from_scale(pyrr.Vector3([self.saturn_ring.radius, 0.1, self.saturn_ring.radius])))
            ring_model = pyrr.matrix44.multiply(ring_model, pyrr.matrix44.create_from_translation(pyrr.Vector3([saturn.distance * math.cos(saturn.angle), 0.0, saturn.distance * math.sin(saturn.angle)])))

            self.draw_object(self.sphere, ring_model, ring_ka, ring_kd, ring_ks, ring_shininess, is_saturn_ring=True)

        # Draw the Moon relative to Earth
        earth = next((planet for planet in self.planets if planet.name == "Earth"), None)
        if earth:
            moon_angle = self.moon.speed * self.animation_time
            moon_rotation_angle = self.moon.rotation_speed * self.animation_time

           # Bind the Moon textures
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.diffuse_textures["Moon"])
            glUniform1i(glGetUniformLocation(self.shader, "diffuseTexture"), 0)

            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, self.normal_textures["Moon"])
            glUniform1i(glGetUniformLocation(self.shader, "normalTexture"), 1)

            moon_ka = np.array([0.1, 0.1, 0.1], dtype=np.float32)
            moon_kd = np.array([0.6, 0.6, 0.6], dtype=np.float32)
            moon_ks = np.array([0.1, 0.1, 0.1], dtype=np.float32)
            moon_shininess = 16.0

            moon_position = earth.distance * np.array([math.cos(earth.angle), 0.0, math.sin(earth.angle)], dtype=np.float32)
            moon_orbit_position = self.moon.distance * np.array([math.cos(moon_angle), 0.0, math.sin(moon_angle)], dtype=np.float32)

            moon_model = pyrr.matrix44.create_from_y_rotation(moon_angle)
            moon_model = pyrr.matrix44.multiply(moon_model, pyrr.matrix44.create_from_y_rotation(moon_rotation_angle))
            moon_model = pyrr.matrix44.multiply(moon_model, pyrr.matrix44.create_from_scale(pyrr.Vector3([self.moon.radius, self.moon.radius, self.moon.radius])))
            moon_model = pyrr.matrix44.multiply(moon_model, pyrr.matrix44.create_from_translation(moon_position + moon_orbit_position))

            self.draw_object(self.sphere, moon_model, moon_ka, moon_kd, moon_ks, moon_shininess)

            # Draw the moon's orbit around the earth
            moon_orbit_model = pyrr.matrix44.create_from_translation(moon_position)
            moon_orbit_model = pyrr.matrix44.multiply(pyrr.matrix44.create_from_scale(pyrr.Vector3([self.moon.distance, 1.0, self.moon.distance])), moon_orbit_model)
            self.draw_orbit_ring(moon_orbit_model)

        # Bind the starry background texture
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.starry_background_texture)
        glUniform1i(glGetUniformLocation(self.shader, "diffuseTexture"), 0)

        # Create a large sphere encompassing the scene
        background_radius = 50
        background_model = pyrr.matrix44.create_identity()
        background_model = pyrr.matrix44.multiply(background_model, pyrr.matrix44.create_from_translation(pyrr.Vector3([0.0, 0.0, 0.0])))
        background_model = pyrr.matrix44.create_from_scale(pyrr.Vector3([background_radius, background_radius, background_radius]))

        # Draw the starry background sphere
        self.draw_object(self.sphere, background_model, None, None, None, None, is_starry_background=True)

        # Update the light positions based on the planet positions
        self.light_positions = []
        for planet in self.planets:
            if np.any(planet.light_color > 0.0):
                planet_position = planet.distance * np.array([math.cos(planet.angle), 0.0, math.sin(planet.angle)], dtype=np.float32)
                self.light_positions.append(planet_position)
        self.light_positions = np.array(self.light_positions, dtype=np.float32)

        # Set the shader uniform variables for the light sources
        glUniform3fv(glGetUniformLocation(self.shader, "lightPositions"), len(self.light_positions), self.light_positions)
        glUniform3fv(glGetUniformLocation(self.shader, "lightColors"), len(self.light_colors), self.light_colors)

        # Unbind FBO and draw to screen
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        
        glDisable(GL_DEPTH_TEST)
        
        glUseProgram(self.post_shader)
        glBindVertexArray(self.hud_vao) # Reuse HUD quad geometry
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.fbo_texture)
        glUniform1i(glGetUniformLocation(self.post_shader, "screenTexture"), 0)
        
        glDrawArrays(GL_TRIANGLES, 0, 6)
        
        glEnable(GL_DEPTH_TEST)

        self.render_hud()

        pg.display.flip()

    def render_hud(self):
        """
        Renders Pygame text to an OpenGL texture and draws it as an overlay.
        """
        hud_surface = pg.Surface((self.screen_width, self.screen_height), pg.SRCALPHA)
        
        mode = "Viewing: Free Camera (Sun Focused)"
        if self.target_planet_index != -1 and self.target_planet_index < len(self.planets):
            mode = f"Viewing: Tracking {self.planets[self.target_planet_index].name}"
        
        text1 = self.font.render(mode, True, (255, 255, 255))
        hud_surface.blit(text1, (20, 20))
        
        text2 = self.font.render("Mouse: Left-click & drag to rotate | Scroll to zoom", True, (200, 200, 200))
        hud_surface.blit(text2, (20, 50))

        text3 = self.font.render("Keys 1-8: Focus Planet | Key 0: Reset to Sun | SPACE: Pause", True, (200, 200, 200))
        hud_surface.blit(text3, (20, 80))
        
        text_data = pg.image.tostring(hud_surface, "RGBA", False)
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.hud_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.screen_width, self.screen_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        glUseProgram(self.hud_shader)
        glUniform1i(glGetUniformLocation(self.hud_shader, "textTexture"), 0)

        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glBindVertexArray(self.hud_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)

    def draw_object(self, obj, model, ka, kd, ks, shininess, is_sun=False, is_saturn_ring=False, is_starry_background=False, planet=None):
        """
        Draw an object using the provided model matrix and material properties.

        Args:
            obj (Geometry): The geometry object to draw.
            model (numpy.ndarray): The model matrix.
            ka (numpy.ndarray): The ambient reflection coefficient.
            kd (numpy.ndarray): The diffuse reflection coefficient.
            ks (numpy.ndarray): The specular reflection coefficient.
            shininess (float): The shininess exponent.
            is_sun (bool, optional): Whether the object is the sun. Defaults to False.
            is_saturn_ring (bool, optional): Whether the object is Saturn's ring. Defaults to False.
            is_starry_background (bool, optional): Whether the object is the starry background. Defaults to False.
            planet (Planet, optional): The planet object, if applicable. Defaults to None.
        """
        glBindVertexArray(self.vao)
        
        model_loc = glGetUniformLocation(self.shader, "model")
        glUniformMatrix4fv(model_loc, 1, GL_FALSE, model)

        # Set isOrbit flag to 0 for regular objects
        is_orbit_loc = glGetUniformLocation(self.shader, "isOrbit")
        glUniform1i(is_orbit_loc, 0)

        if planet is not None:
            atmosphere_thickness_loc = glGetUniformLocation(self.shader, "atmosphereThickness")
            glUniform1f(atmosphere_thickness_loc, planet.atmosphere_thickness)

            atmosphere_color_loc = glGetUniformLocation(self.shader, "atmosphereColor")
            glUniform3fv(atmosphere_color_loc, 1, planet.atmosphere_color)

        normal_matrix = pyrr.matrix33.create_from_matrix44(pyrr.matrix44.inverse(model.T))
        glUniformMatrix3fv(glGetUniformLocation(self.shader, "normalMatrix"), 1, GL_FALSE, normal_matrix)

        if not is_starry_background:
            ka_loc = glGetUniformLocation(self.shader, "ka")
            glUniform3fv(ka_loc, 1, ka)

            kd_loc = glGetUniformLocation(self.shader, "kd")
            glUniform3fv(kd_loc, 1, kd)

            ks_loc = glGetUniformLocation(self.shader, "ks")
            glUniform3fv(ks_loc, 1, ks)

            shininess_loc = glGetUniformLocation(self.shader, "shininess")
            glUniform1f(shininess_loc, shininess)

        is_sun_loc = glGetUniformLocation(self.shader, "isSun")
        glUniform1i(is_sun_loc, 1 if is_sun else 0)

        is_saturn_ring_loc = glGetUniformLocation(self.shader, "isSaturnRing")
        glUniform1i(is_saturn_ring_loc, 1 if is_saturn_ring else 0)

        is_starry_background_loc = glGetUniformLocation(self.shader, "isStarryBackground")
        glUniform1i(is_starry_background_loc, 1 if is_starry_background else 0)

        if planet is not None and planet.name == "Earth":
            glActiveTexture(GL_TEXTURE2)
            glBindTexture(GL_TEXTURE_2D, self.earth_cloud_texture)
            glUniform1i(glGetUniformLocation(self.shader, "cloudTexture"), 2)
            
            glUniform1i(glGetUniformLocation(self.shader, "isEarth"), 1)
        else:
            glUniform1i(glGetUniformLocation(self.shader, "isEarth"), 0)

        glDrawArrays(GL_TRIANGLES, 0, obj.vertexCount)

    def draw_orbit_ring(self, model):
        """
        Draw an orbit circle using GL_LINE_LOOP
        """
        model_loc = glGetUniformLocation(self.shader, "model")
        glUniformMatrix4fv(model_loc, 1, GL_FALSE, model)

        # Set an emissive-like ambient state for the line so it's visible without lighting
        ka_loc = glGetUniformLocation(self.shader, "ka")
        glUniform3fv(ka_loc, 1, np.array([0.5, 0.5, 0.5], dtype=np.float32))
        kd_loc = glGetUniformLocation(self.shader, "kd")
        glUniform3fv(kd_loc, 1, np.array([0.0, 0.0, 0.0], dtype=np.float32))
        ks_loc = glGetUniformLocation(self.shader, "ks")
        glUniform3fv(ks_loc, 1, np.array([0.0, 0.0, 0.0], dtype=np.float32))
        shininess_loc = glGetUniformLocation(self.shader, "shininess")
        glUniform1f(shininess_loc, 1.0)
        
        is_sun_loc = glGetUniformLocation(self.shader, "isSun")
        glUniform1i(is_sun_loc, 0) # Treat as sun to ignore complex shading
        is_saturn_ring_loc = glGetUniformLocation(self.shader, "isSaturnRing")
        glUniform1i(is_saturn_ring_loc, 0)
        is_starry_background_loc = glGetUniformLocation(self.shader, "isStarryBackground")
        glUniform1i(is_starry_background_loc, 0)
        glUniform1i(glGetUniformLocation(self.shader, "isEarth"), 0)

        is_orbit_loc = glGetUniformLocation(self.shader, "isOrbit")
        glUniform1i(is_orbit_loc, 1)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glBindVertexArray(self.orbit_vao)
        glDrawArrays(GL_LINE_LOOP, 0, self.orbit_vertex_count)
        glBindVertexArray(self.vao)

        glDisable(GL_BLEND)

    def cleanup(self):
        """
        Clean up the OpenGL resources.
        """
        self.sphere.cleanup()
        glDeleteProgram(self.shader)
        glDeleteProgram(self.hud_shader)
        glDeleteProgram(self.post_shader)
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteVertexArrays(1, (self.orbit_vao,))
        glDeleteVertexArrays(1, (self.hud_vao,))
        glDeleteBuffers(1, (self.orbit_vbo,))
        glDeleteBuffers(1, (self.hud_vbo,))
        glDeleteFramebuffers(1, (self.fbo,))
        glDeleteRenderbuffers(1, (self.rbo,))