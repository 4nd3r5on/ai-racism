import pygame
from pygame import Rect, Vector2
from typing import List
from engine.interfaces import GameObject, RaycastHit
from engine.spatial import SpatialQuadTree

def create_ray_bounds(start: Vector2, end: Vector2) -> pygame.Rect:
    min_x = min(start.x, end.x)
    min_y = min(start.y, end.y)
    max_x = max(start.x, end.x)
    max_y = max(start.y, end.y)
    return Rect(min_x, min_y, max_x - min_x, max_y - min_y)

# provided direction vector should be normalazied
# -1 for no limit
def raycast(
    spatial_tree: SpatialQuadTree,
    origin: Vector2,
    direction: Vector2,
    max_distance: float = float('inf'),
    hits_lim: int = -1,
    ignore_obj_tpyes: set[int] = set(),
) -> List[tuple[GameObject, RaycastHit]]:
    hits: List[tuple[GameObject, RaycastHit]] = []
    end_point = origin + direction * max_distance
    ray_bounds = create_ray_bounds(origin, end_point)
    potential_objects = spatial_tree.retrieve(ray_bounds)
    for obj in potential_objects:
        if len(hits) >= hits_lim:
            break
        if obj.getType() in ignore_obj_tpyes:
            continue
        if not obj.is_collidable():
            continue
        shape = obj.get_collision_shape()
        if not shape:
            continue
        hit = shape.intersects_ray(origin, direction, max_distance)
        if hit:
            hits.append((obj, hit))
    return hits