from typing import Sequence
from pygame import Color, Rect, SurfaceType, Vector2
import pygame

from engine.engine import Engine

# Engine that provides graphical capabilities for game engine
class EngineView(Engine):
    screen: SurfaceType
    camera_offset: Vector2 = Vector2(0, 0)
    camera_scale: float = 1.0

    def __init__(self, screen: SurfaceType, world_bounds: Rect) -> None:
        super().__init__(world_bounds)
        self.screen = screen

    # Camera
    def move_camera(self, vec: Vector2) -> None:
        self.camera_offset = self.camera_offset + vec
    def set_camera(self, vec: Vector2) -> None:
        self.camera_offset = vec
    def get_camera_pos(self) -> Vector2:
        return self.camera_offset
    def set_camera_scale(self, scale: float) -> None:
        self.camera_scale = max(0.1, scale)
    def zoom_camera(self, factor: float) -> None:
        self.camera_scale *= factor

    # Drawing stuff on screen
    def draw_polygon(self, color: Color, points: Sequence[Vector2]) -> None:
        points_with_offset_and_scale = [(point - self.camera_offset) * self.camera_scale for point in points]
        pygame.draw.polygon(self.screen, color, points_with_offset_and_scale)
    def draw_line(self, color: Color, start: Vector2, end: Vector2, width: int = 1) -> None:
        start_transformed = (start - self.camera_offset) * self.camera_scale
        end_transformed = (end - self.camera_offset) * self.camera_scale
        scaled_width = max(1, int(width * self.camera_scale))
        pygame.draw.line(self.screen, color, start_transformed, end_transformed, scaled_width)
    def draw_circle(self, color: Color, center: Vector2, radius: float) -> None:
        scaled_center = (center - self.camera_offset) * self.camera_scale
        scaled_radius = radius * self.camera_scale
        pygame.draw.circle(self.screen, color, scaled_center, scaled_radius)
    def draw_rect(self, color: Color, rect: Rect, width: int = 0) -> None:
        transformed_rect = Rect(
            (Vector2(rect.topleft) - self.camera_offset) * self.camera_scale,
            Vector2(rect.size) * self.camera_scale
        )
        pygame.draw.rect(self.screen, color, transformed_rect, max(1, int(width * self.camera_scale)) if width else 0)
    def draw_ellipse(self, color: Color, rect: Rect, width: int = 0) -> None:
        transformed_rect = Rect(
            (Vector2(rect.topleft) - self.camera_offset) * self.camera_scale,
            Vector2(rect.size) * self.camera_scale
        )
        pygame.draw.ellipse(self.screen, color, transformed_rect, max(1, int(width * self.camera_scale)) if width else 0)
    def draw_arc(self, color: Color, rect: Rect, start_angle: float, end_angle: float, width: int = 1) -> None:
        transformed_rect = Rect(
            (Vector2(rect.topleft) - self.camera_offset) * self.camera_scale,
            Vector2(rect.size) * self.camera_scale
        )
        pygame.draw.arc(self.screen, color, transformed_rect, start_angle, end_angle, max(1, int(width * self.camera_scale)))

    def draw(self):
        for gameObj in list(self.game_objs.values()):
            gameObj.draw(self.screen, self)