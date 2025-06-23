from enum import IntEnum
from pygame import Color, SurfaceType, Vector2, init
from engine.interfaces import CollisionInfo, CollisionShape, EngineAPI, GameObject, GameObjectUpdateRes
from engine.primitives import LineShape
from game.objects.objects import GameObjectType
from game.signals import EngineSignal

class CheckpointSignal(IntEnum):
    RESET      = 0 # Goes back to initial state
    ACTIVATE   = 1
    DEACTIVATE = 2

class Checkpoint(GameObject):
    _type = GameObjectType.CHECKPOINT
    active = True
    active_color = Color(0, 255, 0)
    inactive_color = Color(60, 60, 60) # Some kinda gray?

    def __init__(self, start: Vector2, end: Vector2, init_active: bool = False):
        self.start_pos = start
        self.end_pos = end
        self.width = 4
        self._collision_shape = LineShape(start, end)

        self.init_active = init_active
        self.active = init_active

    def getType(self) -> int:
        return self._type

    def draw(self, screen: SurfaceType, world: EngineAPI):
        color = self.active_color if self.active else self.inactive_color
        world.draw_line(color, self.start_pos, self.end_pos, self.width)
    
    def is_collidable(self) -> bool:
        return True
    
    def get_collision_shape(self) -> CollisionShape:
        return self._collision_shape
    
    def on_collision(self, engine: EngineAPI, other: GameObject, collision: CollisionInfo) -> None:
        if other.getType() == GameObjectType.CAR:
            engine.signal(self._id, EngineSignal.CHECKPOINT_PASSED, None)

    def signal(self, world: EngineAPI, signal: int, data) -> None:
        if signal == CheckpointSignal.ACTIVATE:
            self.active = True
        elif signal == CheckpointSignal.DEACTIVATE:   
            self.active = False
        elif signal == CheckpointSignal.RESET:
            self.active = self.init_active

    # Those do nothing, just to implement the interface
    def handle_events(self) -> None: pass
    def update(self, screen: SurfaceType, world: EngineAPI, dt: float) -> GameObjectUpdateRes | None: pass