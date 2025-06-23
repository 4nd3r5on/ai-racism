from typing import Any, Callable, Optional

from pygame import Rect, Vector2

from engine.primitives import CircleShape, LineShape, PolygonShape, RectShape
from engine.interfaces import CollisionInfo, GameObject, CollisionShape
from engine.spatial import SpatialQuadTree


def circle_intersects_circle(s1: CircleShape, s2: CircleShape) -> Optional[CollisionInfo]:
    """Check collision between two circles"""
    distance_vector = s2.position - s1.position
    distance = distance_vector.length()
    combined_radius = s1.radius + s2.radius
    
    if distance > combined_radius:
        return None
    
    # Handle case where circles are at same position
    if distance < 1e-6:
        normal = Vector2(1, 0)
        penetration = combined_radius
    else:
        normal = distance_vector / distance
        penetration = combined_radius - distance
    
    # Contact point is on the line between centers
    contact_point = s1.position + normal * s1.radius
    
    return CollisionInfo(
        contact_points=[contact_point],
        normal=normal,
        penetration=penetration
    )

def rect_intersects_circle(s1: RectShape, s2: CircleShape) -> Optional[CollisionInfo]:
    """Check collision between rectangle and circle"""
    # Find closest point on rectangle to circle center
    closest_x = max(s1.rect.x, min(s2.position.x, s1.rect.x + s1.rect.width))
    closest_y = max(s1.rect.y, min(s2.position.y, s1.rect.y + s1.rect.height))
    closest_point = Vector2(closest_x, closest_y)
    
    distance_vector = s2.position - closest_point
    distance = distance_vector.length()
    
    if distance > s2.radius:
        return None
    
    # Handle case where circle center is inside rectangle
    if distance < 1e-6:
        # Find shortest distance to rectangle edge
        distances = [
            s2.position.x - s1.rect.x,  # left
            (s1.rect.x + s1.rect.width) - s2.position.x,  # right
            s2.position.y - s1.rect.y,  # top
            (s1.rect.y + s1.rect.height) - s2.position.y   # bottom
        ]
        min_dist_idx = distances.index(min(distances))
        
        normals = [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1)]
        normal = normals[min_dist_idx]
        penetration = s2.radius + distances[min_dist_idx]
        contact_point = s2.position - normal * s2.radius
    else:
        normal = distance_vector / distance
        penetration = s2.radius - distance
        contact_point = closest_point
    
    return CollisionInfo(
        contact_points=[contact_point],
        normal=normal,
        penetration=penetration
    )

def line_intersects_circle(s1: LineShape, s2: CircleShape) -> Optional[CollisionInfo]:
    """Check collision between line segment and circle"""
    line_vec = s1.end - s1.start
    to_circle = s2.position - s1.start
    
    # Project circle center onto line
    line_length_sq = line_vec.length_squared()
    if line_length_sq < 1e-6:
        # Line is a point
        distance = (s2.position - s1.start).length()
        if distance > s2.radius:
            return None
        normal = (s2.position - s1.start).normalize() if distance > 1e-6 else Vector2(1, 0)
        return CollisionInfo(
            contact_points=[s1.start],
            normal=normal,
            penetration=s2.radius - distance
        )
    
    t = max(0, min(1, to_circle.dot(line_vec) / line_length_sq))
    closest_point = s1.start + line_vec * t
    
    distance_vector = s2.position - closest_point
    distance = distance_vector.length()
    
    if distance > s2.radius:
        return None
    
    if distance < 1e-6:
        # Circle center is on the line
        normal = Vector2(-line_vec.y, line_vec.x).normalize()
    else:
        normal = distance_vector / distance
    
    return CollisionInfo(
        contact_points=[closest_point],
        normal=normal,
        penetration=s2.radius - distance
    )

def polygon_intersects_circle(s1: PolygonShape, s2: CircleShape) -> Optional[CollisionInfo]:
    """Check collision between polygon and circle using SAT"""
    min_penetration = float('inf')
    collision_normal = Vector2(0, 0)
    contact_point = Vector2(0, 0)
    
    # Check each edge of the polygon
    for i in range(len(s1.vertices)):
        v1 = s1.vertices[i]
        v2 = s1.vertices[(i + 1) % len(s1.vertices)]
        
        edge = v2 - v1
        normal = Vector2(-edge.y, edge.x).normalize()
        
        # Project polygon onto normal
        poly_min = poly_max = v1.dot(normal)
        for vertex in s1.vertices[1:]:
            proj = vertex.dot(normal)
            poly_min = min(poly_min, proj)
            poly_max = max(poly_max, proj)
        
        # Project circle onto normal
        circle_center_proj = s2.position.dot(normal)
        circle_min = circle_center_proj - s2.radius
        circle_max = circle_center_proj + s2.radius
        
        # Check for separation
        if poly_max < circle_min or circle_max < poly_min:
            return None
        
        # Calculate penetration
        penetration = min(poly_max - circle_min, circle_max - poly_min)
        if penetration < min_penetration:
            min_penetration = penetration
            collision_normal = normal
            
            # Find contact point on polygon edge
            line_to_circle = s2.position - v1
            t = max(0, min(1, line_to_circle.dot(edge) / edge.length_squared()))
            contact_point = v1 + edge * t
    
    # Check if circle center is closest to a vertex
    for vertex in s1.vertices:
        to_vertex = vertex - s2.position
        distance = to_vertex.length()
        if distance < s2.radius:
            penetration = s2.radius - distance
            if penetration < min_penetration:
                min_penetration = penetration
                collision_normal = to_vertex.normalize() if distance > 1e-6 else Vector2(1, 0)
                contact_point = vertex
    
    return CollisionInfo(
        contact_points=[contact_point],
        normal=collision_normal,
        penetration=min_penetration
    )

def rect_intersects_rect(s1: RectShape, s2: RectShape) -> Optional[CollisionInfo]:
    """Check collision between two rectangles"""
    # Check for overlap
    if (s1.rect.x + s1.rect.width < s2.rect.x or 
        s2.rect.x + s2.rect.width < s1.rect.x or
        s1.rect.y + s1.rect.height < s2.rect.y or 
        s2.rect.y + s2.rect.height < s1.rect.y):
        return None
    
    # Calculate overlap distances
    left_overlap = (s1.rect.x + s1.rect.width) - s2.rect.x
    right_overlap = (s2.rect.x + s2.rect.width) - s1.rect.x
    top_overlap = (s1.rect.y + s1.rect.height) - s2.rect.y
    bottom_overlap = (s2.rect.y + s2.rect.height) - s1.rect.y
    
    # Find minimum overlap (penetration)
    penetrations = [left_overlap, right_overlap, top_overlap, bottom_overlap]
    min_penetration = min(penetrations)
    min_idx = penetrations.index(min_penetration)
    
    # Determine normal and contact point
    if min_idx == 0:  # Left
        normal = Vector2(-1, 0)
        contact_point = Vector2(s2.rect.x, s1.rect.y + s1.rect.height / 2)
    elif min_idx == 1:  # Right
        normal = Vector2(1, 0)
        contact_point = Vector2(s2.rect.x + s2.rect.width, s1.rect.y + s1.rect.height / 2)
    elif min_idx == 2:  # Top
        normal = Vector2(0, -1)
        contact_point = Vector2(s1.rect.x + s1.rect.width / 2, s2.rect.y)
    else:  # Bottom
        normal = Vector2(0, 1)
        contact_point = Vector2(s1.rect.x + s1.rect.width / 2, s2.rect.y + s2.rect.height)
    
    return CollisionInfo(
        contact_points=[contact_point],
        normal=normal,
        penetration=min_penetration
    )

def rect_intersects_line(s1: RectShape, s2: LineShape) -> Optional[CollisionInfo]:
    """Check collision between rectangle and line segment"""
    # Check if line endpoints are inside rectangle
    def point_in_rect(point: Vector2, rect: Rect) -> bool:
        return (rect.x <= point.x <= rect.x + rect.width and 
                rect.y <= point.y <= rect.y + rect.height)
    
    start_inside = point_in_rect(s2.start, s1.rect)
    end_inside = point_in_rect(s2.end, s1.rect)
    
    if start_inside and end_inside:
        # Entire line is inside rectangle
        line_vec = s2.end - s2.start
        line_center = (s2.start + s2.end) / 2
        
        # Find closest rectangle edge
        distances = [
            line_center.x - s1.rect.x,  # left
            (s1.rect.x + s1.rect.width) - line_center.x,  # right
            line_center.y - s1.rect.y,  # top
            (s1.rect.y + s1.rect.height) - line_center.y   # bottom
        ]
        min_dist_idx = distances.index(min(distances))
        normals = [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1)]
        
        return CollisionInfo(
            contact_points=[line_center],
            normal=normals[min_dist_idx],
            penetration=distances[min_dist_idx]
        )
    
    # Check line-rectangle edge intersections
    rect_edges = [
        (Vector2(s1.rect.x, s1.rect.y), Vector2(s1.rect.x + s1.rect.width, s1.rect.y)),  # top
        (Vector2(s1.rect.x + s1.rect.width, s1.rect.y), Vector2(s1.rect.x + s1.rect.width, s1.rect.y + s1.rect.height)),  # right
        (Vector2(s1.rect.x + s1.rect.width, s1.rect.y + s1.rect.height), Vector2(s1.rect.x, s1.rect.y + s1.rect.height)),  # bottom
        (Vector2(s1.rect.x, s1.rect.y + s1.rect.height), Vector2(s1.rect.x, s1.rect.y))   # left
    ]
    
    edge_normals = [Vector2(0, -1), Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0)]
    
    for i, (edge_start, edge_end) in enumerate(rect_edges):
        # Check line-line intersection
        intersection = line_line_intersection(s2.start, s2.end, edge_start, edge_end)
        if intersection:
            return CollisionInfo(
                contact_points=[intersection],
                normal=edge_normals[i],
                penetration=0.1  # Small penetration for line intersections
            )
    
    return None

def rect_intersects_polygon(s1: RectShape, s2: PolygonShape) -> Optional[CollisionInfo]:
    """Check collision between rectangle and polygon using SAT"""
    # Convert rectangle to polygon for SAT algorithm
    rect_vertices = [
        Vector2(s1.rect.x, s1.rect.y),
        Vector2(s1.rect.x + s1.rect.width, s1.rect.y),
        Vector2(s1.rect.x + s1.rect.width, s1.rect.y + s1.rect.height),
        Vector2(s1.rect.x, s1.rect.y + s1.rect.height)
    ]
    
    # Create temporary polygon shapes
    temp_rect = PolygonShape(rect_vertices)
    return polygon_intersects_polygon(temp_rect, s2)

def line_intersects_line(s1: LineShape, s2: LineShape) -> Optional[CollisionInfo]:
    """Check collision between two line segments"""
    intersection = line_line_intersection(s1.start, s1.end, s2.start, s2.end)
    if intersection:
        # Calculate normal (perpendicular to first line)
        line1_vec = s1.end - s1.start
        normal = Vector2(-line1_vec.y, line1_vec.x).normalize()
        
        return CollisionInfo(
            contact_points=[intersection],
            normal=normal,
            penetration=0.1  # Small penetration for line intersections
        )
    return None

def line_intersects_polygon(s1: LineShape, s2: PolygonShape) -> Optional[CollisionInfo]:
    """Check collision between line segment and polygon"""
    # Check if line intersects any polygon edge
    for i in range(len(s2.vertices)):
        v1 = s2.vertices[i]
        v2 = s2.vertices[(i + 1) % len(s2.vertices)]
        
        intersection = line_line_intersection(s1.start, s1.end, v1, v2)
        if intersection:
            # Calculate normal (perpendicular to polygon edge)
            edge_vec = v2 - v1
            normal = Vector2(-edge_vec.y, edge_vec.x).normalize()
            
            return CollisionInfo(
                contact_points=[intersection],
                normal=normal,
                penetration=0.1  # Small penetration for line intersections
            )
    
    return None

def polygon_intersects_polygon(s1: PolygonShape, s2: PolygonShape) -> Optional[CollisionInfo]:
    """Check collision between two polygons using SAT (Separating Axis Theorem)"""
    min_penetration = float('inf')
    collision_normal = Vector2(0, 0)
    
    # Check all edges of both polygons
    all_vertices = [s1.vertices, s2.vertices]
    
    for poly_idx, vertices in enumerate(all_vertices):
        for i in range(len(vertices)):
            # Get edge normal
            edge = vertices[(i + 1) % len(vertices)] - vertices[i]
            normal = Vector2(-edge.y, edge.x).normalize()
            
            # Project both polygons onto this normal
            poly1_min = poly1_max = s1.vertices[0].dot(normal)
            for vertex in s1.vertices[1:]:
                proj = vertex.dot(normal)
                poly1_min = min(poly1_min, proj)
                poly1_max = max(poly1_max, proj)
            
            poly2_min = poly2_max = s2.vertices[0].dot(normal)
            for vertex in s2.vertices[1:]:
                proj = vertex.dot(normal)
                poly2_min = min(poly2_min, proj)
                poly2_max = max(poly2_max, proj)
            
            # Check for separation
            if poly1_max < poly2_min or poly2_max < poly1_min:
                return None
            
            # Calculate penetration
            penetration = min(poly1_max - poly2_min, poly2_max - poly1_min)
            if penetration < min_penetration:
                min_penetration = penetration
                collision_normal = normal
    
    # Find contact point (approximate)
    contact_point = (s1.position + s2.position) / 2
    
    return CollisionInfo(
        contact_points=[contact_point],
        normal=collision_normal,
        penetration=min_penetration
    )

def line_line_intersection(p1: Vector2, p2: Vector2, p3: Vector2, p4: Vector2) -> Optional[Vector2]:
    """Helper function to find intersection point between two line segments"""
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y
    x4, y4 = p4.x, p4.y
    
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-6:
        return None  # Lines are parallel
    
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    
    if 0 <= t <= 1 and 0 <= u <= 1:
        # Intersection point
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        return Vector2(x, y)
    
    return None


type CollisionDetectorFunc = Callable[[Any, Any], Optional[CollisionInfo]]

class CollisionDetector:
    _registry: dict[tuple[type, type], Callable[[Any, Any], Optional[CollisionInfo]]] = {}

    def __init__(self, default_detectors: list[tuple[type, type, CollisionDetectorFunc]] = []):
        for type_a, type_b, handler in default_detectors:
            self.add(type_a, type_b, handler)

    @classmethod
    def add(cls, type_a: type, type_b: type, handler: Callable[[Any, Any], Optional[CollisionInfo]]):
        cls._registry[(type_a, type_b)] = handler
        cls._registry[(type_b, type_a)] = lambda b, a: handler(a, b)

    @classmethod
    def detect(cls, a: Any, b: Any) -> Optional[CollisionInfo]:
        handler = cls._registry.get((type(a), type(b)))
        if not handler:
            raise NotImplementedError(f"No collision handler for {type(a).__name__} x {type(b).__name__}")
        return handler(a, b)


default_detectors: list[tuple[type, type, CollisionDetectorFunc]] = [
    (CircleShape, CircleShape, circle_intersects_circle),
    (RectShape, CircleShape, rect_intersects_circle),
    (LineShape, CircleShape, line_intersects_circle),
    (PolygonShape, CircleShape, polygon_intersects_circle),
    (RectShape, RectShape, rect_intersects_rect),
    (RectShape, LineShape, rect_intersects_line),
    (RectShape, PolygonShape, rect_intersects_polygon),
    (LineShape, LineShape, line_intersects_line),
    (LineShape, PolygonShape, line_intersects_polygon),
    (PolygonShape, PolygonShape, polygon_intersects_polygon),
]
