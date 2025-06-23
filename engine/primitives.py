import math
from pygame import Vector2, Rect
from engine.interfaces import CollisionShape, RaycastHit

class CircleShape(CollisionShape):
    def __init__(self, position: Vector2, radius: float):
        super().__init__(position)
        self.radius = radius
    
    def get_bounding_rect(self) -> Rect:
        return Rect(
            self.position.x - self.radius,
            self.position.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )
    
    def contains_point(self, point: Vector2) -> bool:
        distance_squared = (point.x - self.position.x) ** 2 + (point.y - self.position.y) ** 2
        return distance_squared <= self.radius ** 2

    def intersects_ray(self, origin: Vector2, direction: Vector2, max_distance: float) -> RaycastHit | None:
        # Vector from ray origin to circle center
        oc = origin - self.position
        
        # Quadratic equation coefficients for ray-circle intersection
        a = direction.dot(direction)
        b = 2.0 * oc.dot(direction)
        c = oc.dot(oc) - self.radius * self.radius
        
        discriminant = b * b - 4 * a * c
        
        if discriminant < 0:
            return None
        
        # Calculate closest intersection point
        sqrt_discriminant = math.sqrt(discriminant)
        t1 = (-b - sqrt_discriminant) / (2 * a)
        t2 = (-b + sqrt_discriminant) / (2 * a)
        
        # Find the closest positive intersection within max_distance
        t = None
        if t1 >= 0 and t1 <= max_distance:
            t = t1
        elif t2 >= 0 and t2 <= max_distance:
            t = t2
        
        if t is None:
            return None
        
        # Calculate intersection point and normal
        hit_point = origin + direction * t
        normal = (hit_point - self.position).normalize()
        
        return RaycastHit(
            point=hit_point,
            normal=normal,
            distance=t
        )


class RectShape(CollisionShape):
    def __init__(self, rect: Rect):
        super().__init__(Vector2(rect.center))
        self.rect = rect
    
    def get_bounding_rect(self) -> Rect:
        return self.rect
    
    def contains_point(self, point: Vector2) -> bool:
        return self.rect.collidepoint(point.x, point.y)
    
    def intersects_ray(self, origin: Vector2, direction: Vector2, max_distance: float) -> RaycastHit | None:
        # Ray-AABB intersection using slab method
        if direction.x == 0 and direction.y == 0:
            return None
        
        # Calculate intersection parameters for each axis
        if direction.x != 0:
            t_min_x = (self.rect.left - origin.x) / direction.x
            t_max_x = (self.rect.right - origin.x) / direction.x
            if t_min_x > t_max_x:
                t_min_x, t_max_x = t_max_x, t_min_x
        else:
            if origin.x < self.rect.left or origin.x > self.rect.right:
                return None
            t_min_x = float('-inf')
            t_max_x = float('inf')
        
        if direction.y != 0:
            t_min_y = (self.rect.top - origin.y) / direction.y
            t_max_y = (self.rect.bottom - origin.y) / direction.y
            if t_min_y > t_max_y:
                t_min_y, t_max_y = t_max_y, t_min_y
        else:
            if origin.y < self.rect.top or origin.y > self.rect.bottom:
                return None
            t_min_y = float('-inf')
            t_max_y = float('inf')
        
        # Find intersection of the slabs
        t_min = max(t_min_x, t_min_y)
        t_max = min(t_max_x, t_max_y)
        
        # Check if intersection exists and is in front of ray origin
        if t_max < 0 or t_min > t_max:
            return None
        
        # Get the closest positive intersection within max_distance
        t = t_min if t_min >= 0 else t_max
        if t > max_distance:
            return None
        
        # Calculate intersection point
        hit_point = origin + direction * t
        
        # Calculate normal based on which face was hit
        normal = Vector2(0, 0)
        if abs(hit_point.x - self.rect.left) < 1e-6:
            normal = Vector2(-1, 0)
        elif abs(hit_point.x - self.rect.right) < 1e-6:
            normal = Vector2(1, 0)
        elif abs(hit_point.y - self.rect.top) < 1e-6:
            normal = Vector2(0, -1)
        elif abs(hit_point.y - self.rect.bottom) < 1e-6:
            normal = Vector2(0, 1)
        
        return RaycastHit(
            point=hit_point,
            normal=normal,
            distance=t
        )


class PolygonShape(CollisionShape):
    def __init__(self, vertices: list[Vector2]):
        center = sum(vertices, Vector2(0, 0)) / len(vertices)
        super().__init__(center)
        self.vertices = vertices
    
    def get_bounding_rect(self) -> Rect:
        if not self.vertices:
            return Rect(0, 0, 0, 0)
        
        min_x = min(v.x for v in self.vertices)
        max_x = max(v.x for v in self.vertices)
        min_y = min(v.y for v in self.vertices)
        max_y = max(v.y for v in self.vertices)
        
        return Rect(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def contains_point(self, point: Vector2) -> bool:
        # Ray casting algorithm for point-in-polygon test
        x, y = point.x, point.y
        n = len(self.vertices)
        inside = False
        
        p1x, p1y = self.vertices[0].x, self.vertices[0].y
        for i in range(1, n + 1):
            p2x, p2y = self.vertices[i % n].x, self.vertices[i % n].y
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def intersects_ray(self, origin: Vector2, direction: Vector2, max_distance: float) -> RaycastHit | None:
        # Ray-polygon intersection by testing each edge
        min_t = float('inf')
        hit_normal = Vector2(0, 0)
        
        n = len(self.vertices)
        for i in range(n):
            # Get edge from vertex i to vertex (i+1)
            v1 = self.vertices[i]
            v2 = self.vertices[(i + 1) % n]
            
            # Ray-line segment intersection
            edge_dir = v2 - v1
            h = Vector2(-direction.y, direction.x)  # Perpendicular to ray direction
            
            a = edge_dir.dot(h)
            if abs(a) < 1e-10:  # Ray is parallel to edge
                continue
            
            f = 1.0 / a
            s = origin - v1
            u = f * s.dot(h)
            
            if u < 0.0 or u > 1.0:  # Intersection not on edge
                continue
            
            q = Vector2(-edge_dir.y, edge_dir.x)  # Perpendicular to edge
            v = f * direction.dot(q)
            
            if v > 0:  # Intersection is in ray direction
                t = f * s.dot(q)
                if t < min_t and t <= max_distance:
                    min_t = t
                    # Calculate normal (perpendicular to edge, pointing inward)
                    edge_normal = Vector2(-edge_dir.y, edge_dir.x).normalize()
                    # Ensure normal points away from polygon center
                    edge_center = (v1 + v2) / 2
                    to_center = self.position - edge_center
                    if edge_normal.dot(to_center) < 0:
                        edge_normal = -edge_normal
                    hit_normal = edge_normal
        
        if min_t == float('inf'):
            return None
        
        hit_point = origin + direction * min_t
        return RaycastHit(
            point=hit_point,
            normal=hit_normal,
            distance=min_t
        )


class LineShape(CollisionShape):
    def __init__(self, start: Vector2, end: Vector2):
        mid = (start + end) / 2
        super().__init__(mid)
        self.start = start
        self.end = end

    def get_bounding_rect(self) -> Rect:
        left = min(self.start.x, self.end.x)
        top = min(self.start.y, self.end.y)
        width = abs(self.start.x - self.end.x)
        height = abs(self.start.y - self.end.y)
        return Rect(left, top, width or 1, height or 1)

    # Check if point is on the line segment using cross product and projection
    def contains_point(self, point: Vector2) -> bool:
        line = self.end - self.start
        to_point = point - self.start
        cross = abs(line.cross(to_point))
        if cross > 1e-6:
            return False
        dot = to_point.dot(line)
        if dot < 0 or dot > line.length_squared():
            return False
        return True
    
    def intersects_ray(self, origin: Vector2, direction: Vector2, max_distance: float) -> RaycastHit | None:
        # Ray-line segment intersection
        line_dir = self.end - self.start
        h = Vector2(-direction.y, direction.x)  # Perpendicular to ray direction
        
        a = line_dir.dot(h)
        if abs(a) < 1e-10:  # Ray is parallel to line
            return None
        
        f = 1.0 / a
        s = origin - self.start
        u = f * s.dot(h)
        
        if u < 0.0 or u > 1.0:  # Intersection not on line segment
            return None
        
        q = Vector2(-line_dir.y, line_dir.x)  # Perpendicular to line
        v = f * direction.dot(q)
        
        if v <= 0:  # Intersection is behind ray origin
            return None
        
        t = f * s.dot(q)
        if t > max_distance:  # Intersection beyond max distance
            return None
        
        # Calculate intersection point and normal
        hit_point = origin + direction * t
        normal = Vector2(-line_dir.y, line_dir.x).normalize()
        
        return RaycastHit(
            point=hit_point,
            normal=normal,
            distance=t
        )