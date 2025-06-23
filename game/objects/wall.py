from pygame import SurfaceType, Vector2, Color

from engine.interfaces import CollisionInfo, CollisionShape, EngineAPI, GameObject, GameObjectUpdateRes
from engine.primitives import LineShape
from game.objects.objects import GameObjectType


class Wall(GameObject):
    _type = GameObjectType.WALL
    visible = True

    def __init__(self, start: Vector2, end: Vector2, color: Color = Color(255, 255, 255)):
        self.start_pos = start
        self.end_pos = end
        self.color = color
        self.width = 2
        self._collision_shape = LineShape(start, end)
    
    def getType(self) -> int:
        return self._type
    
    def draw(self, screen: SurfaceType, world: EngineAPI):
        if self.visible:
            world.draw_line(self.color, self.start_pos, self.end_pos, self.width)
    
    def is_collidable(self) -> bool:
        return True
    
    def get_collision_shape(self) -> CollisionShape:
        return self._collision_shape
    
    def on_collision(self, engine: EngineAPI, other: GameObject, collision: CollisionInfo) -> None:
        pass  # Walls don't react to collisions

    # Those do nothing, just to implement the interface
    def handle_events(self) -> None: pass
    def update(self, screen: SurfaceType, world: EngineAPI, dt: float) -> GameObjectUpdateRes | None: pass
    def signal(self, world: EngineAPI, signal: int, data) -> None: pass
