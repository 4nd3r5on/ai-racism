import time
from typing import Sequence
import pygame
from pygame import Color, Vector2, Rect
from engine.benchmarks.DummyObject import DummyGameObject
from engine.interfaces import GameObject, CollisionInfo
from engine.engine import Engine
from engine.spatial import SpatialQuadTree


class QuadTreeEngine(Engine):
    def __init__(self, world_bounds: Rect):
        super().__init__(world_bounds)
        self.camera_offset = Vector2(0, 0)
        self.camera_scale = 1.0
        # Use the spatial tree normally
        self.spatial_tree = SpatialQuadTree(world_bounds)

    def add_game_object(self, obj: GameObject) -> int:
        obj_id = super().add_game_object(obj)
        self.spatial_tree.insert(obj)
        return obj_id

    def remove_game_object(self, obj_id: int) -> None:
        obj = self.get_game_object_by_id(obj_id)
        if obj:
            self.spatial_tree.remove(obj)
        super().remove_game_object(obj_id)

    def update(self, dt: float) -> None:
        objs_moved: list[GameObject] = []
        for game_obj in list(self.game_objs.values()):
            objUpd = game_obj.update(self.screen, self, dt)
            if objUpd and objUpd.object_moved:
                objs_moved.append(game_obj)

        collisions: list[tuple[CollisionInfo, tuple[GameObject, GameObject]]] = []

        for moved_obj in objs_moved:
            shape_a = moved_obj.get_collision_shape()
            if not shape_a:
                continue

            # Retrieve potential collision candidates using quad tree
            shape_rect = shape_a.get_bounding_rect()
            candidates = self.spatial_tree.retrieve(shape_rect)

            for other_obj in candidates:
                if moved_obj is other_obj or not other_obj.is_collidable():
                    continue

                shape_b = other_obj.get_collision_shape()
                if not shape_b:
                    continue

                try:
                    collision = self.collision_detector.detect(shape_a, shape_b)
                except NotImplementedError:
                    continue

                if collision:
                    collisions.append((collision, (moved_obj, other_obj)))

        for collision_info, (obj1, obj2) in collisions:
            obj1.on_collision(self, obj2, collision_info)
            obj2.on_collision(self, obj1, collision_info)

        # Update spatial tree positions for moved objects
        for moved_obj in objs_moved:
            self.spatial_tree.update_object(moved_obj)

    # View API (no-op)
    def move_camera(self, vec: Vector2) -> None: pass
    def get_camera_pos(self) -> Vector2: return self.camera_offset
    def set_camera(self, vec: Vector2) -> None: self.camera_offset = vec
    def set_camera_scale(self, scale: float) -> None: self.camera_scale = scale
    def zoom_camera(self, factor: float) -> None: self.camera_scale *= factor

    def draw_polygon(self, color: Color, points: Sequence[Vector2]) -> None: pass
    def draw_line(self, color: Color, start: Vector2, end: Vector2, width: int = 1) -> None: pass
    def draw_circle(self, color: Color, center: Vector2, radius: float) -> None: pass
    def draw_rect(self, color: Color, rect: Rect, width: int = 0) -> None: pass
    def draw_ellipse(self, color: Color, rect: Rect, width: int = 0) -> None: pass
    def draw_arc(self, color: Color, rect: Rect, start_angle: float, end_angle: float, width: int = 1) -> None: pass
    def draw(self) -> None: pass
    def signal(self, obj_id: int, signal: int, data) -> None: pass


# Reuse DummyGameObject from your previous code
# ...

def run_benchmark_quadtree(num_objects: int, spacing: int = 50):
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    world_bounds = Rect(0, 0, 10000, 10000)
    engine = QuadTreeEngine(world_bounds)
    engine.screen = screen

    grid_size = int(num_objects ** 0.5)
    for i in range(grid_size):
        for j in range(grid_size):
            if len(engine.game_objs) >= num_objects:
                break
            obj = DummyGameObject(Vector2(i * spacing, j * spacing), radius=10, obj_type=1)
            engine.add_game_object(obj)

    print(f"Benchmarking {num_objects} objects (quad tree)...")
    start = time.time()
    engine.update(0.016)
    end = time.time()
    print(f"Update time: {(end - start) * 1000:.2f} ms")


if __name__ == "__main__":
    for n in [100, 500, 1000, 2000]:
        run_benchmark_quadtree(n)
