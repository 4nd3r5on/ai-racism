from enum import IntEnum
import math
from pygame import Color, Rect, SurfaceType, Vector2
from engine.interfaces import CollisionShape, EngineAPI, GameObject, GameObjectUpdateRes
from engine.physics import PhysicsBody
from engine.primitives import RectShape
from game.objects.objects import GameObjectType
from game.signals import EngineSignal

class CarSignals(IntEnum):
    GAS = 1
    BRAKE = 2
    STEER_LEFT = 3
    STEER_RIGHT = 4
    RELEASE_GAS = 5
    RELEASE_BRAKE = 6
    RELEASE_STEER = 7


class Car(GameObject):
    _type = GameObjectType.CAR
    def __init__(self, mass=1000, length=40, width=20, color=Color(0, 0, 255), 
                 pull=500, friction_coeff=0.8, brake_multiplier=5, 
                 location=(100, 100, 0.5*math.pi)):

        # Initialize physics body
        self.physics = PhysicsBody(
            position=Vector2(location[0], location[1]),
            mass=mass,
            friction=friction_coeff * 0.1,  # Base friction
            drag=0.05,  # Air resistance
            enable_rotation=True,
            rotation=location[2]
        )
        
        # Car-specific properties
        self.length = length
        self.width = width
        self.color = color
        self.pull = pull  # Engine force
        self.base_friction = friction_coeff
        self.brake_multiplier = brake_multiplier
        self.steering_speed = 0.07
        
        # Input states
        self.gas_pressed = False
        self.brake_pressed = False
        self.steer_left = False
        self.steer_right = False
        
        # Collision shape
        self.collision_shape = RectShape(Rect(
            self.physics.position.x - self.width/2,
            self.physics.position.y - self.length/2,
            self.width,
            self.length
        ))
    
    def getType(self) -> int:
        return self._type
    
    def handle_events(self):
        import pygame
        
        keys = pygame.key.get_pressed()
        
        # Reset input states first
        self.gas_pressed = False
        self.brake_pressed = False
        self.steer_left = False
        self.steer_right = False
        
        # Check for input keys and update states
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.gas_pressed = True
        
        if keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_SPACE]:
            self.brake_pressed = True
            
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.steer_left = True
            
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.steer_right = True
    
    def update(self, screen: SurfaceType, world: EngineAPI, dt: float) -> GameObjectUpdateRes:
        self._apply_car_forces(dt)
        self.collision_shape.position = self.physics.position
        return self.physics.integrate(dt)
    
    def _apply_car_forces(self, dt: float):
        if self.gas_pressed:
            engine_force = Vector2(
                self.pull * math.cos(self.physics.rotation),
                self.pull * math.sin(self.physics.rotation)
            )
            self.physics.apply_force(engine_force)
        
        # Apply steering
        if self.steer_left:
            self.physics.rotation -= self.steering_speed * dt * 60  # Normalize for dt
        if self.steer_right:
            self.physics.rotation += self.steering_speed * dt * 60
        
        # Normalize rotation
        self.physics.rotation = (self.physics.rotation + 2 * math.pi) % (2 * math.pi)
        
        # Apply braking (increase friction)
        if self.brake_pressed:
            self.physics.friction = self.base_friction * self.brake_multiplier
        else:
            self.physics.friction = self.base_friction
    
    def draw(self, screen: SurfaceType, world: EngineAPI):
        # Calculate car corners for rotated rectangle
        cos_ori = math.cos(self.physics.rotation)
        sin_ori = math.sin(self.physics.rotation)
        half_width = self.length / 2
        half_length = self.width / 2
        
        # Define corners relative to center
        corners = [
            (-half_width, -half_length),  # Top-left
            (half_width, -half_length),   # Top-right
            (half_width, half_length),    # Bottom-right
            (-half_width, half_length)    # Bottom-left
        ]
        
        # Rotate and translate corners
        rotated_corners = []
        for x, y in corners:
            rotated_x = self.physics.position.x + x * cos_ori - y * sin_ori
            rotated_y = self.physics.position.y + x * sin_ori + y * cos_ori
            rotated_corners.append(Vector2(rotated_x, rotated_y))
        
        # Draw car body
        world.draw_polygon(self.color, rotated_corners)
        
        # Draw front indicator (red triangle)
        front_center_x = self.physics.position.x + half_length * cos_ori
        front_center_y = self.physics.position.y + half_length * sin_ori
        
        front_triangle = [
            Vector2(
                front_center_x + half_width * 0.5 * sin_ori,
                front_center_y - half_width * 0.5 * cos_ori
            ),
            Vector2(
                front_center_x - half_width * 0.5 * sin_ori,
                front_center_y + half_width * 0.5 * cos_ori
            ),
            Vector2(
                front_center_x + half_length * 0.5 * cos_ori,
                front_center_y + half_length * 0.5 * sin_ori
            )
        ]
        world.draw_polygon(Color(255, 0, 0), front_triangle)
    
    def signal(self, world: EngineAPI, signal: int, data) -> None:
        if signal == CarSignals.GAS:
            self.gas_pressed = True
        elif signal == CarSignals.RELEASE_GAS:
            self.gas_pressed = False
        elif signal == CarSignals.BRAKE:
            self.brake_pressed = True
        elif signal == CarSignals.RELEASE_BRAKE:
            self.brake_pressed = False
        elif signal == CarSignals.STEER_LEFT:
            self.steer_left = True
        elif signal == CarSignals.STEER_RIGHT:
            self.steer_right = True
        elif signal == CarSignals.RELEASE_STEER:
            self.steer_left = False
            self.steer_right = False
    
    def is_collidable(self) -> bool:
        return True
    def get_collision_shape(self) -> CollisionShape:
        return self.collision_shape
    
    def on_collision(self, engine: EngineAPI, other: GameObject, collision) -> None:
        if other.getType() == GameObjectType.WALL: # Player looses if crashed to the wall
            engine.signal(self._id, EngineSignal.QUIT, None)
        if collision.normal.length() > 0:
            # Simple collision response - reduce velocity in collision direction
            relative_velocity = self.physics.velocity
            velocity_in_normal = relative_velocity.dot(collision.normal)
            
            if velocity_in_normal > 0:  # Objects moving towards each other
                # Apply impulse to separate
                impulse_magnitude = velocity_in_normal * 0.8  # Restitution coefficient
                impulse = collision.normal * impulse_magnitude
                self.physics.apply_impulse(-impulse)
    
    def gas(self):
        self.gas_pressed = True
    
    def brake(self):
        self.brake_pressed = True
    
    def steerleft(self):
        self.steer_left = True
        self.steer_right = False
    
    def steerright(self):
        self.steer_right = True
        self.steer_left = False
    
    def release_all_inputs(self):
        self.gas_pressed = False
        self.brake_pressed = False
        self.steer_left = False
        self.steer_right = False
    
    def tostart(self, location):
        """Reset car to starting position"""
        self.physics.position = Vector2(location[0], location[1])
        self.physics.rotation = location[2]
        self.physics.velocity = Vector2(0, 0)
        self.physics.angular_velocity = 0.0
        self.physics.forces = Vector2(0, 0)
        self.release_all_inputs()

    @property
    def vx(self):
        return self.physics.velocity.x
    
    @property
    def vy(self):
        return self.physics.velocity.y