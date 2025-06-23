from dataclasses import dataclass
from pygame import Color, Rect, SurfaceType
import pygame
from engine.interfaces import GameObject
from engine.view import EngineView
from game.level import LevelData, WallData
from game.objects.checkpoints import Checkpoint, CheckpointSignal
from game.signals import EngineSignal

class Level():
    world_bounds: Rect
    wallas = []

@dataclass
class GameScore():
    pass

class Game(EngineView):
    checkpoints_ordered_ids: list[int] = []
    expect_next_checkpoint_idx: int = -1 # references checkpoints_ordered_ids
    background = Color(0, 0, 0, 1)
    running = True

    def __init__(self, screen: SurfaceType, world_bounds: Rect, level: LevelData):
        super().__init__(screen, world_bounds)

    def _init_walls(self, walls_data: list[WallData]):
        pass
    
    def _init_checkpoints(self, walls_data: list[WallData]):
        pass
    
    def _checkpoint_passed(self, obj_id: int, signal: int, data) -> None:
        expect_id = self.checkpoints_ordered_ids[self.expect_next_checkpoint_idx]
        if obj_id != expect_id: # Do nothing if wrong checkpoint
            return
        checkpoint_obj = self.game_objs[obj_id] # passed checkpoint
        # Last checkpoint
        if self.expect_next_checkpoint_idx == len(self.checkpoints_ordered_ids) - 1:
            self.expect_next_checkpoint_idx = 0
            for id in self.checkpoints_ordered_ids:
                obj = self.game_objs[id]
                if obj:
                    obj.signal(self, CheckpointSignal.RESET, None)
        else:
            # Deactivate passed checkpoint
            checkpoint_obj.signal(self, CheckpointSignal.DEACTIVATE, None)
            self.expect_next_checkpoint_idx += 1
            # Activate next endpoint
            next_checkpoint_id = self.checkpoints_ordered_ids[self.expect_next_checkpoint_idx]
            next_checkpoint_obj = self.game_objs[next_checkpoint_id]
            next_checkpoint_obj.signal(self, CheckpointSignal.ACTIVATE, None)
        

    def signal(self, obj_id: int, signal: int, data) -> None:
        if signal == EngineSignal.QUIT:
            self.running = False
            return
        elif signal == EngineSignal.CHECKPOINT_PASSED:
            self._checkpoint_passed(obj_id, signal, data)


    def run_game(self) -> GameScore:
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(90) / 1000
            self.screen.fill(self.background)
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()
            for event in pygame.event.get():
                if event == pygame.QUIT:
                    self.running = False
        
        return GameScore()
        
