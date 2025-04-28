from typing import BinaryIO, Any, Optional

from mathutils import Vector, Quaternion

from ..io import unpack


class DAT:
    name: str
    version: int
    object_data_pos: int
    render_data_pos: int
    world_info_string: str
    lightmap_grid_size: int
    boundary_min: Vector
    boundary_max: Vector

    quad_tree: Any
    world_models: list['WorldModel']
    world_objects: list['WorldObject']

    def __init__(self):
        self.name = ''
        self.version = 0
        self.object_data_pos = -1
        self.render_data_pos = -1
        self.world_info_string = ''
        self.lightmap_grid_size = 20
        self.boundary_min = Vector()
        self.boundary_max = Vector()
        self.quad_tree = None
        self.world_models: list['WorldModel'] = []
        self.world_objects: list['WorldObject'] = []


class QuadTree:
    box_min: Vector
    box_max: Vector
    node_count: int
    dummy_terrain_depth: int
    tree_data: list[Any]

    def __init__(self):
        self.box_min = Vector()
        self.box_max = Vector()
        self.node_count = 0
        self.dummy_terrain_depth = 0
        self.tree_data = []


class Vertex:
    count: int
    extra: int

    def __init__(self):
        self.count = 0
        self.extra = 0


class LeafData:
    portal_id: int
    contents: list[Any]

    def __init__(self):
        self.portal_id = 0
        self.contents = []


class Leaf:
    leaf_data: list[Any]
    polygons: list[Any]

    def __init__(self):
        self.leaf_data = []
        self.polygons = []


class Plane:
    normal: Vector
    distance: int

    def __init__(self):
        self.normal = Vector()
        self.distance = 0


class Surface:
    uv_list: list[Vector]
    texture_index: int
    plane_index: int  # I think...
    flags: int
    use_effects: bool
    effect: str
    effect_param: str
    texture_flags: int

    def __init__(self):
        self.uv_list = [Vector(), Vector(), Vector()]
        self.texture_index = 0
        self.plane_index = 0
        self.flags = 0
        self.use_effects = False
        self.effect = ''
        self.effect_param = ''
        self.texture_flags = 0

    @property
    def is_solid(self):
        """Surface is solid"""
        return self.flags & (1 << 0)

    @property
    def is_non_existent(self):
        """Gets removed by preprocessor"""
        return self.flags & (1 << 1)

    @property
    def is_invisible(self):
        """Don't draw"""
        return self.flags & (1 << 2)

    @property
    def is_sky(self):
        """Sky portal"""
        return self.flags & (1 << 4)

    @property
    def is_bright(self):
        """Full bright"""
        return self.flags & (1 << 5)

    @property
    def is_flat_shaded(self):
        """Flat shaded"""
        return self.flags & (1 << 6)

    @property
    def is_lightmap(self):
        """Has a lightmap"""
        return self.flags & (1 << 7)

    @property
    def is_no_sub_div(self):
        """Don't subdivide this surface"""
        return self.flags & (1 << 8)

    @property
    def is_hull_maker(self):
        """Adds hulls for PVS"""
        return self.flags & (1 << 9)

    @property
    def is_directional_light(self):
        """Only lit by GlobalDirLight"""
        return self.flags & (1 << 11)

    @property
    def is_gouraud_shaded(self):
        """Gouraud shade this surface"""
        return self.flags & (1 << 12)

    @property
    def is_portal(self):
        """This surface is a portal that can be opened/closed"""
        return self.flags & (1 << 13)

    @property
    def is_panning_sky(self):
        """This surface has a panning sky on it"""
        return self.flags & (1 << 15)

    @property
    def is_physics_blocker(self):
        """Blocks player"""
        return self.flags & (1 << 17)

    @property
    def is_terrain_occluder(self):
        """Used for visibility calculations on terrain"""
        return self.flags & (1 << 18)

    @property
    def is_additive(self):
        """Add source and destination colours"""
        return self.flags & (1 << 19)

    @property
    def is_vis_blocker(self):
        """Blocks off the visibility tree"""
        return self.flags & (1 << 21)

    @property
    def is_not_a_step(self):
        """No steppy on this surface"""
        return self.flags & (1 << 22)

    @property
    def is_mirror(self):
        """A mirror, plane/portal based reflections"""
        return self.flags & (1 << 23)

class DiskVert:
    vert_idx: int
    vert_colour: list[int]

    def __init__(self):
        self.vert_idx = -1
        self.vert_colour = []

class Poly:
    center: Vector
    lightmap_width: int
    lightmap_height: int
    surface_index: int
    plane_index: int
    disk_vertices: list[DiskVert]

    def __init__(self):
        self.center = Vector()
        self.lightmap_width = 0
        self.lightmap_height = 0
        self.surface_index = 0
        self.plane_index = 0
        self.disk_vertices = []


class Point:
    data: Vector
    normals: Vector

    def __init__(self):
        self.data = Vector()
        self.normals = Vector()


class Node:
    poly_index: int
    leaf_index: int
    node_indices: list

    def __init__(self):
        self.poly_index = 0
        self.leaf_index = 0
        self.node_indices = []


class UserPortal:
    name: str
    center: Vector
    dims: Vector

    def __init__(self):
        self.name = ''
        self.center = Vector()
        self.dims = Vector()


class WorldModel:
    index: int
    name: str
    root_node_index: int
    sections: int

    info_flags: int
    point_count: int
    plane_count: int
    surface_count: int
    user_portal_count: int
    poly_count: int
    leaf_count: int
    vertex_count: int
    total_vis_list_size: int
    leaf_list_count: int
    node_count: int
    min_box: Vector
    max_box: Vector
    world_offset: Vector
    texture_list: list[str]

    vertices: list[Vertex]
    leafs: list[Leaf]
    planes: list[Plane]
    surfaces: list[Surface]
    polies: list[Poly]
    nodes: list[Node]
    user_portals: list[UserPortal]
    points: list[Point]
    block_table: list

    def __init__(self):
        self.index = 0
        self.name = ''
        self.root_node_index = -1
        self.sections = 0

        self.info_flags = 0
        self.point_count = 0
        self.plane_count = 0
        self.surface_count = 0
        self.user_portal_count = 0
        self.poly_count = 0
        self.leaf_count = 0
        self.vertex_count = 0
        self.total_vis_list_size = 0
        self.leaf_list_count = 0
        self.node_count = 0
        self.min_box = Vector()
        self.max_box = Vector()
        self.world_offset = Vector()
        self.texture_list: list[str] = []

        self.vertices: list[Vertex] = []
        self.leafs: list[Leaf] = []
        self.planes: list[Plane] = []
        self.surfaces: list[Surface] = []
        self.polies: list[Poly] = []
        self.nodes: list[Node] = []
        self.user_portals: list[UserPortal] = []
        self.points: list[Point] = []
        self.block_table = []  # Physics?

    @property
    def is_movable(self):
        return self.info_flags & (1 << 1)

    @property
    def is_main_world(self):
        return self.info_flags & (1 << 2)

    @property
    def is_physics_bsp(self):
        return self.info_flags & (1 << 4)

    @property
    def is_vis_bsp(self):
        return self.info_flags & (1 << 5)


class WorldProperty:
    name: str
    property_type: int
    flags: int

    def __init__(self):
        self.name = ''
        self.property_type = 0
        self.flags = 0


class WorldPropertyString(WorldProperty):
    value: str

    def __init__(self):
        super().__init__()
        self.value = ''

    def read_value(self, f: BinaryIO):
        # TODO: Move _read_string to a common area and use that
        self.value = f.read(unpack('H', f)[0]).decode('ascii')


class WorldPropertyVector(WorldProperty):
    value: Vector

    def __init__(self):
        super().__init__()
        self.value = Vector()

    def read_value(self, f: BinaryIO):
        # TODO: Move _read_vector to a common area and use that
        self.value = Vector(unpack('3f', f))


class WorldPropertyFloat(WorldProperty):
    value: float

    def __init__(self):
        super().__init__()
        self.value = 0.0

    def read_value(self, f: BinaryIO):
        self.value = unpack('f', f)[0]


class WorldPropertyBool(WorldProperty):
    value: bool

    def __init__(self):
        super().__init__()
        self.value = False

    def read_value(self, f: BinaryIO):
        self.value = unpack('B', f)[0] == 1


class WorldPropertyInt(WorldProperty):
    value: int

    def __init__(self):
        super().__init__()
        self.value = 0

    def read_value(self, f: BinaryIO):
        self.value = unpack('I', f)[0]


class WorldPropertyRotation(WorldProperty):
    value: Quaternion

    def __init__(self):
        super().__init__()
        self.value = Quaternion()

    def read_value(self, f: BinaryIO):
        # TODO: Move _read_quaternion to a common area and use that
        x, y, z, w = unpack('4f', f)
        self.value = Quaternion((w, x, y, z))


class WorldObject:
    type: str
    property_count: int
    properties: list[WorldProperty]

    # Some helpful attributes
    name: Optional[str]
    pos: Optional[Vector()]
    rotation: Optional[Quaternion()]

    name_prop_idx: int
    pos_prop_idx: int
    rotation_prop_idx: int

    def __init__(self):
        self.type = ''
        self.properties_count = 0
        self.properties = []

        self.name = None
        self.pos = None
        self.rotation = None

        self.name_prop_idx = -1
        self.pos_prop_idx = -1
        self.rotation_prop_idx = -1
