from collections import defaultdict
from typing import Sequence
from pygame import Color, SurfaceType, Rect, Vector2
from engine.collision import CollisionDetector, default_detectors
from engine.interfaces import CollisionInfo, GameObject, EngineAPI, RaycastHit
from engine.raycast import raycast
from engine.spatial import SpatialQuadTree


class Engine(EngineAPI):
    next_obj_id: int = 0
    game_objs: dict[int, GameObject] = {}
    game_objs_by_type: dict[int, dict[int, GameObject]] = defaultdict(dict)

    screen: SurfaceType

    spatial_tree: SpatialQuadTree
    collision_detector = CollisionDetector(default_detectors)

    def __init__(self, world_bounds: Rect):
        self.spatial_tree = SpatialQuadTree(world_bounds)

    def _next_id(self) -> int:
        _id = self.next_obj_id
        self.next_obj_id += 1
        return _id

    def add_game_object(self, obj: GameObject) -> int:
        obj_id = self._next_id()
        obj.setId(obj_id)
        self.game_objs_by_type[obj.getType()][obj_id] = obj
        self.game_objs[obj_id] = obj
        return obj_id

    def remove_game_object(self, obj_id: int) -> None:
        if obj_id in self.game_objs:
            obj_to_remove = self.game_objs[obj_id]
            obj_type = obj_to_remove.getType()

            if obj_type in self.game_objs_by_type and obj_id in self.game_objs_by_type[obj_type]:
                del self.game_objs_by_type[obj_type][obj_id]
                if not self.game_objs_by_type[obj_type]:
                    del self.game_objs_by_type[obj_type]
            del self.game_objs[obj_id]

    def get_game_objects_by_type(self, type: int) -> dict[int, GameObject] | None:
        return self.game_objs_by_type.get(type, None)
    def get_game_object_by_id(self, obj_id: int) -> GameObject | None:
        return self.game_objs.get(obj_id)
    def get_objects_in_radius(self, center: Vector2, radius: float) -> set[GameObject]:
        return self.spatial_tree.retrieve_in_radius(center, radius)
    def get_objects_in_rect(self, rect: Rect) -> set[GameObject]:
        return self.spatial_tree.retrieve(rect)
    
    def raycast(
        self,
        origin: Vector2,
        direction: Vector2,
        max_distance: float = float('inf'),
        hits_lim: int = -1,
        ignore_obj_tpyes: set[int] = set(),
    ) -> list[tuple[GameObject, RaycastHit]]:
        return raycast(self.spatial_tree, origin, direction, max_distance, hits_lim, ignore_obj_tpyes)

    def handle_events(self) -> None:
        for gameObj in list(self.game_objs.values()):
            gameObj.handle_events()

    def update(self, dt: float) -> None:
        # Update objects
        objs_moved: list[GameObject] = []
        for game_obj in list(self.game_objs.values()):
            objUpd = game_obj.update(self.screen, self, dt)
            if objUpd and objUpd.object_moved:
                objs_moved.append(game_obj)
        
        # Update moved objects in spatial tree
        for moved_obj in objs_moved:
            self.spatial_tree.update_object(moved_obj)
        
        # Collision detection
        collisions: list[tuple[CollisionInfo, tuple[GameObject, GameObject]]] = []
        for moved_obj in objs_moved:
            shape = moved_obj.get_collision_shape()
            if not shape:
                continue
            shape_bounding_rect = shape.get_bounding_rect()
            collision_objs = self.spatial_tree.retrieve(shape_bounding_rect)
            for collision_obj in collision_objs:
                if moved_obj == collision_obj:  # Don't collide with self
                    continue
                collision = self.collision_detector.detect(moved_obj, collision_obj)
                if not collision:
                    continue
                collisions.append((collision, (moved_obj, collision_obj)))
        
        # Handle collisions
        for collision in collisions:
            collision_info, objs = collision
            obj1, obj2 = objs
            obj1.on_collision(self, obj2, collision_info)
            obj2.on_collision(self, obj1, collision_info)