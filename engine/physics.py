from pygame import Vector2
from dataclasses import dataclass, field

from engine.interfaces import GameObjectUpdateRes

@dataclass
class PhysicsBody:
    position: Vector2 = field(default_factory=Vector2)
    velocity: Vector2 = field(default_factory=Vector2)
    acceleration: Vector2 = field(default_factory=Vector2)
    mass: float = 1.0
    drag: float = 0.1             # Air resistance
    friction: float = 0.2         # Ground/contact friction
    is_static: bool = False
    
    # Optional angular motion
    rotation: float = 0.0
    angular_velocity: float = 0.0
    angular_drag: float = 0.1
    enable_rotation: bool = False
    
    # Internal
    forces: Vector2 = field(default_factory=Vector2, init=False)
    torque: float = 0.0
    inverse_mass: float = field(init=False)
    
    def __post_init__(self):
        self.inverse_mass = 0.0 if self.is_static or self.mass <= 0 else 1.0 / self.mass
    
    def apply_force(self, force: Vector2):
        if not self.is_static:
            self.forces += force
    
    def apply_impulse(self, impulse: Vector2):
        if not self.is_static:
            self.velocity += impulse * self.inverse_mass
    
    def integrate(self, dt: float) -> GameObjectUpdateRes:
        if self.is_static:
            return GameObjectUpdateRes(object_moved=False)
        
        # Store previous position for comparison
        prev_position = Vector2(self.position.x, self.position.y)
        prev_rotation = self.rotation
        
        # Accumulate acceleration
        acc = self.forces * self.inverse_mass
        
        # Apply friction and drag
        if self.friction > 0:
            acc -= self.velocity * self.friction
        if self.drag > 0:
            acc -= self.velocity * self.drag
        
        # Integrate velocity and position
        self.velocity += acc * dt
        self.position += self.velocity * dt
        
        # Optional rotation
        if self.enable_rotation:
            self.angular_velocity *= max(0.0, 1.0 - self.angular_drag * dt)
            self.rotation += self.angular_velocity * dt
        
        # Clear forces for next frame
        self.forces = Vector2()
        self.acceleration = acc
        
        # Check if object moved (position or rotation changed)
        position_changed = self.position != prev_position
        rotation_changed = self.enable_rotation and self.rotation != prev_rotation
        
        return GameObjectUpdateRes(object_moved=position_changed or rotation_changed)