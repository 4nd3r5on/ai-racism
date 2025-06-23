from pygame import Surface, Vector2
from engine.interfaces import CollisionInfo, EngineAPI, GameObject, GameObjectUpdateRes
from engine.primitives import CircleShape


class DummyGameObject(GameObject):
    def __init__(self, pos: Vector2, radius: float, obj_type: int):
        self._id = 0
        self.pos = pos
        self.radius = radius
        self.obj_type = obj_type
        self.shape = CircleShape(pos, radius)

    def getType(self) -> int:
        return self.obj_type

    def handle_events(self) -> None:
        pass

    def update(self, screen: Surface, world: EngineAPI, dt: float) -> GameObjectUpdateRes:
        # Simulate movement for testing (no-op for now)
        return GameObjectUpdateRes(object_moved=True)

    def draw(self, screen: Surface, world: EngineAPI) -> None:
        pass

    def signal(self, world: EngineAPI, signal: int, data) -> None:
        pass

    def is_collidable(self) -> bool:
        return True

    def get_collision_shape(self):
        return self.shape

    def on_collision(self, engine: EngineAPI, other: GameObject, collision: CollisionInfo) -> None:
        pass