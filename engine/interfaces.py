from abc import abstractmethod, ABC
from collections.abc import Sequence
from dataclasses import dataclass

from pygame import Color, Rect, SurfaceType, Vector2


class EngineAPI(ABC):
    # View API
    @abstractmethod
    def move_camera(self, vec: Vector2) -> None: pass
    @abstractmethod
    def get_camera_pos(self) -> Vector2: pass
    @abstractmethod
    def set_camera(self, vec: Vector2) -> None: pass
    @abstractmethod
    def set_camera_scale(self, scale: float) -> None: pass
    @abstractmethod
    def zoom_camera(self, factor: float) -> None: pass
    @abstractmethod
    def draw_polygon(self, color: Color, points: Sequence[Vector2]) -> None: pass
    @abstractmethod
    def draw_line(self, color: Color, start: Vector2, end: Vector2, width: int = 1) -> None: pass
    @abstractmethod
    def draw_circle(self, color: Color, center: Vector2, radius: float) -> None: pass
    @abstractmethod
    def draw_rect(self, color: Color, rect: Rect, width: int = 0) -> None: pass
    @abstractmethod
    def draw_ellipse(self, color: Color, rect: Rect, width: int = 0) -> None: pass
    @abstractmethod
    def draw_arc(self, color: Color, rect: Rect, start_angle: float, end_angle: float, width: int = 1) -> None: pass
    @abstractmethod
    def draw(self) -> None: pass # To be compatible with the view version

    # Object managment
    @abstractmethod
    def get_game_object_by_id(self, obj_id: int) -> 'GameObject | None': pass
    @abstractmethod
    def add_game_object(self, obj: 'GameObject') -> int: pass
    @abstractmethod
    def remove_game_object(self, obj_id: int) -> None: pass

    # Collisions & raycast
    @abstractmethod
    # direction verctor should be normalized
    # -1 for no limit
    def raycast(
        self,
        origin: Vector2,
        direction: Vector2,
        max_distance: float = float('inf'),
        hits_lim: int = -1,
        ignore_obj_tpyes: set[int] = set()) -> list[tuple['GameObject', 'RaycastHit']]: pass
    @abstractmethod
    def get_objects_in_radius(self, center: Vector2, radius: float) -> set['GameObject']: pass
    @abstractmethod
    def get_objects_in_rect(self, rect: Rect) -> set['GameObject']: pass

    # Communication with the engine
    @abstractmethod
    def signal(self, obj_id: int, signal: int, data) -> None: pass


class GameObject(ABC):
    _id: int = 0
    # ID
    def setId(self, obj_id: int) -> None:
        self._id = obj_id
    def getId(self) -> int:
        return self._id

    # Type
    @abstractmethod
    def getType(self) -> int: pass

    # Engine interactions
    @abstractmethod
    def handle_events(self) -> None: pass
    @abstractmethod
    def update(self, screen: SurfaceType, world: EngineAPI, dt: float) -> 'GameObjectUpdateRes | None': pass
    @abstractmethod
    def draw(self, screen: SurfaceType, world: EngineAPI) -> None: pass
    # If u need communication between objects
    @abstractmethod
    def signal(self, world: EngineAPI, signal: int, data) -> None: pass

    # Collisions
    @abstractmethod
    def is_collidable(self) -> bool: pass
    @abstractmethod
    def get_collision_shape(self) -> 'CollisionShape | None': pass
    @abstractmethod
    def on_collision(self, engine: EngineAPI, other: 'GameObject', collision: 'CollisionInfo') -> None: pass


class CollisionShape(ABC):
    def __init__(self, position: Vector2 = Vector2(0, 0)):
        self.position = position
    @abstractmethod
    def get_bounding_rect(self) -> Rect: pass
    @abstractmethod
    def contains_point(self, point: Vector2) -> bool: pass
    @abstractmethod
    def intersects_ray(self, origin: Vector2, direction: Vector2, max_distance: float) -> 'RaycastHit | None': pass


@dataclass
class RaycastHit:
    point: Vector2
    normal: Vector2
    distance: float

@dataclass
class GameObjectUpdateRes:
    object_moved: bool

@dataclass
class CollisionInfo:
    contact_points: list[Vector2]
    normal: Vector2
    penetration: float