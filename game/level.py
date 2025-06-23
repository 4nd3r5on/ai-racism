from dataclasses import dataclass
import pickle

from pygame import Rect, Vector2

@dataclass
class Line():
    start: Vector2
    end: Vector2

@dataclass
class WallData(Line):
    pass
@dataclass
class CheckpointData(Line):
    pass

@dataclass
class CarData():
    car_start: Vector2
    car_rotation_rads: float
    car_width: int = 20
    car_length: int = 40

@dataclass
class LevelData():
    walls: list[WallData]
    checkpoints: list[CheckpointData]
    world_bounds: Rect
    car: CarData

def load_level(file_path: str) -> LevelData:
    with open(file_path, 'rb') as f:
        level_data: LevelData = pickle.load(f)
    return level_data