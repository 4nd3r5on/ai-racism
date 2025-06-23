from pygame import Rect, Vector2
from typing import Optional
from engine.interfaces import GameObject

class SpatialQuadTree:
    def __init__(self, bounds: Rect, max_objects: int = 10, max_levels: int = 5, level: int = 0):
        self.bounds = bounds
        self.max_objects = max_objects
        self.max_levels = max_levels
        self.level = level
        self.objects: set[GameObject] = set()
        self.nodes: list[Optional['SpatialQuadTree']] = [None] * 4
        self.vertical_mid = 0
        self.horizontal_mid = 0

    def clear(self):
        self.objects.clear()
        for i in range(4):
            node = self.nodes[i]
            if node is not None:
                node.clear()
                self.nodes[i] = None

    def split(self):
        sub_width = self.bounds.width // 2
        sub_height = self.bounds.height // 2
        x, y = self.bounds.x, self.bounds.y

        self.vertical_mid = x + sub_width
        self.horizontal_mid = y + sub_height

        self.nodes[0] = SpatialQuadTree(Rect(self.vertical_mid, y, sub_width, sub_height),
                                        self.max_objects, self.max_levels, self.level + 1)  # NE
        self.nodes[1] = SpatialQuadTree(Rect(x, y, sub_width, sub_height),
                                        self.max_objects, self.max_levels, self.level + 1)  # NW
        self.nodes[2] = SpatialQuadTree(Rect(x, self.horizontal_mid, sub_width, sub_height),
                                        self.max_objects, self.max_levels, self.level + 1)  # SW
        self.nodes[3] = SpatialQuadTree(Rect(self.vertical_mid, self.horizontal_mid, sub_width, sub_height),
                                        self.max_objects, self.max_levels, self.level + 1)  # SE

    def get_index(self, rect: Rect) -> int:
        in_left = rect.right <= self.vertical_mid
        in_right = rect.left >= self.vertical_mid
        in_top = rect.bottom <= self.horizontal_mid
        in_bottom = rect.top >= self.horizontal_mid

        if in_left:
            if in_top:
                return 1  # NW
            if in_bottom:
                return 2  # SW
        elif in_right:
            if in_top:
                return 0  # NE
            if in_bottom:
                return 3  # SE

        return -1  # Doesn't fully fit

    def insert(self, obj: GameObject):
        shape = obj.get_collision_shape()
        if not shape:
            return

        obj_rect = shape.get_bounding_rect()
        if not self.bounds.colliderect(obj_rect):
            return

        if self.nodes[0] is not None:
            index = self.get_index(obj_rect)
            if index != -1:
                node = self.nodes[index]
                if node is not None:
                    node.insert(obj)
                    return

        self.objects.add(obj)

        if len(self.objects) > self.max_objects and self.level < self.max_levels:
            if self.nodes[0] is None:
                self.split()

            for obj in list(self.objects):
                shape = obj.get_collision_shape()
                if not shape:
                    continue

                obj_rect = shape.get_bounding_rect()
                index = self.get_index(obj_rect)
                if index != -1:
                    node = self.nodes[index]
                    if node is not None:
                        node.insert(obj)
                        self.objects.remove(obj)


    def remove(self, obj: GameObject):
        """Remove an object from the quad tree"""
        shape = obj.get_collision_shape()
        if not shape:
            return
        
        obj_rect = shape.get_bounding_rect()
        self._remove_recursive(obj, obj_rect)

    def _remove_recursive(self, obj: GameObject, obj_rect: Rect):
        if not self.bounds.colliderect(obj_rect):
            return
        
        # Remove from this node
        self.objects.discard(obj)
        
        # Remove from child nodes
        if self.nodes[0] is not None:
            for node in self.nodes:
                if node is not None:
                    node._remove_recursive(obj, obj_rect)

    def update_object(self, obj: GameObject):
        """Remove and re-insert an object (for when it moves)"""
        self.remove(obj)
        self.insert(obj)


    def retrieve(self, obj_rect: Rect) -> set[GameObject]:
        if not self.bounds.colliderect(obj_rect):
            return set()

        found: set[GameObject] = set(self.objects)
        if self.nodes[0] is not None:
            index = self.get_index(obj_rect)
            if index != -1:
                node = self.nodes[index]
                if node is not None:
                    found.update(node.retrieve(obj_rect))
            else:
                for node in self.nodes:
                    if node is not None:
                        found.update(node.retrieve(obj_rect))
        return found

    def retrieve_in_radius(self, center: Vector2, radius: float) -> set[GameObject]:
        query_rect = Rect(center.x - radius, center.y - radius, radius * 2, radius * 2)
        candidates = self.retrieve(query_rect)
        return {
            obj for obj in candidates
            if (shape := obj.get_collision_shape()) and
               (shape.position - center).magnitude() <= radius
        }
